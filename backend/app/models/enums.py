"""
Enumerations for database models
"""
from enum import Enum


class SafetyLevel(str, Enum):
    """
    Safety classification levels for ingredients during pregnancy
    """
    SAFE = "safe"
    CAUTION = "caution"
    AVOID = "avoid"
    UNKNOWN = "unknown"


class IngredientCategory(str, Enum):
    """
    Categories for ingredient classification
    """
    PRESERVATIVE = "preservative"
    FRAGRANCE = "fragrance"
    EMOLLIENT = "emollient"
    HUMECTANT = "humectant"
    SURFACTANT = "surfactant"
    EMULSIFIER = "emulsifier"
    ACTIVE = "active"
    COLORANT = "colorant"
    SOLVENT = "solvent"
    THICKENER = "thickener"
    pH_ADJUSTER = "ph_adjuster"
    ANTIOXIDANT = "antioxidant"
    OTHER = "other"


class TrimesterRisk(str, Enum):
    """
    Risk levels by trimester
    """
    FIRST = "first"
    SECOND = "second"
    THIRD = "third"
    ALL = "all"
    NONE = "none"
