import base64
import hashlib
from typing import List, Tuple

import numpy as np
import requests

from ..config import settings
from ..models import EmbeddingRequest, EmbeddingResult

TEXT_EMBED_MODELS = ["gemini-embedding-2"]
IMAGE_EMBED_MODELS = ["gemini-embedding-2"]


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
    raise RuntimeError(
        "Gemini embedding request failed. Check GEMINI_API_KEY and model access."
    )


def _embed_image_sync(image_bytes: bytes, mime_type: str) -> List[float]:
    api_key = _get_api_key()
    b64_data = base64.b64encode(image_bytes).decode("ascii")
    payload = {
        "content": {
            "parts": [
                {
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": b64_data,
                    }
                }
            ]
        }
    }
    last_error = None
    for model in IMAGE_EMBED_MODELS:
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:embedContent?key={api_key}"
        )
        response = requests.post(url, json=payload, timeout=30)
        if response.ok:
            vector = response.json()["embedding"]["values"]
            _check_dimension(vector)
            return vector
        last_error = response
        if response.status_code != 404:
            response.raise_for_status()

    if settings.gemini_fallback:
        dimension = settings.pinecone_dimension or 384
        return _hash_to_vector(image_bytes.hex(), dimension)

    if last_error is not None:
        last_error.raise_for_status()
    raise RuntimeError(
        "Gemini image embedding request failed. Check GEMINI_API_KEY and model access."
    )


async def embed_text(requests_list: List[EmbeddingRequest]) -> List[EmbeddingResult]:
    results: List[EmbeddingResult] = []
    for req in requests_list:
        vector = _embed_text_sync(req.text)
        results.append(EmbeddingResult(id=req.id, vector=vector))
    return results


async def embed_images_with_ids(
    image_entries: List[Tuple[str, bytes, str]]
) -> List[EmbeddingResult]:
    results: List[EmbeddingResult] = []
    for image_id, data, mime_type in image_entries:
        vector = _embed_image_sync(data, mime_type)
        results.append(EmbeddingResult(id=image_id, vector=vector))
    return results


async def embed_images(image_bytes_list: List[bytes]) -> List[EmbeddingResult]:
    entries = [
        (f"image-{idx}", data, "image/png")
        for idx, data in enumerate(image_bytes_list)
    ]
    return await embed_images_with_ids(entries)