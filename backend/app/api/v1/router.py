"""
API v1 Router
Aggregates all endpoint routers - FIXES THE BROKEN IMPORT
"""
from fastapi import APIRouter
from app.api.v1.endpoints import ingredients, products, scan

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(
    ingredients.router,
    prefix="/ingredients",
    tags=["ingredients"]
)

api_router.include_router(
    products.router,
    prefix="/products",
    tags=["products"]
)

api_router.include_router(
    scan.router,
    prefix="/scan",
    tags=["scan"]
)
