from typing import List

from ..models import AidSheetRequest, RetrievalCandidate


async def index_items() -> None:
    # [V] TODO: upsert text/image vectors with metadata into Pinecone
    return None


async def retrieve(request: AidSheetRequest) -> List[RetrievalCandidate]:
    # [V] TODO: query Pinecone with constraints
    return []
