"""
Product endpoints
CRUD operations for products
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.product import Product, product_ingredients
from app.models.ingredient import Ingredient
from app.schemas.product import ProductCreate, ProductResponse, ProductIngredientResponse

router = APIRouter()


@router.get("/", response_model=List[ProductResponse])
async def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    brand: str = Query(None),
    db: Session = Depends(get_db)
):
    """
    List all products with pagination
    """
    query = db.query(Product)

    if brand:
        query = query.filter(Product.brand.ilike(f"%{brand}%"))

    products = query.offset(skip).limit(limit).all()

    # Convert to response format
    result = []
    for prod in products:
        # Get ingredients with their positions
        ing_query = db.query(Ingredient, product_ingredients.c.position).join(
            product_ingredients,
            Ingredient.id == product_ingredients.c.ingredient_id
        ).filter(
            product_ingredients.c.product_id == prod.id
        ).order_by(product_ingredients.c.position).all()

        ingredients = [
            ProductIngredientResponse(
                id=ing.id,
                name=ing.name,
                safety_level=ing.safety_level,
                position=pos
            ) for ing, pos in ing_query
        ]

        result.append(ProductResponse(
            id=prod.id,
            name=prod.name,
            brand=prod.brand,
            barcode=prod.barcode,
            description=prod.description,
            product_type=prod.product_type,
            image_url=prod.image_url,
            verified=bool(prod.verified),
            data_source=prod.data_source,
            ingredients=ingredients
        ))

    return result


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific product by ID
    """
    product = db.query(Product).filter(Product.id == product_id).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Get ingredients with their positions
    ing_query = db.query(Ingredient, product_ingredients.c.position).join(
        product_ingredients,
        Ingredient.id == product_ingredients.c.ingredient_id
    ).filter(
        product_ingredients.c.product_id == product.id
    ).order_by(product_ingredients.c.position).all()

    ingredients = [
        ProductIngredientResponse(
            id=ing.id,
            name=ing.name,
            safety_level=ing.safety_level,
            position=pos
        ) for ing, pos in ing_query
    ]

    return ProductResponse(
        id=product.id,
        name=product.name,
        brand=product.brand,
        barcode=product.barcode,
        description=product.description,
        product_type=product.product_type,
        image_url=product.image_url,
        verified=bool(product.verified),
        data_source=product.data_source,
        ingredients=ingredients
    )


@router.get("/barcode/{barcode}", response_model=ProductResponse)
async def get_product_by_barcode(
    barcode: str,
    db: Session = Depends(get_db)
):
    """
    Get a product by barcode (UPC/EAN)
    """
    product = db.query(Product).filter(Product.barcode == barcode).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Get ingredients
    ing_query = db.query(Ingredient, product_ingredients.c.position).join(
        product_ingredients,
        Ingredient.id == product_ingredients.c.ingredient_id
    ).filter(
        product_ingredients.c.product_id == product.id
    ).order_by(product_ingredients.c.position).all()

    ingredients = [
        ProductIngredientResponse(
            id=ing.id,
            name=ing.name,
            safety_level=ing.safety_level,
            position=pos
        ) for ing, pos in ing_query
    ]

    return ProductResponse(
        id=product.id,
        name=product.name,
        brand=product.brand,
        barcode=product.barcode,
        description=product.description,
        product_type=product.product_type,
        image_url=product.image_url,
        verified=bool(product.verified),
        data_source=product.data_source,
        ingredients=ingredients
    )


@router.post("/", response_model=ProductResponse, status_code=201)
async def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new product
    """
    # Check if barcode already exists
    if product.barcode:
        existing = db.query(Product).filter(Product.barcode == product.barcode).first()
        if existing:
            raise HTTPException(status_code=400, detail="Product with this barcode already exists")

    # Create product
    db_product = Product(
        name=product.name,
        brand=product.brand,
        barcode=product.barcode,
        description=product.description,
        product_type=product.product_type,
        image_url=product.image_url,
        data_source=product.data_source
    )

    db.add(db_product)
    db.flush()

    # Add ingredients with positions
    for position, ingredient_id in enumerate(product.ingredient_ids or [], start=1):
        # Verify ingredient exists
        ingredient = db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()
        if not ingredient:
            db.rollback()
            raise HTTPException(status_code=400, detail=f"Ingredient {ingredient_id} not found")

        # Insert into association table
        stmt = product_ingredients.insert().values(
            product_id=db_product.id,
            ingredient_id=ingredient_id,
            position=position
        )
        db.execute(stmt)

    db.commit()
    db.refresh(db_product)

    # Get ingredients for response
    ing_query = db.query(Ingredient, product_ingredients.c.position).join(
        product_ingredients,
        Ingredient.id == product_ingredients.c.ingredient_id
    ).filter(
        product_ingredients.c.product_id == db_product.id
    ).order_by(product_ingredients.c.position).all()

    ingredients = [
        ProductIngredientResponse(
            id=ing.id,
            name=ing.name,
            safety_level=ing.safety_level,
            position=pos
        ) for ing, pos in ing_query
    ]

    return ProductResponse(
        id=db_product.id,
        name=db_product.name,
        brand=db_product.brand,
        barcode=db_product.barcode,
        description=db_product.description,
        product_type=db_product.product_type,
        image_url=db_product.image_url,
        verified=bool(db_product.verified),
        data_source=db_product.data_source,
        ingredients=ingredients
    )
