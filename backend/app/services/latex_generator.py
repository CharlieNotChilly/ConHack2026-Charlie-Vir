from typing import List

from ..models import AidSheetDraft, AidSheetRequest, RetrievalCandidate


async def build_draft(
    request: AidSheetRequest, candidates: List[RetrievalCandidate]
) -> AidSheetDraft:
    # [V] TODO: assemble LaTeX with exact formulas + figures
    return AidSheetDraft(latex_source="% TODO")
