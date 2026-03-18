"""
Scan endpoint - Core feature
Analyzes products/ingredients for pregnancy safety
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.scan import ScanRequest, ScanResponse
from app.agents.orchestrator import OrchestratorAgent

router = APIRouter()


@router.post("/", response_model=ScanResponse)
async def scan_product(
    request: ScanRequest,
    db: Session = Depends(get_db)
):
    """
    Scan a product for pregnancy safety

    Accepts:
    - barcode: Product barcode for database lookup
    - ingredient_text: Comma-separated ingredient list
    - image_base64: Image for OCR (future feature)

    Returns:
    - Traffic-light safety verdict (safe/caution/avoid/unknown)
    - Flagged ingredients with explanations
    - Safe alternatives
    """
    # Validate request
    if not request.barcode and not request.ingredient_text and not request.image_base64:
        raise HTTPException(
            status_code=400,
            detail="Must provide either barcode, ingredient_text, or image_base64"
        )

    # Delegate to orchestrator agent
    orchestrator = OrchestratorAgent(db)
    result = orchestrator.execute(request)

    return result
