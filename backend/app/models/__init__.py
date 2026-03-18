"""
Database models package
Exports all models for SQLAlchemy to discover
"""
from app.models.enums import SafetyLevel, IngredientCategory, TrimesterRisk
from app.models.ingredient import Ingredient, IngredientAlias
from app.models.product import Product, product_ingredients
from app.models.safety_classification import SafetyClassification

__all__ = [
    # Enums
    "SafetyLevel",
    "IngredientCategory",
    "TrimesterRisk",
    # Models
    "Ingredient",
    "IngredientAlias",
    "Product",
    "product_ingredients",
    "SafetyClassification",
]
