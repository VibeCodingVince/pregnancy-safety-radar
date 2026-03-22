"""
Global cost circuit breaker.
Tracks total OpenAI API calls per day and blocks all calls once the daily
budget is exhausted. This is the last line of defence — even if rate limiting
has a bug, this cap guarantees bounded spend.

Default limit: 5 000 calls/day ≈ $150/day (at ~$0.03 per Vision call).
Adjust DAILY_API_CALL_LIMIT via environment variable if needed.
"""
import os
import time

DAILY_API_CALL_LIMIT = int(os.environ.get("DAILY_API_CALL_LIMIT", "5000"))
_DAY_SECONDS = 86400

_call_timestamps: list[float] = []


def _clean() -> int:
    """Remove timestamps older than 24 h, return today's count."""
    global _call_timestamps
    cutoff = time.time() - _DAY_SECONDS
    _call_timestamps = [ts for ts in _call_timestamps if ts > cutoff]
    return len(_call_timestamps)


def can_make_api_call() -> bool:
    """Return True if we are still under the daily API call budget."""
    return _clean() < DAILY_API_CALL_LIMIT


def record_api_call() -> None:
    """Record that an OpenAI API call was made."""
    _call_timestamps.append(time.time())


def get_usage() -> dict:
    """Return current usage stats (for admin/monitoring)."""
    count = _clean()
    return {
        "api_calls_today": count,
        "daily_limit": DAILY_API_CALL_LIMIT,
        "remaining": max(0, DAILY_API_CALL_LIMIT - count),
        "budget_exhausted": count >= DAILY_API_CALL_LIMIT,
    }
