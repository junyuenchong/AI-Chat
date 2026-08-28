"""
Chat commands.

Re-exports domain command types for application consumers.
"""

from app.domain.chat.entities import ChatCommand

# ────────────────────────────────────────────────────────
# ChatCommand
# Internal — application command type
# Re-exported from domain for use by chat service and mapper.
# ────────────────────────────────────────────────────────

__all__ = ["ChatCommand"]
