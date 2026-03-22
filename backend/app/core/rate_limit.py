"""
Rate limiting / freemium scan counter
Tracks scans per IP (free) or email (premium) per day.
Free: 3 text/barcode scans/day (NO photo scans — Pro only).
Premium: 20 scans/day (5 photo max).

Cost math (worst case, all users max out daily):
  Free users: $0 (text/barcode only, DB lookups + occasional AI classify)
  Photo scan (GPT-4o-mini Vision): ~$0.03 each — PREMIUM ONLY
  5 photos/day x 30 days = $4.50/month per premium user
  Stripe fee on $9.99: $0.59
  Net revenue: $9.99 - $0.59 = $9.40
  Guaranteed profit per premium user: $9.40 - $4.50 = $4.90/month minimum
  Free users can NEVER cost more than pennies (AI classify fallback only).
"""
import time
from collections import defaultdict
from typing import Tuple

# In-memory store (fine for MVP on single server; swap to Redis later)
_scan_counts: dict = defaultdict(list)  # key -> [timestamp, ...]
_photo_counts: dict = defaultdict(list)  # key -> [timestamp, ...] (photo scans only)

FREE_SCANS_PER_DAY = 3
PREMIUM_SCANS_PER_DAY = 20
PREMIUM_PHOTO_SCANS_PER_DAY = 5
DAY_SECONDS = 86400


def _clean_counts(key: str) -> Tuple[int, int]:
    """Clean expired entries and return (total_scans, photo_scans) for today."""
    now = time.time()
    cutoff = now - DAY_SECONDS
    _scan_counts[key] = [ts for ts in _scan_counts[key] if ts > cutoff]
    _photo_counts[key] = [ts for ts in _photo_counts[key] if ts > cutoff]
    return len(_scan_counts[key]), len(_photo_counts[key])


def check_scan_limit(
    ip: str,
    is_premium: bool = False,
    email: str = None,
    is_photo: bool = False,
) -> Tuple[bool, int, int]:
    """
    Check if a user has remaining scans.

    Premium users are tracked by email (not IP) so limits follow them
    across devices. Free users are tracked by IP.

    Returns:
        (allowed, remaining, total_today)
    """
    key = f"premium:{email}" if is_premium and email else ip
    total_today, photo_today = _clean_counts(key)

    if is_premium:
        limit = PREMIUM_SCANS_PER_DAY
        remaining = max(0, limit - total_today)
        allowed = total_today < limit

        # Additional photo cap check
        if is_photo and photo_today >= PREMIUM_PHOTO_SCANS_PER_DAY:
            allowed = False
            remaining = 0

        return allowed, remaining, total_today

    # Free users: photo scans are BLOCKED (Pro only)
    if is_photo:
        return False, 0, total_today

    remaining = max(0, FREE_SCANS_PER_DAY - total_today)
    allowed = total_today < FREE_SCANS_PER_DAY
    return allowed, remaining, total_today


def record_scan(ip: str, is_premium: bool = False, email: str = None, is_photo: bool = False):
    """Record a scan for the given user."""
    key = f"premium:{email}" if is_premium and email else ip
    _scan_counts[key].append(time.time())
    if is_photo:
        _photo_counts[key].append(time.time())


def get_scan_info(ip: str, is_premium: bool = False, email: str = None) -> dict:
    """Get scan usage info for display."""
    key = f"premium:{email}" if is_premium and email else ip
    total_today, photo_today = _clean_counts(key)

    if is_premium:
        remaining = max(0, PREMIUM_SCANS_PER_DAY - total_today)
        photo_remaining = max(0, PREMIUM_PHOTO_SCANS_PER_DAY - photo_today)
        return {
            "scans_today": total_today,
            "scans_remaining": remaining,
            "limit": PREMIUM_SCANS_PER_DAY,
            "photo_scans_today": photo_today,
            "photo_scans_remaining": photo_remaining,
            "photo_limit": PREMIUM_PHOTO_SCANS_PER_DAY,
            "is_premium": True,
        }

    remaining = max(0, FREE_SCANS_PER_DAY - total_today)
    return {
        "scans_today": total_today,
        "scans_remaining": remaining,
        "limit": FREE_SCANS_PER_DAY,
        "is_premium": False,
        "upgrade_url": "/premium",
    }
