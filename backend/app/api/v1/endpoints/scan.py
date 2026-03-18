"""
Scan endpoint - Core feature
Analyzes products/ingredients for pregnancy safety
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.rate_limit import check_scan_limit, record_scan, get_scan_info
from app.schemas.scan import ScanRequest, ScanResponse
from app.agents.orchestrator import OrchestratorAgent

router = APIRouter()


def _get_client_ip(request: Request) -> str:
    """Extract real client IP (behind nginx proxy)."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host


@router.post("/", response_model=ScanResponse)
async def scan_product(
    request: ScanRequest,
    raw_request: Request,
    db: Session = Depends(get_db),
):
    """
    Scan a product for pregnancy safety.

    Accepts:
    - barcode: Product barcode for database lookup
    - ingredient_text: Comma-separated ingredient list
    - image_base64: Base64-encoded photo for OCR

    Returns traffic-light safety verdict with flagged ingredients.
    Free tier: 3 scans/day.
    """
    # Validate input
    if not request.barcode and not request.ingredient_text and not request.image_base64:
        raise HTTPException(
            status_code=400,
            detail="Must provide either barcode, ingredient_text, or image_base64",
        )

    # Check rate limit
    ip = _get_client_ip(raw_request)
    allowed, remaining, total = check_scan_limit(ip)

    if not allowed:
        raise HTTPException(
            status_code=429,
            detail={
                "message": "Daily scan limit reached! Upgrade to BumpRadar Premium for unlimited scans.",
                "scans_today": total,
                "limit": 3,
                "upgrade_url": "/premium",
            },
        )

    # Run scan
    orchestrator = OrchestratorAgent(db)
    result = orchestrator.execute(request)

    # Record successful scan
    record_scan(ip)
    scan_info = get_scan_info(ip)

    # Inject scan counter into response headers (frontend can read these)
    # We'll add it to the response model instead for simplicity

    return result


@router.get("/usage")
async def scan_usage(request: Request):
    """Get current scan usage for this user."""
    ip = _get_client_ip(request)
    return get_scan_info(ip)
