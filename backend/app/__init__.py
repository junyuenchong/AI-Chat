"""
Application package root.

Top-level exports for the FastAPI app package.
"""

from app.core.config import get_settings

__all__ = ["get_settings"]
