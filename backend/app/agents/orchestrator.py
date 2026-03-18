"""
Orchestrator Agent
Routes scan requests to appropriate handlers
"""
from sqlalchemy.orm import Session
from app.agents.base import BaseAgent
from app.agents.safety_classifier import SafetyClassifierAgent
from app.schemas.scan import ScanRequest, ScanResponse
from app.models.product import Product


class OrchestratorAgent(BaseAgent):
    """
    Orchestrator Agent - Routes scan requests

    Responsibilities:
    1. If barcode provided -> lookup product in DB -> delegate to classifier
    2. If ingredient_text provided -> delegate directly to classifier
    3. If image provided -> delegate to OCR agent (future) -> classifier
    """

    def execute(self, request: ScanRequest) -> ScanResponse:
        """
        Execute scan request routing

        Args:
            request: ScanRequest with barcode, ingredient_text, or image

        Returns:
            ScanResponse with safety verdict
        """
        self.log_info(f"Orchestrating scan request: barcode={request.barcode}, has_text={bool(request.ingredient_text)}")

        # Route 1: Barcode lookup
        if request.barcode:
            return self._handle_barcode_scan(request.barcode)

        # Route 2: Direct ingredient text analysis
        if request.ingredient_text:
            return self._handle_ingredient_text(request.ingredient_text)

        # Route 3: Image OCR (future)
        if request.image_base64:
            self.log_warning("Image OCR not yet implemented")
            return ScanResponse(
                overall_safety="unknown",
                verdict_message="Image scanning not yet available",
                flagged_ingredients=[],
                total_ingredients_analyzed=0,
                confidence=0.0
            )

        # Should not reach here due to validation in endpoint
        raise ValueError("No valid input provided")

    def _handle_barcode_scan(self, barcode: str) -> ScanResponse:
        """
        Handle barcode-based product lookup

        Args:
            barcode: Product barcode (UPC/EAN)

        Returns:
            ScanResponse with product analysis
        """
        self.log_info(f"Looking up product by barcode: {barcode}")

        # Lookup product in database
        product = self.db.query(Product).filter(Product.barcode == barcode).first()

        if not product:
            self.log_warning(f"Product not found for barcode: {barcode}")
            return ScanResponse(
                overall_safety="unknown",
                verdict_message="Product not found in database. Try entering ingredients manually.",
                flagged_ingredients=[],
                total_ingredients_analyzed=0,
                product_name=None,
                product_brand=None,
                confidence=0.0
            )

        # Product found - get ingredient list and analyze
        ingredient_names = [ing.name for ing in product.ingredients]
        ingredient_text = ", ".join(ingredient_names)

        self.log_info(f"Found product: {product.name} ({product.brand}) with {len(ingredient_names)} ingredients")

        # Delegate to classifier
        classifier = SafetyClassifierAgent(self.db)
        result = classifier.execute(ingredient_text)

        # Add product metadata to response
        result.product_name = product.name
        result.product_brand = product.brand

        return result

    def _handle_ingredient_text(self, ingredient_text: str) -> ScanResponse:
        """
        Handle direct ingredient text analysis

        Args:
            ingredient_text: Comma-separated ingredient list

        Returns:
            ScanResponse with ingredient analysis
        """
        self.log_info(f"Analyzing ingredient text (length: {len(ingredient_text)})")

        # Delegate to classifier
        classifier = SafetyClassifierAgent(self.db)
        result = classifier.execute(ingredient_text)

        return result
