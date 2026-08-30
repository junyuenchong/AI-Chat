"""Document domain types."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DocumentUpload:
    """Validated upload payload before persistence."""

    user_id: str
    filename: str
    content: str
