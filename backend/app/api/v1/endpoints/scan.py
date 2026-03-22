"""
Scan endpoint - Core feature
Analyzes products/ingredients for pregnancy safety
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.rate_limit import check_scan_limit, record_scan, get_scan_info
from app.core.auth import get_optional_user
from app.schemas.scan import ScanRequest, ScanResponse
from app.agents.orchestrator import OrchestratorAgent
from app.models.subscriber import Subscriber
from app.models.user import User

router = APIRouter()


def _get_client_ip(request: Request) -> str:
    """Extract real client IP (behind nginx proxy)."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host


def _check_premium(email: Optional[str], db: Session) -> bool:
    """Check if an email has an active premium subscription."""
    if not email:
        return False
    subscriber = db.query(Subscriber).filter(Subscriber.email == email).first()
    return subscriber is not None and subscriber.status == "active"


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
    is_premium = _check_premium(email, db)

    # Determine scan type (photo scans cost more due to Vision API)
    is_photo = bool(request.image_base64)

    # Check rate limit
    ip = _get_client_ip(raw_request)
    allowed, remaining, total = check_scan_limit(
        ip, is_premium=is_premium, email=email, is_photo=is_photo
    )

    if not allowed:
        if not is_premium and is_photo:
            # Free user trying photo scan — this is a Pro feature
            raise HTTPException(
                status_code=403,
                detail={
                    "message": "Photo scanning is a Pro feature. Upgrade to BumpRadar Premium for $9.99/mo to unlock photo scans, or paste your ingredients as text for free!",
                    "photo_pro_only": True,
                    "is_premium": False,
                },
            )
        elif is_premium and is_photo:
            message = "Daily photo scan limit reached (5/day). Try pasting ingredients as text instead!"
        elif is_premium:
            message = "Daily scan limit reached (20/day). Your limit resets tomorrow!"
        else:
            message = "Daily scan limit reached! Upgrade to BumpRadar Premium for 20 scans/day."
        raise HTTPException(
            status_code=429,
            detail={
                "message": message,
                "scans_today": total,
                "limit": 20 if is_premium else 3,
                "is_premium": is_premium,
            },
        )

    # Run scan
    orchestrator = OrchestratorAgent(db)
    result = orchestrator.execute(request)

    # Record successful scan
    record_scan(ip, is_premium=is_premium, email=email, is_photo=is_photo)

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
    is_premium = _check_premium(resolved_email, db)
    return get_scan_info(ip, is_premium=is_premium, email=resolved_email)
