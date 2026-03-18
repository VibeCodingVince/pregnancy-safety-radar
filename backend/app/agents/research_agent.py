"""
Research Agent
Auto-expands the ingredient database by researching unknown ingredients
Uses OpenAI to generate comprehensive safety data
"""
import json
import re
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.agents.base import BaseAgent
from app.models.ingredient import Ingredient, IngredientAlias
from app.models.enums import SafetyLevel
from app.core.config import settings

try:
    import openai
except ImportError:
    openai = None


class ResearchAgent(BaseAgent):
    """
    Research Agent - Expands ingredient database

    Responsibilities:
    1. Identify gaps in the database (unknown/low-confidence ingredients)
    2. Research ingredients in batch via AI
    3. Add comprehensive safety data including aliases, categories, alternatives
    4. Improve existing entries with better data
    """

    def execute(self, mode: str = "fill_gaps", limit: int = 50) -> Dict:
        """
        Run research cycle.

        Args:
            mode: "fill_gaps" (improve unknowns) or "expand" (add common ingredients)
            limit: Max ingredients to research per cycle

        Returns:
            Dict with stats: researched, added, updated, errors
        """
        self.log_info(f"Starting research cycle: mode={mode}, limit={limit}")

        if not settings.OPENAI_API_KEY or not openai:
            return {"error": "OpenAI API key not configured", "researched": 0}

        if mode == "fill_gaps":
            return self._fill_gaps(limit)
        elif mode == "expand":
            return self._expand_database(limit)
        else:
            return {"error": f"Unknown mode: {mode}", "researched": 0}

    def _fill_gaps(self, limit: int) -> Dict:
        """Research ingredients with low confidence or unknown status."""
        # Find ingredients needing improvement
        targets = self.db.query(Ingredient).filter(
            (Ingredient.safety_level == SafetyLevel.UNKNOWN) |
            (Ingredient.confidence_score < 0.7) |
            (Ingredient.why_flagged.is_(None))
        ).limit(limit).all()

        if not targets:
            self.log_info("No gaps to fill — database is in good shape")
            return {"researched": 0, "added": 0, "updated": 0, "errors": 0}

        names = [t.name for t in targets]
        self.log_info(f"Researching {len(names)} ingredients with gaps")

        results = self._research_batch(names)
        stats = self._apply_results(results, update_existing=True)
        return stats

    def _expand_database(self, limit: int) -> Dict:
        """Add common pregnancy-relevant ingredients not yet in DB."""
        # Get existing names
        existing = set(
            row[0] for row in
            self.db.query(Ingredient.name_normalized).all()
        )

        # Common ingredients to ensure we have
        common_ingredients = self._get_common_ingredient_list()

        # Filter to ones we don't have
        missing = [name for name in common_ingredients if name.lower() not in existing]

        if not missing:
            self.log_info("All common ingredients already in database")
            return {"researched": 0, "added": 0, "updated": 0, "errors": 0}

        batch = missing[:limit]
        self.log_info(f"Researching {len(batch)} new common ingredients")

        results = self._research_batch(batch)
        stats = self._apply_results(results, update_existing=False)
        return stats

    def _research_batch(self, names: List[str]) -> List[Dict]:
        """Research a batch of ingredients via OpenAI."""
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

        # Process in chunks of 20 to stay within token limits
        all_results = []
        for i in range(0, len(names), 20):
            chunk = names[i:i + 20]
            chunk_results = self._research_chunk(client, chunk)
            all_results.extend(chunk_results)

        return all_results

    def _research_chunk(self, client, names: List[str]) -> List[Dict]:
        """Research a single chunk of ingredients."""
        prompt = f"""You are a pharmacology and toxicology expert specializing in pregnancy safety.

For each ingredient, provide comprehensive safety data. Be thorough and evidence-based.

For EACH ingredient, return:
- "name": exact name as given
- "safety_level": "safe", "caution", "avoid", or "unknown"
- "category": one of: preservative, fragrance, emollient, humectant, surfactant, emulsifier, active, colorant, solvent, thickener, ph_adjuster, antioxidant, other
- "description": brief description of what the ingredient is and what it does (1-2 sentences)
- "why_flagged": detailed explanation of pregnancy concerns (2-3 sentences, null if safe)
- "safe_alternatives": comma-separated alternatives if avoid/caution (null if safe)
- "aliases": array of alternative names (INCI names, common names, chemical names)
- "confidence": 0.0-1.0 your confidence

Safety guidelines:
- AVOID: Known teratogens, high-dose retinoids, certain essential oils, formaldehyde releasers
- CAUTION: Limited data, dose-dependent risk, some preservatives, certain fragrances
- SAFE: Well-established safety profile, commonly used in pregnancy-safe products
- Be conservative — if uncertain, classify as "caution"

Ingredients to research:
{json.dumps(names)}

Return ONLY a valid JSON array."""

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=4000,
            )

            content = response.choices[0].message.content.strip()
            content = re.sub(r'^```json\s*', '', content)
            content = re.sub(r'\s*```$', '', content)

            return json.loads(content)

        except Exception as e:
            self.log_error(f"Research API call failed: {e}")
            return []

    def _apply_results(self, results: List[Dict], update_existing: bool) -> Dict:
        """Apply research results to the database."""
        stats = {"researched": len(results), "added": 0, "updated": 0, "errors": 0}

        for item in results:
            try:
                name = item.get("name", "").strip()
                if not name:
                    continue

                normalized = name.lower().strip()
                existing = self.db.query(Ingredient).filter(
                    Ingredient.name_normalized == normalized
                ).first()

                if existing and update_existing:
                    # Update existing entry
                    if item.get("safety_level"):
                        existing.safety_level = item["safety_level"]
                    if item.get("category"):
                        existing.category = item["category"]
                    if item.get("description"):
                        existing.description = item["description"]
                    if item.get("why_flagged"):
                        existing.why_flagged = item["why_flagged"]
                    if item.get("safe_alternatives"):
                        existing.safe_alternatives = item["safe_alternatives"]
                    existing.confidence_score = min(item.get("confidence", 0.8), 0.9)
                    existing.source = "research_agent_gpt4o_mini"

                    # Add new aliases
                    self._add_aliases(existing.id, item.get("aliases", []))
                    stats["updated"] += 1

                elif not existing:
                    # Create new entry
                    new_ing = Ingredient(
                        name=name,
                        name_normalized=normalized,
                        safety_level=item.get("safety_level", "unknown"),
                        category=item.get("category", "other"),
                        description=item.get("description"),
                        why_flagged=item.get("why_flagged"),
                        safe_alternatives=item.get("safe_alternatives"),
                        source="research_agent_gpt4o_mini",
                        confidence_score=min(item.get("confidence", 0.8), 0.9),
                    )
                    self.db.add(new_ing)
                    self.db.flush()

                    # Add aliases
                    self._add_aliases(new_ing.id, item.get("aliases", []))
                    stats["added"] += 1

            except Exception as e:
                self.log_error(f"Failed to apply result for {item.get('name')}: {e}")
                stats["errors"] += 1

        try:
            self.db.commit()
            self.log_info(f"Research results applied: {stats}")
        except Exception as e:
            self.db.rollback()
            self.log_error(f"Failed to commit research results: {e}")
            stats["errors"] = stats["researched"]

        return stats

    def _add_aliases(self, ingredient_id: int, aliases: List[str]):
        """Add aliases for an ingredient, skipping duplicates."""
        existing_aliases = set(
            row[0] for row in
            self.db.query(IngredientAlias.alias_normalized).filter(
                IngredientAlias.ingredient_id == ingredient_id
            ).all()
        )

        for alias in aliases:
            normalized = alias.lower().strip()
            if normalized and normalized not in existing_aliases:
                self.db.add(IngredientAlias(
                    ingredient_id=ingredient_id,
                    alias=alias,
                    alias_normalized=normalized,
                ))
                existing_aliases.add(normalized)

    def _get_common_ingredient_list(self) -> List[str]:
        """Return a list of common cosmetic/skincare ingredients to ensure we cover."""
        return [
            # Retinoids (AVOID)
            "Tretinoin", "Isotretinoin", "Adapalene", "Tazarotene", "Retinaldehyde",
            "Retinyl Palmitate", "Retinol",

            # Chemical sunscreens (CAUTION/AVOID)
            "Oxybenzone", "Octinoxate", "Homosalate", "Avobenzone", "Octocrylene",
            "Octisalate",

            # Safe sunscreens
            "Zinc Oxide", "Titanium Dioxide",

            # Preservatives
            "Methylparaben", "Propylparaben", "Butylparaben", "Ethylparaben",
            "Phenoxyethanol", "Benzalkonium Chloride", "Formaldehyde",
            "DMDM Hydantoin", "Imidazolidinyl Urea", "Diazolidinyl Urea",
            "Quaternium-15", "Bronopol",

            # Common safe ingredients
            "Water", "Glycerin", "Hyaluronic Acid", "Niacinamide", "Ceramides",
            "Squalane", "Shea Butter", "Aloe Vera", "Jojoba Oil", "Vitamin E",
            "Vitamin C", "Ascorbic Acid", "Panthenol", "Allantoin",
            "Centella Asiatica", "Green Tea Extract", "Chamomile Extract",

            # Acids
            "Salicylic Acid", "Glycolic Acid", "Lactic Acid", "Azelaic Acid",
            "Mandelic Acid", "Benzoyl Peroxide", "Kojic Acid",

            # Essential oils (mixed safety)
            "Tea Tree Oil", "Lavender Oil", "Rosemary Oil", "Peppermint Oil",
            "Eucalyptus Oil", "Clary Sage Oil",

            # Common actives
            "Hydroquinone", "Arbutin", "Tranexamic Acid", "Bakuchiol",
            "Peptides", "Collagen", "Caffeine", "Snail Mucin",

            # Surfactants
            "Sodium Lauryl Sulfate", "Sodium Laureth Sulfate",
            "Cocamidopropyl Betaine", "Decyl Glucoside",

            # Emollients/Oils
            "Dimethicone", "Cyclomethicone", "Mineral Oil", "Petrolatum",
            "Coconut Oil", "Argan Oil", "Rosehip Oil",

            # Fragrance/Color
            "Fragrance", "Parfum", "Limonene", "Linalool", "Citral",

            # Hair care
            "Minoxidil", "Ketoconazole",

            # Misc
            "Aluminum Chlorohydrate", "Triclosan", "BHA", "BHT",
        ]
