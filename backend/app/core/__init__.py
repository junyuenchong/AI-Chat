"""
Core package.

Shared kernel exports for config, exceptions, and utilities.
"""

from app.core.config import get_settings
from app.core.exceptions import AppError, AppException, error_body

__all__ = ["AppError", "AppException", "error_body", "get_settings"]
