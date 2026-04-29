from typing import List

from pinecone import Pinecone, ServerlessSpec

from ..config import settings
from ..models import AidSheetRequest, EmbeddingRequest, PageRecord, RetrievalCandidate
from .embedding import embed_text
from ..utils.chunking import chunk_text


def _get_index():
    if settings.pinecone_disabled:
        return None
    if not settings.pinecone_api_key or not settings.pinecone_index:
        raise RuntimeError("Pinecone config missing")

    client = Pinecone(api_key=settings.pinecone_api_key)
    existing = {item["name"] for item in client.list_indexes()}
    if settings.pinecone_index not in existing:
        client.create_index(
            name=settings.pinecone_index,
            dimension=settings.pinecone_dimension,
            metric="cosine",
            spec=ServerlessSpec(
                cloud=settings.pinecone_cloud, region=settings.pinecone_region
            ),
        )
    return client.Index(settings.pinecone_index)


async def index_pages(pages: List[PageRecord], source_path: str) -> int:
    index = _get_index()
    if index is None:
        return 0
    requests: List[EmbeddingRequest] = []
    metadata_list: List[dict] = []

    for page in pages:
        chunks = chunk_text(page.text)
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

    if not requests:
        return 0

    embeddings = await embed_text(requests)
    vectors = []
    for embedding, metadata in zip(embeddings, metadata_list):
        vectors.append((embedding.id, embedding.vector, metadata))

    index.upsert(vectors=vectors)
    return len(vectors)


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
