"""
Pydantic schemas for Product endpoints
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class ProductBase(BaseModel):
    """Base product schema"""
    name: str = Field(..., min_length=1, max_length=255)
    brand: Optional[str] = Field(None, max_length=255)
    barcode: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    product_type: Optional[str] = Field(None, max_length=100)
    image_url: Optional[str] = Field(None, max_length=512)


class ProductCreate(ProductBase):
    """Schema for creating a new product"""
    ingredient_ids: Optional[List[int]] = Field(default_factory=list)
    data_source: Optional[str] = "user_submitted"


class ProductIngredientResponse(BaseModel):
    """Simplified ingredient info for product response"""
    id: int
    name: str
    safety_level: str
    position: Optional[int] = None

    class Config:
        from_attributes = True


class ProductResponse(ProductBase):
    """Schema for product response"""
    id: int
    verified: bool
    data_source: Optional[str] = None
    ingredients: List[ProductIngredientResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True
