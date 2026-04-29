from typing import List

from ..models import EmbeddingRequest, EmbeddingResult


async def embed_text(requests: List[EmbeddingRequest]) -> List[EmbeddingResult]:
    # [V] TODO: call Gemini text embedding model
    return []


async def embed_images(image_bytes_list: List[bytes]) -> List[EmbeddingResult]:
    # [V] TODO: call image embedding provider (Voyage or Gemini multimodal)
    return []
