from fastapi import APIRouter

from ..models import AidSheetDraft, AidSheetPreview, AidSheetRequest
from ..services import latex_generator, vector_store
from ..utils.pdf_stub import placeholder_pdf_base64

router = APIRouter()


@router.post("/")
async def generate_aidsheet(request: AidSheetRequest) -> AidSheetDraft:
    # [V] TODO: enforce constraints, assemble LaTeX with formulas + figures
    candidates = await vector_store.retrieve(request)
    draft = await latex_generator.build_draft(request, candidates)
    if not candidates:
        draft.warnings = [
            "No retrieval candidates found; draft uses placeholder content."
        ]
    return draft


@router.post("/preview", response_model=AidSheetPreview)
async def preview_aidsheet(request: AidSheetRequest) -> AidSheetPreview:
    candidates = await vector_store.retrieve(request)
    draft = await latex_generator.build_draft(request, candidates)
    warnings = draft.warnings or []
    if not candidates:
        warnings = warnings + [
            "Preview uses placeholder PDF. Run ingestion to populate data."
        ]
    return AidSheetPreview(
        latex_source=draft.latex_source,
        pdf_base64=placeholder_pdf_base64(),
        warnings=warnings or None,
    )
