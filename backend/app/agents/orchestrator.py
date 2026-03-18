"""
Orchestrator Agent
Routes scan requests to appropriate handlers
"""
from sqlalchemy.orm import Session
from app.agents.base import BaseAgent
from app.agents.safety_classifier import SafetyClassifierAgent
from app.agents.product_scanner import ProductScannerAgent
from app.agents.ocr_agent import OCRAgent
from app.schemas.scan import ScanRequest, ScanResponse
from app.models.enums import SafetyLevel


class OrchestratorAgent(BaseAgent):
    """
    Orchestrator Agent - Routes scan requests

    Responsibilities:
    1. If barcode provided -> ProductScannerAgent -> classifier
    2. If ingredient_text provided -> delegate directly to classifier
    3. If image provided -> OCRAgent -> classifier
    """

    def execute(self, request: ScanRequest) -> ScanResponse:
        """
        Execute scan request routing
        """
        self.log_info(f"Orchestrating scan request: barcode={request.barcode}, "
                      f"has_text={bool(request.ingredient_text)}, "
                      f"has_image={bool(request.image_base64)}")

        # Route 1: Barcode lookup via ProductScannerAgent
        if request.barcode:
            return self._handle_barcode_scan(request.barcode)

        # Route 2: Direct ingredient text analysis
        if request.ingredient_text:
            return self._handle_ingredient_text(request.ingredient_text)

        # Route 3: Image OCR via OCRAgent
        if request.image_base64:
            return self._handle_image_scan(request.image_base64)

        raise ValueError("No valid input provided")

    def _handle_barcode_scan(self, barcode: str) -> ScanResponse:
        """Handle barcode-based product lookup using ProductScannerAgent."""
        scanner = ProductScannerAgent(self.db)
        result = scanner.execute(barcode)

        if not result["found"]:
            return ScanResponse(
                overall_safety=SafetyLevel.UNKNOWN,
                verdict_message="Product not found. Try scanning the ingredient list instead.",
                flagged_ingredients=[],
                total_ingredients_analyzed=0,
                confidence=0.0,
            )

        # Classify the ingredients
        classifier = SafetyClassifierAgent(self.db)
        scan_result = classifier.execute(result["ingredient_text"])

        # Add product metadata
        scan_result.product_name = result.get("product_name")
        scan_result.product_brand = result.get("brand")

        return scan_result

    def _handle_ingredient_text(self, ingredient_text: str) -> ScanResponse:
        """Handle direct ingredient text analysis."""
        classifier = SafetyClassifierAgent(self.db)
        return classifier.execute(ingredient_text)

    def _handle_image_scan(self, image_base64: str) -> ScanResponse:
        """Handle image-based scanning via OCR Agent."""
        ocr = OCRAgent(self.db)
        ocr_result = ocr.execute(image_base64)

        if not ocr_result["success"]:
            return ScanResponse(
                overall_safety=SafetyLevel.UNKNOWN,
                verdict_message=ocr_result.get("error", "Could not read the image. Please try a clearer photo."),
                flagged_ingredients=[],
                total_ingredients_analyzed=0,
                confidence=0.0,
            )

        # Classify extracted ingredients
        classifier = SafetyClassifierAgent(self.db)
        scan_result = classifier.execute(ocr_result["ingredient_text"])

        # Add product metadata from OCR
        if ocr_result.get("product_name"):
            scan_result.product_name = ocr_result["product_name"]

        return scan_result
