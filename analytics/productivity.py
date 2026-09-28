"""Thin re-export: time/productivity calculations live in roi_engine to avoid
duplicate formula implementations drifting out of sync with the backend."""
from roi_engine import compute_ai_assisted_time_minutes, compute_time_saved, compute_time_saved_percentage

__all__ = ["compute_ai_assisted_time_minutes", "compute_time_saved", "compute_time_saved_percentage"]
