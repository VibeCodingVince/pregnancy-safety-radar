"""
Scan endpoint - Core feature
Analyzes products/ingredients for pregnancy safety
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Optional

from pydantic import BaseModel

from app.core.database import get_db
from app.core.rate_limit import check_scan_limit, record_scan, get_scan_info, TIER_LIMITS
from app.core.auth import get_optional_user
from app.schemas.scan import ScanRequest, ScanResponse
from app.agents.orchestrator import OrchestratorAgent
from app.models.subscriber import Subscriber
from app.models.user import User
from app.models.scan_history import ScanHistory
from app.models.feedback import Feedback

router = APIRouter()


def _get_client_ip(request: Request) -> str:
    """Extract real client IP (behind nginx proxy)."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host


def _get_tier(email: Optional[str], db: Session) -> str:
    """Get the subscription tier for a user. Returns 'free', 'pro', or 'pro_plus'."""
    if not email:
        return "free"
    subscriber = db.query(Subscriber).filter(Subscriber.email == email).first()
    if subscriber and subscriber.status == "active":
        return subscriber.tier or "pro"
    return "free"


@router.post("/", response_model=ScanResponse)
async def scan_product(
    request: ScanRequest,
    raw_request: Request,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
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

    # Check premium status — JWT auth only (header spoofing removed)
    email = user.email if user else None
    tier = _get_tier(email, db)

    # Determine scan type (photo scans cost more due to Vision API)
    is_photo = bool(request.image_base64)

    # Check rate limit
    ip = _get_client_ip(raw_request)
    allowed, remaining, total = check_scan_limit(
        ip, tier=tier, email=email, is_photo=is_photo
    )

    if not allowed:
        scan_limit, photo_limit = TIER_LIMITS.get(tier, TIER_LIMITS["free"])
        if is_photo:
            if tier == "pro_plus":
                message = f"Daily photo scan limit reached ({photo_limit}/day). Try pasting ingredients as text instead!"
            elif tier == "pro":
                message = f"Daily photo scan limit reached ({photo_limit}/day). Upgrade to Pro+ for 20 photo scans/day!"
            else:
                message = "Photo scanning is a Pro feature. Upgrade to unlock!"
        elif tier != "free":
            message = f"Daily scan limit reached ({scan_limit}/day). Your limit resets tomorrow!"
        else:
            message = "Daily scan limit reached. Try again tomorrow!"
        raise HTTPException(
            status_code=429,
            detail={
                "message": message,
                "scans_today": total,
                "limit": scan_limit,
                "tier": tier,
                "is_premium": tier != "free",
            },
        )

    # Free photo scans use local Tesseract OCR ($0 cost)
    use_local_ocr = is_photo and tier == "free"

    # Run scan
    orchestrator = OrchestratorAgent(db)
    result = orchestrator.execute(request, use_local_ocr=use_local_ocr)

    # Record successful scan
    record_scan(ip, tier=tier, email=email, is_photo=is_photo)

    # Save to scan history if user is logged in
    if user:
        scan_type = "photo" if is_photo else ("barcode" if request.barcode else "text")
        input_summary = (
            result.product_name
            or request.barcode
            or (request.ingredient_text[:100] if request.ingredient_text else "Photo scan")
        )
        history = ScanHistory(
            user_id=user.id,
            scan_type=scan_type,
            input_summary=input_summary,
            overall_safety=result.overall_safety.value if hasattr(result.overall_safety, 'value') else str(result.overall_safety),
            verdict_message=result.verdict_message,
            flagged_count=len(result.flagged_ingredients),
            total_ingredients=result.total_ingredients_analyzed,
            product_name=result.product_name,
            product_brand=result.product_brand,
        )
        db.add(history)
        db.commit()

    return result


@router.get("/usage")
async def scan_usage(
    request: Request,
    email: Optional[str] = None,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
):
    """Get current scan usage for this user."""
    ip = _get_client_ip(request)
    resolved_email = user.email if user else email
    tier = _get_tier(resolved_email, db)
    return get_scan_info(ip, tier=tier, email=resolved_email)


class FeedbackRequest(BaseModel):
    rating: str  # helpful, not_helpful, suggestion
    comment: Optional[str] = None
    product_name: Optional[str] = None
    overall_safety: Optional[str] = None


@router.post("/feedback")
async def submit_feedback(
    body: FeedbackRequest,
    raw_request: Request,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
):
    """Submit feedback on a scan result."""
    if body.rating not in ("helpful", "not_helpful", "suggestion"):
        raise HTTPException(status_code=400, detail="Invalid rating")

    feedback = Feedback(
        rating=body.rating,
        comment=body.comment[:1000] if body.comment else None,
        product_name=body.product_name[:255] if body.product_name else None,
        overall_safety=body.overall_safety,
        user_id=user.id if user else None,
        ip_address=_get_client_ip(raw_request),
    )
    db.add(feedback)
    db.commit()
    return {"status": "ok"}
