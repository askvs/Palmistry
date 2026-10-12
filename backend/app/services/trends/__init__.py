"""Life trend analysis engine package (Milestone 3)."""
from app.services.trends.engine import (
    DOMAIN_LABELS,
    ENGINE_NAME,
    ENGINE_VERSION,
    METHOD,
    LifeTrendEngine,
    extract_reading_signals,
)

__all__ = [
    "LifeTrendEngine",
    "extract_reading_signals",
    "DOMAIN_LABELS",
    "ENGINE_NAME",
    "ENGINE_VERSION",
    "METHOD",
]
