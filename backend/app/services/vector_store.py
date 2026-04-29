import logging
from pathlib import Path
from typing import List

import fitz
from pinecone import Pinecone, ServerlessSpec

from ..config import settings
from ..models import AidSheetRequest, EmbeddingRequest, PageRecord, RetrievalCandidate
from .embedding import embed_text, embed_images_with_ids
from ..utils.chunking import chunk_text

logger = logging.getLogger(__name__)


def _list_index_names(client) -> set:
    try:
        return set(client.list_indexes().names())
    except Exception:
        try:
            return {item["name"] for item in client.list_indexes()}
        except Exception:
            return {item.name for item in client.list_indexes()}


def _get_index():
    if settings.pinecone_disabled:
        logger.info("Pinecone disabled; skipping index")
        return None
    if not settings.pinecone_api_key or not settings.pinecone_index:
        logger.error("Pinecone config missing")
        raise RuntimeError("Pinecone config missing")

    client = Pinecone(api_key=settings.pinecone_api_key)
    existing = _list_index_names(client)
    if settings.pinecone_index not in existing:
        logger.info(
            "Creating Pinecone index",
            extra={
                "index": settings.pinecone_index,
                "dimension": settings.pinecone_dimension,
                "cloud": settings.pinecone_cloud,
                "region": settings.pinecone_region,
            },
        )
        client.create_index(
            name=settings.pinecone_index,
            dimension=settings.pinecone_dimension,
            metric="cosine",
            spec=ServerlessSpec(
                cloud=settings.pinecone_cloud, region=settings.pinecone_region
            ),
        )
    return client.Index(settings.pinecone_index)


def _extract_images(file_path: str, lecture_id: str) -> List[dict]:
    images: List[dict] = []
    try:
        with fitz.open(file_path) as doc:
            for page_number, page in enumerate(doc, start=1):
                for img_index, img in enumerate(page.get_images(full=True)):
                    xref = img[0]
                    base = doc.extract_image(xref)
                    image_bytes = base.get("image")
                    if not image_bytes:
                        continue
                    image_ext = base.get("ext") or "png"
                    if image_ext.lower() == "jpg":
                        image_ext = "jpeg"
                    images.append(
                        {
                            "id": f"{lecture_id}-p{page_number}-i{img_index}",
                            "bytes": image_bytes,
                            "mime_type": f"image/{image_ext}",
                            "metadata": {
                                "lecture_id": lecture_id,
                                "page_number": page_number,
                                "image_index": img_index,
                                "image_xref": xref,
                                "image_ext": image_ext,
                                "image_width": base.get("width"),
                                "image_height": base.get("height"),
                                "source_path": file_path,
                                "type": "image",
                            },
                        }
                    )
    except Exception:
        logger.exception("Image extraction failed", extra={"source_path": file_path})
        raise
    return images


async def index_pages(pages: List[PageRecord], source_path: str) -> int:
    index = _get_index()
    if index is None:
        return 0
    requests: List[EmbeddingRequest] = []
    metadata_list: List[dict] = []
    total_chunks = 0
    batch_size = 48
    
    try:
        for page in pages:
            chunks = chunk_text(page.text)
            total_chunks += len(chunks)
            for chunk_index, chunk in enumerate(chunks):
                chunk_id = f"{page.lecture_id}-p{page.page_number}-c{chunk_index}"
                requests.append(EmbeddingRequest(id=chunk_id, text=chunk))
                metadata_list.append(
                    {
                        "lecture_id": page.lecture_id,
                        "page_number": page.page_number,
                        "chunk_index": chunk_index,
                        "source_path": source_path,
                        "type": "text",
                        "content": chunk,
                    }
                )

                if len(requests) >= batch_size:
                    logger.info(
                        "Embedding batch",
                        extra={
                            "batch": len(requests),
                            "source_path": source_path,
                            "chunks_total": total_chunks,
                        },
                    )
                    embeddings = await embed_text(requests)
                    vectors = []
                    for embedding, metadata in zip(embeddings, metadata_list):
                        vectors.append((embedding.id, embedding.vector, metadata))
                    logger.info(
                        "Upserting batch",
                        extra={"count": len(vectors), "source_path": source_path},
                    )
                    index.upsert(vectors=vectors)
                    requests = []
                    metadata_list = []
    except Exception:
        logger.exception(
            "Chunking failed",
            extra={"source_path": source_path, "page_count": len(pages)},
        )
        raise

    if not requests and total_chunks == 0:
        logger.info("No text chunks to index", extra={"source_path": source_path})
        return 0

    try:
        if requests:
            logger.info(
                "Embedding final batch",
                extra={"count": len(requests), "source_path": source_path},
            )
            embeddings = await embed_text(requests)
            vectors = []
            for embedding, metadata in zip(embeddings, metadata_list):
                vectors.append((embedding.id, embedding.vector, metadata))

            logger.info(
                "Upserting final batch",
                extra={"count": len(vectors), "source_path": source_path},
            )
            index.upsert(vectors=vectors)
        text_chunk_total = total_chunks
        image_vectors_total = 0
        lecture_id = pages[0].lecture_id if pages else Path(source_path).stem
        images = _extract_images(source_path, lecture_id)
        if images:
            logger.info(
                "Extracted images",
                extra={"count": len(images), "source_path": source_path},
            )
            image_batch_size = 8
            for i in range(0, len(images), image_batch_size):
                batch = images[i : i + image_batch_size]
                entries = [
                    (item["id"], item["bytes"], item["mime_type"]) for item in batch
                ]
                logger.info(
                    "Embedding image batch",
                    extra={"count": len(entries), "source_path": source_path},
                )
                embeddings = await embed_images_with_ids(entries)
                vectors = []
                for embedding, item in zip(embeddings, batch):
                    vectors.append((embedding.id, embedding.vector, item["metadata"]))
                logger.info(
                    "Upserting image batch",
                    extra={"count": len(vectors), "source_path": source_path},
                )
                index.upsert(vectors=vectors)
                image_vectors_total += len(vectors)

        return text_chunk_total + image_vectors_total
    except Exception:
        logger.exception(
            "Vector indexing failed",
            extra={"source_path": source_path, "chunks": total_chunks},
        )
        raise


async def retrieve(request: AidSheetRequest) -> List[RetrievalCandidate]:
    index = _get_index()
    if index is None:
        return []
    query_text = request.instructions or "aid sheet"
    embeddings = await embed_text([EmbeddingRequest(id="query", text=query_text)])
    query_vector = embeddings[0].vector
    response = index.query(vector=query_vector, top_k=20, include_metadata=True)

    candidates: List[RetrievalCandidate] = []
    for match in response.get("matches", []):
        metadata = match.get("metadata", {})
        candidates.append(
            RetrievalCandidate(
                id=match.get("id", ""),
                type=metadata.get("type", "text"),
                content=metadata.get("content", ""),
                metadata=metadata,
            )
        )
    return candidates
