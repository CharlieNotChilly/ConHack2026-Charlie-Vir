from typing import List, Optional

from pydantic import BaseModel


class PageRecord(BaseModel):
    lecture_id: str
    page_number: int
    text: str
    width: int
    height: int


class FormulaBlock(BaseModel):
    latex: str
    bbox: Optional[List[int]] = None


class EmbeddingRequest(BaseModel):
    id: str
    text: str


class EmbeddingResult(BaseModel):
    id: str
    vector: List[float]


class RetrievalCandidate(BaseModel):
    id: str
    type: str
    content: str
    metadata: dict


class AidSheetRequest(BaseModel):
    course_id: str
    target_pages: int
    instructions: Optional[str] = None


class AidSheetDraft(BaseModel):
    latex_source: str
