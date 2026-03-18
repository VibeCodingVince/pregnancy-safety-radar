"""
Pydantic schemas for Ingredient endpoints
"""
from typing import Optional, List
from pydantic import BaseModel, Field
from app.models.enums import SafetyLevel, IngredientCategory


class IngredientBase(BaseModel):
    """Base ingredient schema"""
    name: str = Field(..., min_length=1, max_length=255)
    safety_level: SafetyLevel
    category: Optional[IngredientCategory] = None
    description: Optional[str] = None
    why_flagged: Optional[str] = None
    safe_alternatives: Optional[str] = None
    source: Optional[str] = None
    confidence_score: Optional[float] = Field(default=1.0, ge=0.0, le=1.0)


class IngredientCreate(IngredientBase):
    """Schema for creating a new ingredient"""
    aliases: Optional[List[str]] = Field(default_factory=list)


class IngredientResponse(IngredientBase):
    """Schema for ingredient response"""
    id: int
    name_normalized: str
    aliases: List[str] = Field(default_factory=list)

    class Config:
        from_attributes = True


class IngredientSearchResponse(BaseModel):
    """Schema for ingredient search results"""
    total: int
    results: List[IngredientResponse]

    class Config:
        from_attributes = True
