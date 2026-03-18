"""
QA Agent
Validates classification accuracy and database integrity
"""
import json
from typing import Dict, List
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


class QAAgent(BaseAgent):
    """
    QA Agent - Quality assurance for the safety database

    Responsibilities:
    1. Validate high-risk classifications (avoid/caution) are correct
    2. Check for duplicates in the database
    3. Verify AI-classified ingredients against known sources
    4. Flag inconsistencies
    """

    # Known ground truth — ingredients that MUST be classified correctly
    GROUND_TRUTH = {
        "retinol": SafetyLevel.AVOID,
        "tretinoin": SafetyLevel.AVOID,
        "isotretinoin": SafetyLevel.AVOID,
        "hydroquinone": SafetyLevel.AVOID,
        "formaldehyde": SafetyLevel.AVOID,
        "oxybenzone": SafetyLevel.CAUTION,
        "salicylic acid": SafetyLevel.CAUTION,
        "benzoyl peroxide": SafetyLevel.CAUTION,
        "water": SafetyLevel.SAFE,
        "glycerin": SafetyLevel.SAFE,
        "hyaluronic acid": SafetyLevel.SAFE,
        "niacinamide": SafetyLevel.SAFE,
        "zinc oxide": SafetyLevel.SAFE,
        "titanium dioxide": SafetyLevel.SAFE,
        "shea butter": SafetyLevel.SAFE,
        "vitamin e": SafetyLevel.SAFE,
        "vitamin c": SafetyLevel.SAFE,
    }

    def execute(self, check: str = "all") -> Dict:
        """
        Run QA checks.

        Args:
            check: "all", "ground_truth", "duplicates", "consistency"

        Returns:
            Dict with check results and issues found
        """
        self.log_info(f"Running QA check: {check}")
        results = {}

        if check in ("all", "ground_truth"):
            results["ground_truth"] = self._check_ground_truth()

        if check in ("all", "duplicates"):
            results["duplicates"] = self._check_duplicates()

        if check in ("all", "consistency"):
            results["consistency"] = self._check_consistency()

        if check in ("all", "stats"):
            results["stats"] = self._get_db_stats()

        # Overall summary
        total_issues = sum(
            len(r.get("issues", [])) for r in results.values() if isinstance(r, dict)
        )
        results["summary"] = {
            "total_issues": total_issues,
            "status": "pass" if total_issues == 0 else "issues_found",
        }

        return results

    def _check_ground_truth(self) -> Dict:
        """Verify known ingredients are classified correctly."""
        issues = []
        checked = 0

        for name, expected_level in self.GROUND_TRUTH.items():
            ingredient = self.db.query(Ingredient).filter(
                Ingredient.name_normalized == name
            ).first()

            if not ingredient:
                issues.append({
                    "ingredient": name,
                    "issue": "missing",
                    "expected": expected_level.value,
                    "actual": None,
                })
            elif ingredient.safety_level != expected_level.value:
                issues.append({
                    "ingredient": name,
                    "issue": "wrong_classification",
                    "expected": expected_level.value,
                    "actual": ingredient.safety_level,
                })
            checked += 1

        return {
            "checked": checked,
            "issues": issues,
            "pass": len(issues) == 0,
        }

    def _check_duplicates(self) -> Dict:
        """Find duplicate or near-duplicate ingredients."""
        issues = []

        # Exact normalized name duplicates (shouldn't happen with unique constraint)
        dupes = (
            self.db.query(Ingredient.name_normalized, func.count(Ingredient.id))
            .group_by(Ingredient.name_normalized)
            .having(func.count(Ingredient.id) > 1)
            .all()
        )

        for name, count in dupes:
            issues.append({
                "name": name,
                "issue": "exact_duplicate",
                "count": count,
            })

        # Check if any ingredient name appears as another's alias
        aliases = self.db.query(IngredientAlias).all()
        ingredient_names = set(
            row[0] for row in self.db.query(Ingredient.name_normalized).all()
        )

        for alias in aliases:
            if alias.alias_normalized in ingredient_names:
                # This alias points to an ingredient that also exists as a standalone
                actual_ing = self.db.query(Ingredient).filter(
                    Ingredient.name_normalized == alias.alias_normalized
                ).first()
                if actual_ing and actual_ing.id != alias.ingredient_id:
                    issues.append({
                        "alias": alias.alias,
                        "issue": "alias_is_also_ingredient",
                        "alias_ingredient_id": alias.ingredient_id,
                        "standalone_ingredient_id": actual_ing.id,
                    })

        return {
            "issues": issues,
            "pass": len(issues) == 0,
        }

    def _check_consistency(self) -> Dict:
        """Check for data consistency issues."""
        issues = []

        # Ingredients with avoid/caution but no explanation
        no_explanation = self.db.query(Ingredient).filter(
            Ingredient.safety_level.in_(["avoid", "caution"]),
            (Ingredient.why_flagged.is_(None)) | (Ingredient.why_flagged == "")
        ).all()

        for ing in no_explanation:
            issues.append({
                "ingredient": ing.name,
                "issue": "flagged_without_explanation",
                "safety_level": ing.safety_level,
            })

        # Ingredients with avoid but no alternatives
        no_alternatives = self.db.query(Ingredient).filter(
            Ingredient.safety_level == "avoid",
            (Ingredient.safe_alternatives.is_(None)) | (Ingredient.safe_alternatives == "")
        ).all()

        for ing in no_alternatives:
            issues.append({
                "ingredient": ing.name,
                "issue": "avoid_without_alternatives",
            })

        # Very low confidence entries
        low_confidence = self.db.query(Ingredient).filter(
            Ingredient.confidence_score < 0.5,
            Ingredient.safety_level != "unknown",
        ).all()

        for ing in low_confidence:
            issues.append({
                "ingredient": ing.name,
                "issue": "low_confidence_classification",
                "confidence": ing.confidence_score,
                "safety_level": ing.safety_level,
            })

        return {
            "issues": issues,
            "pass": len(issues) == 0,
        }

    def _get_db_stats(self) -> Dict:
        """Get database statistics."""
        total = self.db.query(func.count(Ingredient.id)).scalar()

        by_level = {}
        for level in SafetyLevel:
            count = self.db.query(func.count(Ingredient.id)).filter(
                Ingredient.safety_level == level.value
            ).scalar()
            by_level[level.value] = count

        alias_count = self.db.query(func.count(IngredientAlias.id)).scalar()
        ai_classified = self.db.query(func.count(Ingredient.id)).filter(
            Ingredient.source.like("ai_%") | Ingredient.source.like("research_%")
        ).scalar()

        return {
            "total_ingredients": total,
            "by_safety_level": by_level,
            "total_aliases": alias_count,
            "ai_classified": ai_classified,
            "human_verified": total - (ai_classified or 0),
        }
