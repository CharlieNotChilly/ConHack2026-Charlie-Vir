from typing import List


def chunk_text(text: str, max_chars: int = 800, overlap: int = 80) -> List[str]:
    if not text:
        return []
    if max_chars <= 0:
        return [text]

    chunks: List[str] = []
    start = 0
    length = len(text)
    while start < length:
        prev_start = start
        end = min(start + max_chars, length)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= length:
            break
        start = end - overlap
        if start < 0:
            start = 0
        if start == prev_start:
            break
        if start >= length:
            break
    return chunks
