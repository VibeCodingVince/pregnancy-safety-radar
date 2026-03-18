"""
Ingredient database models
"""
from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.enums import SafetyLevel, IngredientCategory


class Ingredient(Base):
    """
    Core ingredient model with safety information
    """
    __tablename__ = "ingredients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    name_normalized = Column(String(255), unique=True, nullable=False, index=True)

    # Safety classification
    safety_level = Column(String(20), nullable=False, default=SafetyLevel.UNKNOWN)
    category = Column(String(50), nullable=True)

    # Descriptions
    description = Column(Text, nullable=True)
    why_flagged = Column(Text, nullable=True)  # Explanation for caution/avoid
    safe_alternatives = Column(Text, nullable=True)  # Suggested alternatives

    # Metadata
    source = Column(String(255), nullable=True)  # Data source reference
    confidence_score = Column(Float, nullable=True, default=1.0)  # 0.0-1.0

    # Relationships
    aliases = relationship("IngredientAlias", back_populates="ingredient", cascade="all, delete-orphan")
    classifications = relationship("SafetyClassification", back_populates="ingredient")

    def __repr__(self):
        return f"<Ingredient(id={self.id}, name='{self.name}', safety={self.safety_level})>"


class IngredientAlias(Base):
    """
    Alternative names for ingredients (INCI variants, common names)
    Enables fuzzy matching for ingredient list parsing
    """
    __tablename__ = "ingredient_aliases"

    id = Column(Integer, primary_key=True, index=True)
    ingredient_id = Column(Integer, ForeignKey("ingredients.id"), nullable=False)
    alias = Column(String(255), nullable=False)
    alias_normalized = Column(String(255), nullable=False, index=True)

    # Relationship
    ingredient = relationship("Ingredient", back_populates="aliases")

    # Indexes for fast lookups
    __table_args__ = (
        Index('idx_alias_normalized', 'alias_normalized'),
    )

    def __repr__(self):
        return f"<IngredientAlias(alias='{self.alias}', ingredient_id={self.ingredient_id})>"
