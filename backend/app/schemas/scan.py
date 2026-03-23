"""
Pydantic schemas for Scan endpoint
"""
from typing import Optional, List
from pydantic import BaseModel, Field
from app.models.enums import SafetyLevel


class ScanRequest(BaseModel):
    """
    Request schema for scanning products
    Supports both barcode lookup and direct ingredient text parsing
    """
    barcode: Optional[str] = Field(None, max_length=50, description="Product barcode (UPC/EAN)")
    ingredient_text: Optional[str] = Field(None, description="Comma-separated ingredient list")
    image_base64: Optional[str] = Field(None, description="Base64-encoded image for OCR (future)")

    class Config:
        json_schema_extra = {
            "example": {
                "ingredient_text": "Water, Glycerin, Retinol, Niacinamide, Hyaluronic Acid"
            }
        }


class FlaggedIngredient(BaseModel):
    """
    Individual ingredient that was flagged in a scan
    """
    name: str
    safety_level: SafetyLevel
    category: Optional[str] = None
    description: Optional[str] = None
    why_flagged: Optional[str] = None
    safe_alternatives: Optional[str] = None
    confidence: Optional[float] = Field(default=1.0, ge=0.0, le=1.0)

    class Config:
        from_attributes = True


class ScanResponse(BaseModel):
    """
    Response schema for scan results
    Traffic-light verdict with detailed ingredient analysis
    """
    overall_safety: SafetyLevel
    verdict_message: str
    flagged_ingredients: List[FlaggedIngredient] = Field(default_factory=list)
    total_ingredients_analyzed: int
    safe_ingredients: List[FlaggedIngredient] = Field(default_factory=list)
    product_name: Optional[str] = None
    product_brand: Optional[str] = None
    product_image_url: Optional[str] = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    classification_version: str = "v1.0"

    class Config:
        json_schema_extra = {
            "example": {
                "overall_safety": "avoid",
                "verdict_message": "⚠️ Contains 1 ingredient to AVOID during pregnancy",
                "flagged_ingredients": [
                    {
                        "name": "Retinol",
                        "safety_level": "avoid",
                        "why_flagged": "Vitamin A derivatives can cause birth defects",
                        "safe_alternatives": "Bakuchiol, Niacinamide",
                        "confidence": 1.0
                    }
                ],
                "total_ingredients_analyzed": 5,
                "confidence": 1.0,
                "classification_version": "v1.0"
            }
        }
