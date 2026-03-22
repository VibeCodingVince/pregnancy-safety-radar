"""
Safety Classifier Agent
Classifies ingredients for pregnancy safety using database + OpenAI fallback
"""
import json
import re
from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.agents.base import BaseAgent
from app.models.ingredient import Ingredient, IngredientAlias
from app.models.enums import SafetyLevel
from app.schemas.scan import ScanResponse, FlaggedIngredient
from app.core.config import settings
from app.core.cost_guard import can_make_api_call, record_api_call

# Only import openai if key is available
try:
    import openai
except ImportError:
    openai = None


class SafetyClassifierAgent(BaseAgent):
    """
    Safety Classifier Agent - Core classification engine

    Strategy:
    1. Parse ingredient text into individual ingredients
    2. Look up each in local database (fast, free)
    3. For unknowns, batch-query OpenAI GPT-4o-mini (cheap fallback)
    4. Determine overall safety verdict
    5. Return traffic-light result with explanations
    """

    SAFETY_PRIORITY = {
        SafetyLevel.AVOID: 0,
        SafetyLevel.CAUTION: 1,
        SafetyLevel.UNKNOWN: 2,
        SafetyLevel.SAFE: 3,
    }

    def execute(self, ingredient_text: str) -> ScanResponse:
        """
        Classify a comma-separated ingredient list for pregnancy safety.
        """
        self.log_info(f"Classifying ingredients: {ingredient_text[:100]}...")

        # Step 1: Parse ingredients
        ingredient_names = self._parse_ingredients(ingredient_text)
        if not ingredient_names:
            return ScanResponse(
                overall_safety=SafetyLevel.UNKNOWN,
                verdict_message="Could not parse any ingredients from the input.",
                flagged_ingredients=[],
                total_ingredients_analyzed=0,
                confidence=0.0,
            )

        self.log_info(f"Parsed {len(ingredient_names)} ingredients")

        # Step 2: Look up each ingredient in DB
        classified = []
        unknowns = []

        for name in ingredient_names:
            result = self._lookup_ingredient(name)
            if result:
                classified.append(result)
            else:
                unknowns.append(name)

        # Step 3: Use OpenAI for unknowns
        if unknowns:
            self.log_info(f"Querying AI for {len(unknowns)} unknown ingredients")
            ai_results = self._classify_with_ai(unknowns)
            classified.extend(ai_results)

        # Step 4: Determine overall verdict
        return self._build_response(classified, len(ingredient_names))

    def _parse_ingredients(self, text: str) -> List[str]:
        """
        Parse ingredient text into individual ingredient names.
        Handles comma-separated, newline-separated, and numbered lists.
        """
        # Remove common prefixes
        text = re.sub(r'^(ingredients?:?\s*)', '', text, flags=re.IGNORECASE)

        # Split on commas, semicolons, newlines, or numbered patterns
        parts = re.split(r'[,;\n]|\d+\.\s', text)

        # Clean each ingredient
        ingredients = []
        for part in parts:
            # Remove parenthetical info but keep ingredient name
            cleaned = re.sub(r'\([^)]*\)', '', part).strip()
            # Remove trailing periods, asterisks, etc.
            cleaned = re.sub(r'[.*†‡]+$', '', cleaned).strip()
            # Remove percentage info
            cleaned = re.sub(r'\d+(\.\d+)?%', '', cleaned).strip()

            if cleaned and len(cleaned) >= 2 and len(cleaned) <= 200:
                ingredients.append(cleaned)

        return ingredients

    def _normalize(self, name: str) -> str:
        """Normalize ingredient name for matching."""
        return name.lower().strip()

    def _lookup_ingredient(self, name: str) -> Optional[FlaggedIngredient]:
        """
        Look up an ingredient in the database by name or alias.
        Returns FlaggedIngredient if found, None if unknown.
        """
        normalized = self._normalize(name)

        # Try exact match on normalized name
        ingredient = self.db.query(Ingredient).filter(
            Ingredient.name_normalized == normalized
        ).first()

        # Try alias match
        if not ingredient:
            alias = self.db.query(IngredientAlias).filter(
                IngredientAlias.alias_normalized == normalized
            ).first()
            if alias:
                ingredient = alias.ingredient

        # Try partial/fuzzy match
        if not ingredient:
            ingredient = self.db.query(Ingredient).filter(
                Ingredient.name_normalized.like(f"%{normalized}%")
            ).first()

        if not ingredient:
            return None

        return FlaggedIngredient(
            name=ingredient.name,
            safety_level=SafetyLevel(ingredient.safety_level),
            category=ingredient.category,
            why_flagged=ingredient.why_flagged,
            safe_alternatives=ingredient.safe_alternatives,
            confidence=ingredient.confidence_score or 1.0,
        )

    def _classify_with_ai(self, unknowns: List[str]) -> List[FlaggedIngredient]:
        """
        Use OpenAI to classify unknown ingredients.
        Batches all unknowns into a single API call for cost efficiency.
        """
        if not settings.OPENAI_API_KEY or not openai:
            self.log_warning("No OpenAI API key — marking unknowns as unknown")
            return [
                FlaggedIngredient(
                    name=name,
                    safety_level=SafetyLevel.UNKNOWN,
                    why_flagged="Not in database and AI classification unavailable",
                    confidence=0.0,
                )
                for name in unknowns
            ]

        # Global cost circuit breaker
        if not can_make_api_call():
            self.log_warning("Daily API budget exhausted — skipping AI classify")
            return [
                FlaggedIngredient(
                    name=name,
                    safety_level=SafetyLevel.UNKNOWN,
                    why_flagged="Service at capacity — could not classify. Try again tomorrow.",
                    confidence=0.0,
                )
                for name in unknowns
            ]

        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

        prompt = f"""You are a pregnancy safety expert. Classify each ingredient for safety during pregnancy.

For EACH ingredient, respond with a JSON array. Each element must have:
- "name": the ingredient name exactly as given
- "safety_level": one of "safe", "caution", "avoid", "unknown"
- "why_flagged": brief explanation (1-2 sentences) if caution or avoid, null if safe
- "safe_alternatives": comma-separated safe alternatives if avoid/caution, null if safe
- "category": one of "preservative", "fragrance", "emollient", "humectant", "surfactant", "emulsifier", "active", "colorant", "solvent", "thickener", "ph_adjuster", "antioxidant", "other"
- "confidence": 0.0-1.0 your confidence in this classification

Be conservative — if uncertain, use "caution" rather than "safe".
Prioritize fetal safety. Consider FDA pregnancy categories where applicable.

Ingredients to classify:
{json.dumps(unknowns)}

Respond with ONLY a valid JSON array, no markdown formatting."""

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=2000,
            )

            record_api_call()
            content = response.choices[0].message.content.strip()
            # Strip markdown code fences if present
            content = re.sub(r'^```json\s*', '', content)
            content = re.sub(r'\s*```$', '', content)

            results = json.loads(content)

            classified = []
            for item in results:
                classified.append(FlaggedIngredient(
                    name=item.get("name", "Unknown"),
                    safety_level=SafetyLevel(item.get("safety_level", "unknown")),
                    category=item.get("category"),
                    why_flagged=item.get("why_flagged"),
                    safe_alternatives=item.get("safe_alternatives"),
                    confidence=min(item.get("confidence", 0.7), 0.85),  # Cap AI confidence at 0.85
                ))

            # Save AI results to DB for future lookups
            self._save_ai_results(classified)

            return classified

        except Exception as e:
            self.log_error(f"AI classification failed: {e}")
            return [
                FlaggedIngredient(
                    name=name,
                    safety_level=SafetyLevel.UNKNOWN,
                    why_flagged=f"Classification error: unable to determine safety",
                    confidence=0.0,
                )
                for name in unknowns
            ]

    def _save_ai_results(self, results: List[FlaggedIngredient]):
        """
        Save AI-classified ingredients to database for future fast lookups.
        """
        for item in results:
            if item.safety_level == SafetyLevel.UNKNOWN:
                continue

            existing = self.db.query(Ingredient).filter(
                Ingredient.name_normalized == self._normalize(item.name)
            ).first()

            if not existing:
                new_ing = Ingredient(
                    name=item.name,
                    name_normalized=self._normalize(item.name),
                    safety_level=item.safety_level.value,
                    category=item.category,
                    description=None,
                    why_flagged=item.why_flagged,
                    safe_alternatives=item.safe_alternatives,
                    source="ai_classified_gpt4o_mini",
                    confidence_score=item.confidence,
                )
                self.db.add(new_ing)

        try:
            self.db.commit()
            self.log_info(f"Saved {len(results)} AI classifications to database")
        except Exception as e:
            self.db.rollback()
            self.log_error(f"Failed to save AI results: {e}")

    def _build_response(
        self, classified: List[FlaggedIngredient], total_count: int
    ) -> ScanResponse:
        """
        Build the final scan response with overall verdict.
        """
        if not classified:
            return ScanResponse(
                overall_safety=SafetyLevel.UNKNOWN,
                verdict_message="No ingredients could be classified.",
                flagged_ingredients=[],
                total_ingredients_analyzed=total_count,
                confidence=0.0,
            )

        # Determine overall safety (worst ingredient wins)
        worst = min(classified, key=lambda x: self.SAFETY_PRIORITY.get(x.safety_level, 99))
        overall = worst.safety_level

        # Filter to only flagged (non-safe) ingredients for the response
        flagged = [i for i in classified if i.safety_level != SafetyLevel.SAFE]

        # Count by level
        avoid_count = sum(1 for i in classified if i.safety_level == SafetyLevel.AVOID)
        caution_count = sum(1 for i in classified if i.safety_level == SafetyLevel.CAUTION)
        safe_count = sum(1 for i in classified if i.safety_level == SafetyLevel.SAFE)
        unknown_count = sum(1 for i in classified if i.safety_level == SafetyLevel.UNKNOWN)

        # Build verdict message
        if overall == SafetyLevel.AVOID:
            verdict = f"🚫 AVOID — Contains {avoid_count} ingredient(s) unsafe during pregnancy"
        elif overall == SafetyLevel.CAUTION:
            verdict = f"⚠️ CAUTION — Contains {caution_count} ingredient(s) to use with care during pregnancy"
        elif overall == SafetyLevel.SAFE:
            verdict = f"✅ SAFE — All {safe_count} ingredients appear safe for pregnancy"
        else:
            verdict = f"❓ UNKNOWN — {unknown_count} ingredient(s) could not be classified"

        # Add details
        if avoid_count > 0 and caution_count > 0:
            verdict += f" (plus {caution_count} requiring caution)"

        # Average confidence
        avg_confidence = sum(i.confidence or 0.5 for i in classified) / len(classified)

        return ScanResponse(
            overall_safety=overall,
            verdict_message=verdict,
            flagged_ingredients=flagged,
            total_ingredients_analyzed=total_count,
            confidence=round(avg_confidence, 2),
        )
