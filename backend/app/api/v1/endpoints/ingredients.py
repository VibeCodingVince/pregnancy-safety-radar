"""
Ingredient endpoints
CRUD operations for ingredients
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.ingredient import Ingredient, IngredientAlias
from app.schemas.ingredient import IngredientCreate, IngredientResponse, IngredientSearchResponse

router = APIRouter()


def normalize_name(name: str) -> str:
    """Normalize ingredient name for matching"""
    return name.lower().strip()


@router.get("/", response_model=List[IngredientResponse])
async def list_ingredients(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    safety_level: str = Query(None),
    db: Session = Depends(get_db)
):
    """
    List all ingredients with pagination
    """
    query = db.query(Ingredient)

    if safety_level:
        query = query.filter(Ingredient.safety_level == safety_level)

    ingredients = query.offset(skip).limit(limit).all()

    # Convert to response format with aliases
    result = []
    for ing in ingredients:
        ing_dict = {
            "id": ing.id,
            "name": ing.name,
            "name_normalized": ing.name_normalized,
            "safety_level": ing.safety_level,
            "category": ing.category,
            "description": ing.description,
            "why_flagged": ing.why_flagged,
            "safe_alternatives": ing.safe_alternatives,
            "source": ing.source,
            "confidence_score": ing.confidence_score,
            "aliases": [alias.alias for alias in ing.aliases]
        }
        result.append(IngredientResponse(**ing_dict))

    return result


@router.get("/{ingredient_id}", response_model=IngredientResponse)
async def get_ingredient(
    ingredient_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific ingredient by ID
    """
    ingredient = db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()

    if not ingredient:
        raise HTTPException(status_code=404, detail="Ingredient not found")

    return IngredientResponse(
        id=ingredient.id,
        name=ingredient.name,
        name_normalized=ingredient.name_normalized,
        safety_level=ingredient.safety_level,
        category=ingredient.category,
        description=ingredient.description,
        why_flagged=ingredient.why_flagged,
        safe_alternatives=ingredient.safe_alternatives,
        source=ingredient.source,
        confidence_score=ingredient.confidence_score,
        aliases=[alias.alias for alias in ingredient.aliases]
    )


@router.get("/search/", response_model=IngredientSearchResponse)
async def search_ingredients(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Search ingredients by name or alias
    """
    search_term = f"%{q.lower()}%"

    # Search in ingredient names
    name_matches = db.query(Ingredient).filter(
        Ingredient.name_normalized.like(search_term)
    ).limit(limit).all()

    # Search in aliases
    alias_matches = db.query(Ingredient).join(IngredientAlias).filter(
        IngredientAlias.alias_normalized.like(search_term)
    ).limit(limit).all()

    # Combine and deduplicate
    all_matches = {ing.id: ing for ing in name_matches}
    for ing in alias_matches:
        if ing.id not in all_matches:
            all_matches[ing.id] = ing

    results = []
    for ing in all_matches.values():
        results.append(IngredientResponse(
            id=ing.id,
            name=ing.name,
            name_normalized=ing.name_normalized,
            safety_level=ing.safety_level,
            category=ing.category,
            description=ing.description,
            why_flagged=ing.why_flagged,
            safe_alternatives=ing.safe_alternatives,
            source=ing.source,
            confidence_score=ing.confidence_score,
            aliases=[alias.alias for alias in ing.aliases]
        ))

    return IngredientSearchResponse(
        total=len(results),
        results=results[:limit]
    )


@router.post("/", response_model=IngredientResponse, status_code=201)
async def create_ingredient(
    ingredient: IngredientCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new ingredient
    """
    # Check if ingredient already exists
    name_normalized = normalize_name(ingredient.name)
    existing = db.query(Ingredient).filter(
        Ingredient.name_normalized == name_normalized
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Ingredient already exists")

    # Create ingredient
    db_ingredient = Ingredient(
        name=ingredient.name,
        name_normalized=name_normalized,
        safety_level=ingredient.safety_level,
        category=ingredient.category,
        description=ingredient.description,
        why_flagged=ingredient.why_flagged,
        safe_alternatives=ingredient.safe_alternatives,
        source=ingredient.source,
        confidence_score=ingredient.confidence_score
    )

    db.add(db_ingredient)
    db.flush()  # Get the ID

    # Add aliases
    for alias_name in ingredient.aliases or []:
        alias = IngredientAlias(
            ingredient_id=db_ingredient.id,
            alias=alias_name,
            alias_normalized=normalize_name(alias_name)
        )
        db.add(alias)

    db.commit()
    db.refresh(db_ingredient)

    return IngredientResponse(
        id=db_ingredient.id,
        name=db_ingredient.name,
        name_normalized=db_ingredient.name_normalized,
        safety_level=db_ingredient.safety_level,
        category=db_ingredient.category,
        description=db_ingredient.description,
        why_flagged=db_ingredient.why_flagged,
        safe_alternatives=db_ingredient.safe_alternatives,
        source=db_ingredient.source,
        confidence_score=db_ingredient.confidence_score,
        aliases=[alias.alias for alias in db_ingredient.aliases]
    )
