"""Split document text into overlapping chunks for ingest and embedding."""


# ---------------------------------------------------------------------------
# Chunker — overlap keeps context across boundaries for better retrieve.
# ---------------------------------------------------------------------------
def split_text(text: str, size: int = 500, overlap: int = 80) -> list[str]:
    """Chunk raw text. Used by knowledge ingest and the embed job."""
    cleaned = text.strip()
    if not cleaned:
        return []
    if len(cleaned) <= size:
        return [cleaned]

    chunks: list[str] = []
    start = 0
    while start < len(cleaned):
        end = min(start + size, len(cleaned))
        chunks.append(cleaned[start:end])
        if end == len(cleaned):
            break
        start = max(end - overlap, start + 1)
    return chunks
