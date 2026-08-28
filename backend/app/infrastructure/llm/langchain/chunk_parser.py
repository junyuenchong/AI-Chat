"""Normalize LangChain streaming chunks to plain text."""


def chunk_part(part: object) -> str:
    if isinstance(part, str):
        return part
    if isinstance(part, dict) and part.get("type") == "text":
        return str(part.get("text", ""))
    return ""


def chunk_text(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(chunk_part(part) for part in content)
    return ""
