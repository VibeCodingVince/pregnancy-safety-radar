"""
Product database models
"""
from sqlalchemy import Column, Integer, String, Text, Table, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


# Association table for many-to-many relationship with position tracking
product_ingredients = Table(
    'product_ingredients',
    Base.metadata,
    Column('id', Integer, primary_key=True),
    Column('product_id', Integer, ForeignKey('products.id'), nullable=False),
    Column('ingredient_id', Integer, ForeignKey('ingredients.id'), nullable=False),
    Column('position', Integer, nullable=False),  # Order in ingredient list
    Column('percentage', String(50), nullable=True)  # e.g., "1-5%", if available
)


class Product(Base):
    """
    Product model - beauty/skincare products with ingredient lists
    """
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    brand = Column(String(255), nullable=True, index=True)
    barcode = Column(String(50), unique=True, nullable=True, index=True)  # UPC/EAN

    # Product details
    description = Column(Text, nullable=True)
    product_type = Column(String(100), nullable=True)  # moisturizer, serum, etc.
    image_url = Column(String(512), nullable=True)

    # Data source
    data_source = Column(String(100), nullable=True)  # user_submitted, api, manual
    verified = Column(Integer, default=0)  # Boolean: 0=unverified, 1=verified

    # Relationships
    ingredients = relationship(
        "Ingredient",
        secondary=product_ingredients,
        backref="products"
    )

    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', brand='{self.brand}')>"
