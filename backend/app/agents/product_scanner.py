"""
Product Scanner Agent
Looks up products by barcode using Open Food Facts API
Falls back to local database
"""
import httpx
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.models.product import Product, product_ingredients
from app.models.ingredient import Ingredient


class ProductScannerAgent(BaseAgent):
    """
    Product Scanner Agent - Barcode-based product lookup

    Strategy:
    1. Check local database first (fast, no API call)
    2. If not found, query Open Food Facts API (free, no key needed)
    3. If found remotely, cache product + ingredients locally
    4. Return ingredient text for classification
    """

    OPEN_FOOD_FACTS_URL = "https://world.openfoodfacts.org/api/v2/product/{barcode}.json"

    def execute(self, barcode: str) -> Dict[str, Any]:
        """
        Look up a product by barcode.

        Returns:
            Dict with keys: found, product_name, brand, ingredient_text, source
        """
        self.log_info(f"Scanning barcode: {barcode}")

        # Step 1: Check local DB
        result = self._lookup_local(barcode)
        if result:
            self.log_info(f"Found in local DB: {result['product_name']}")
            return result

        # Step 2: Query Open Food Facts
        result = self._lookup_open_food_facts(barcode)
        if result:
            self.log_info(f"Found on Open Food Facts: {result['product_name']}")
            self._cache_product(barcode, result)
            return result

        # Step 3: Not found anywhere
        self.log_warning(f"Product not found for barcode: {barcode}")
        return {
            "found": False,
            "product_name": None,
            "brand": None,
            "ingredient_text": None,
            "source": None,
        }

    def _lookup_local(self, barcode: str) -> Optional[Dict[str, Any]]:
        """Check local database for product."""
        product = self.db.query(Product).filter(Product.barcode == barcode).first()
        if not product:
            return None

        ingredient_names = [ing.name for ing in product.ingredients]
        if not ingredient_names:
            return None

        return {
            "found": True,
            "product_name": product.name,
            "brand": product.brand,
            "ingredient_text": ", ".join(ingredient_names),
            "source": "local_db",
        }

    def _lookup_open_food_facts(self, barcode: str) -> Optional[Dict[str, Any]]:
        """Query Open Food Facts API."""
        try:
            url = self.OPEN_FOOD_FACTS_URL.format(barcode=barcode)
            response = httpx.get(url, timeout=10.0, headers={
                "User-Agent": "BumpRadar/1.0 (https://bumpradar.app)"
            })

            if response.status_code != 200:
                self.log_warning(f"Open Food Facts returned {response.status_code}")
                return None

            data = response.json()

            if data.get("status") != 1:
                return None

            product = data.get("product", {})
            ingredient_text = product.get("ingredients_text_en") or product.get("ingredients_text") or ""

            if not ingredient_text:
                # Try to build from structured ingredients
                ingredients_list = product.get("ingredients", [])
                if ingredients_list:
                    ingredient_text = ", ".join(
                        ing.get("text", "") for ing in ingredients_list if ing.get("text")
                    )

            if not ingredient_text:
                self.log_warning("Product found but no ingredient data available")
                return None

            return {
                "found": True,
                "product_name": product.get("product_name", "Unknown Product"),
                "brand": product.get("brands", None),
                "ingredient_text": ingredient_text,
                "image_url": product.get("image_url"),
                "source": "open_food_facts",
            }

        except httpx.TimeoutException:
            self.log_error("Open Food Facts API timeout")
            return None
        except Exception as e:
            self.log_error(f"Open Food Facts lookup failed: {e}")
            return None

    def _cache_product(self, barcode: str, result: Dict[str, Any]):
        """Cache a remotely-found product in local DB."""
        try:
            existing = self.db.query(Product).filter(Product.barcode == barcode).first()
            if existing:
                return

            product = Product(
                name=result["product_name"],
                brand=result.get("brand"),
                barcode=barcode,
                image_url=result.get("image_url"),
                data_source=result["source"],
            )
            self.db.add(product)
            self.db.commit()
            self.log_info(f"Cached product: {result['product_name']}")
        except Exception as e:
            self.db.rollback()
            self.log_error(f"Failed to cache product: {e}")
