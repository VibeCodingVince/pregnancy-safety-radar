"""
OCR Agent
Extracts ingredient lists from product photos using OpenAI Vision
"""
import base64
import json
import re
from typing import Optional
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.core.config import settings
from app.core.cost_guard import can_make_api_call, record_api_call

try:
    import openai
except ImportError:
    openai = None


class OCRAgent(BaseAgent):
    """
    OCR Agent - Image to ingredient text extraction

    Uses OpenAI GPT-4o-mini vision to:
    1. Identify ingredient lists in product photos
    2. Extract and clean the text
    3. Return structured ingredient text ready for classification
    """

    def execute(self, image_base64: str) -> dict:
        """
        Extract ingredients from a product photo.

        Args:
            image_base64: Base64-encoded image (JPEG/PNG)

        Returns:
            Dict with keys: success, ingredient_text, product_name, confidence, error
        """
        self.log_info("Processing image for ingredient extraction")

        if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY.strip() == "":
            self.log_error("OpenAI API key not configured")
            return {
                "success": False,
                "ingredient_text": None,
                "product_name": None,
                "confidence": 0.0,
                "error": "⚠️ Photo scanning requires an OpenAI API key. Add your key to backend/.env file (OPENAI_API_KEY=sk-...) then restart the server.",
            }

        if not openai:
            return {
                "success": False,
                "ingredient_text": None,
                "product_name": None,
                "confidence": 0.0,
                "error": "OpenAI library not installed. Run: pip install openai",
            }

        # Validate image
        if not self._validate_image(image_base64):
            return {
                "success": False,
                "ingredient_text": None,
                "product_name": None,
                "confidence": 0.0,
                "error": "Invalid image data. Please provide a clear photo of the ingredient list.",
            }

        # Global cost circuit breaker
        if not can_make_api_call():
            self.log_error("Daily API budget exhausted — blocking Vision call")
            return {
                "success": False,
                "ingredient_text": None,
                "product_name": None,
                "confidence": 0.0,
                "error": "Our photo scanning service is temporarily at capacity. Please try again tomorrow or paste your ingredients as text instead.",
            }

        return self._extract_with_vision(image_base64)

    def _validate_image(self, image_base64: str) -> bool:
        """Basic validation of base64 image data."""
        try:
            # Strip data URL prefix if present
            if "," in image_base64:
                image_base64 = image_base64.split(",", 1)[1]
            decoded = base64.b64decode(image_base64)
            # Check minimum size (at least 1KB — not a blank image)
            if len(decoded) < 1024:
                return False
            # Check for common image headers
            if decoded[:3] == b'\xff\xd8\xff':  # JPEG
                return True
            if decoded[:8] == b'\x89PNG\r\n\x1a\n':  # PNG
                return True
            if decoded[:4] == b'RIFF' and decoded[8:12] == b'WEBP':  # WebP
                return True
            # Allow it anyway — Vision API will reject truly bad data
            return True
        except Exception:
            return False

    def _extract_with_vision(self, image_base64: str) -> dict:
        """Use OpenAI Vision to extract ingredients from image."""
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

        # Strip data URL prefix if present
        if "," in image_base64:
            image_base64 = image_base64.split(",", 1)[1]

        # Detect MIME type
        try:
            decoded = base64.b64decode(image_base64[:32])
            if decoded[:3] == b'\xff\xd8\xff':
                mime = "image/jpeg"
            elif decoded[:8] == b'\x89PNG\r\n\x1a\n':
                mime = "image/png"
            else:
                mime = "image/jpeg"
        except Exception:
            mime = "image/jpeg"

        data_url = f"data:{mime};base64,{image_base64}"

        try:
            self.log_info("Calling OpenAI Vision API...")
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                timeout=30.0,  # 30 second timeout
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """You are reading a product label photo. Extract the INGREDIENTS LIST.

Rules:
1. Find the ingredient list (usually starts with "Ingredients:" or "Active Ingredients:")
2. Extract ALL ingredients exactly as written
3. Clean up any OCR artifacts or line breaks
4. Return them as a clean, comma-separated list
5. If you can identify the product name, include it
6. Rate your confidence in the extraction (0.0 to 1.0)

Respond with ONLY valid JSON:
{
    "product_name": "Name if visible, or null",
    "ingredient_text": "Ingredient 1, Ingredient 2, ...",
    "confidence": 0.85,
    "notes": "Any relevant notes about readability"
}

If you cannot find an ingredient list in the image, respond:
{
    "product_name": null,
    "ingredient_text": null,
    "confidence": 0.0,
    "notes": "Reason why extraction failed"
}"""
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": data_url,
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                temperature=0.1,
                max_tokens=2000,
            )

            record_api_call()
            content = response.choices[0].message.content.strip()

            # Strip markdown code fences if present
            content = re.sub(r'^```json\s*', '', content)
            content = re.sub(r'\s*```$', '', content)

            result = json.loads(content)

            ingredient_text = result.get("ingredient_text")
            if not ingredient_text:
                return {
                    "success": False,
                    "ingredient_text": None,
                    "product_name": result.get("product_name"),
                    "confidence": 0.0,
                    "error": result.get("notes", "Could not find ingredients in the image"),
                }

            return {
                "success": True,
                "ingredient_text": ingredient_text,
                "product_name": result.get("product_name"),
                "confidence": min(result.get("confidence", 0.7), 0.95),
                "error": None,
            }

        except json.JSONDecodeError:
            self.log_error("Failed to parse Vision API response as JSON")
            return {
                "success": False,
                "ingredient_text": None,
                "product_name": None,
                "confidence": 0.0,
                "error": "Failed to process the image. Please try a clearer photo.",
            }
        except Exception as e:
            self.log_error(f"Vision API call failed: {e}")
            return {
                "success": False,
                "ingredient_text": None,
                "product_name": None,
                "confidence": 0.0,
                "error": f"Image processing error: {str(e)}",
            }
