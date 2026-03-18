"""
Rate limiting / freemium scan counter
Tracks scans per IP per day — free tier gets 3 scans/day
"""
import time
from collections import defaultdict
from typing import Tuple

# In-memory store (fine for MVP on single server; swap to Redis later)
_scan_counts: dict = defaultdict(list)  # ip -> [timestamp, timestamp, ...]

FREE_SCANS_PER_DAY = 3
DAY_SECONDS = 86400


def check_scan_limit(ip: str) -> Tuple[bool, int, int]:
    """
    Check if an IP has remaining free scans.

    Returns:
        (allowed, remaining, total_today)
    """
    now = time.time()
    cutoff = now - DAY_SECONDS

    # Clean old entries
    _scan_counts[ip] = [ts for ts in _scan_counts[ip] if ts > cutoff]

    total_today = len(_scan_counts[ip])
    remaining = max(0, FREE_SCANS_PER_DAY - total_today)
    allowed = total_today < FREE_SCANS_PER_DAY

    return allowed, remaining, total_today


def record_scan(ip: str):
    """Record a scan for the given IP."""
    _scan_counts[ip].append(time.time())


def get_scan_info(ip: str) -> dict:
    """Get scan usage info for display."""
    now = time.time()
    cutoff = now - DAY_SECONDS
    _scan_counts[ip] = [ts for ts in _scan_counts[ip] if ts > cutoff]

    total_today = len(_scan_counts[ip])
    remaining = max(0, FREE_SCANS_PER_DAY - total_today)

    return {
        "scans_today": total_today,
        "scans_remaining": remaining,
        "limit": FREE_SCANS_PER_DAY,
        "is_premium": False,  # TODO: check subscription
        "upgrade_url": "/premium",
    }
