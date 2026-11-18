"""Small presentation-only helpers shared by AquaLoad pages."""

from datetime import datetime


def friendly_datetime(value, fallback: str = "Not available") -> str:
    """Render database timestamps in a concise, local-friendly form."""
    if not value:
        return fallback
    if isinstance(value, datetime):
        parsed = value
    else:
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except (TypeError, ValueError):
            return str(value)
    return parsed.strftime("%d %b %Y, %I:%M %p")
