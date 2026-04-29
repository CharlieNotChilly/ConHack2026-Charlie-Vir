from fastapi import APIRouter

from ..models import AidSheetRequest, AidSheetDraft
from ..services import latex_generator, vector_store

router = APIRouter()


@router.post("/")
async def generate_aidsheet(request: AidSheetRequest) -> AidSheetDraft:
    # [V] TODO: retrieve candidates, enforce constraints, assemble LaTeX
    candidates = await vector_store.retrieve(request)
    draft = await latex_generator.build_draft(request, candidates)
    return draft
