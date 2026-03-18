"""
Safety classification audit trail model
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class SafetyClassification(Base):
    """
    Audit trail for all safety classification decisions
    Tracks every scan/classification with reasoning and version
    """
    __tablename__ = "safety_classifications"

    id = Column(Integer, primary_key=True, index=True)

    # What was classified
    ingredient_id = Column(Integer, ForeignKey("ingredients.id"), nullable=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    raw_input = Column(Text, nullable=True)  # Original text/barcode scanned

    # Classification result
    safety_level = Column(String(20), nullable=False)
    confidence = Column(Float, nullable=True, default=1.0)

    # Reasoning and metadata
    reasoning = Column(Text, nullable=True)  # Why this classification was made
    flagged_ingredients = Column(Text, nullable=True)  # JSON list of problematic ingredients

    # Versioning
    classifier_version = Column(String(50), nullable=False, default="v1.0")
    model_version = Column(String(50), nullable=True)  # AI model version if applicable

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    ingredient = relationship("Ingredient", back_populates="classifications")

    def __repr__(self):
        return f"<SafetyClassification(id={self.id}, safety={self.safety_level}, version={self.classifier_version})>"
