import tempfile

from fastapi import APIRouter

from ..models import AidSheetDraft, AidSheetPreview, AidSheetRequest, AidSheetPreviewRequest
from ..services import image_extractor, latex_generator, latex_renderer, vector_store
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
async def preview_aidsheet(request: AidSheetPreviewRequest) -> AidSheetPreview:
    candidates = await vector_store.retrieve(request)
    draft = await latex_generator.build_draft(request, candidates)
    latex_source = request.latex_source or draft.latex_source
    warnings = draft.warnings or []
    if not candidates:
        warnings = warnings + [
            "Preview uses placeholder PDF. Run ingestion to populate data."
        ]

    with tempfile.TemporaryDirectory(prefix="aid-preview-") as work_dir:
        image_entries = image_extractor.materialize_images(candidates, work_dir)
        if image_entries:
            latex_source = latex_generator.append_images(latex_source, image_entries)

        pdf_bytes, error = latex_renderer.compile_latex_to_pdf(latex_source, work_dir)
        if error:
            warnings = warnings + [error]
            return AidSheetPreview(
                latex_source=latex_source,
                pdf_base64=placeholder_pdf_base64(),
                warnings=warnings or None,
            )

        return AidSheetPreview(
            latex_source=latex_source,
            pdf_base64=latex_renderer.pdf_bytes_to_base64(pdf_bytes),
            warnings=warnings or None,
        )
