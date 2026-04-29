import base64
import hashlib
from typing import List

import numpy as np
import requests

from ..config import settings
from ..models import EmbeddingRequest, EmbeddingResult

TEXT_EMBED_MODELS = ["text-embedding-004", "embedding-001"]
IMAGE_EMBED_MODEL = "multimodal-embedding-001"


def _get_api_key() -> str:
    if not settings.gemini_api_key:
        raise RuntimeError("Gemini API key missing")
    return settings.gemini_api_key


def _check_dimension(vector: List[float]) -> None:
    if settings.pinecone_dimension and len(vector) != settings.pinecone_dimension:
        raise RuntimeError(
            "Embedding dimension mismatch. "
            f"Pinecone expects {settings.pinecone_dimension}, got {len(vector)}."
        )


def _hash_to_vector(text: str, dimension: int) -> List[float]:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    data = np.frombuffer(digest, dtype=np.uint8).astype(np.float32)
    reps = int(np.ceil(dimension / len(data)))
    tiled = np.tile(data, reps)[:dimension]
    norm = np.linalg.norm(tiled)
    if norm == 0:
        return tiled.tolist()
    return (tiled / norm).tolist()


def _embed_text_sync(text: str) -> List[float]:
    api_key = _get_api_key()
    payload = {"content": {"parts": [{"text": text}]}}
    last_error = None
    for model in TEXT_EMBED_MODELS:
        candidates = [
            (
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:embedContent?key={api_key}",
                payload,
                "values",
            ),
            (
                f"https://generativelanguage.googleapis.com/v1/models/{model}:embedContent?key={api_key}",
                payload,
                "values",
            ),
            (
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:embedText?key={api_key}",
                {"text": text},
                None,
            ),
        ]
        for url, body, value_key in candidates:
            response = requests.post(url, json=body, timeout=30)
            if response.ok:
                data = response.json()["embedding"]
                vector = data["values"] if value_key == "values" else data
                _check_dimension(vector)
                return vector
            last_error = response
            if response.status_code != 404:
                response.raise_for_status()

    if settings.gemini_fallback:
        dimension = settings.pinecone_dimension or 384
        return _hash_to_vector(text, dimension)

    if last_error is not None:
        last_error.raise_for_status()
    raise RuntimeError("Gemini embedding request failed")


def _embed_image_sync(image_bytes: bytes) -> List[float]:
    api_key = _get_api_key()
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{IMAGE_EMBED_MODEL}:embedContent?key={api_key}"
    )
    b64_data = base64.b64encode(image_bytes).decode("ascii")
    payload = {
        "content": {
            "parts": [
                {
                    "inline_data": {
                        "mime_type": "image/png",
                        "data": b64_data,
                    }
                }
            ]
        }
    }
    response = requests.post(url, json=payload, timeout=30)
    response.raise_for_status()
    vector = response.json()["embedding"]["values"]
    _check_dimension(vector)
    return vector


async def embed_text(requests_list: List[EmbeddingRequest]) -> List[EmbeddingResult]:
    results: List[EmbeddingResult] = []
    for req in requests_list:
        vector = _embed_text_sync(req.text)
        results.append(EmbeddingResult(id=req.id, vector=vector))
    return results


async def embed_images(image_bytes_list: List[bytes]) -> List[EmbeddingResult]:
    results: List[EmbeddingResult] = []
    for idx, data in enumerate(image_bytes_list):
        try:
            vector = _embed_image_sync(data)
        except requests.HTTPError:
            if settings.gemini_fallback:
                dimension = settings.pinecone_dimension or 384
                vector = _hash_to_vector(data.hex(), dimension)
            else:
                raise
        results.append(EmbeddingResult(id=f"image-{idx}", vector=vector))
    return results
