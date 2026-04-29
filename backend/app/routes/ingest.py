from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, HTTPException, UploadFile

from ..models import IngestResult
from ..services import pdf_parser, storage, vector_store

router = APIRouter()


@router.post("/upload", response_model=IngestResult)
async def upload_lecture(file: UploadFile) -> IngestResult:
    file_path = await storage.save_upload(file)
    lecture_id = uuid4().hex
    pages = await pdf_parser.parse_pdf(file_path, lecture_id)
    chunks_indexed = await vector_store.index_pages(pages, file_path)
    return IngestResult(
        lecture_id=lecture_id,
        pages_indexed=len(pages),
        chunks_indexed=chunks_indexed,
        source_path=file_path,
    )


@router.get("/status/{job_id}")
async def ingest_status(job_id: str) -> dict:
    # [V] TODO: return parse/embedding status
    return {"job_id": job_id, "status": "pending"}


@router.post("/from-path", response_model=IngestResult)
async def ingest_from_path(path: str) -> IngestResult:
    base_dir = Path(__file__).resolve().parents[3] / "test_lectures"
    target = (base_dir / path).resolve()
    if base_dir not in target.parents and target != base_dir:
        raise HTTPException(status_code=400, detail="Invalid path")
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    lecture_id = uuid4().hex
    pages = await pdf_parser.parse_pdf(str(target), lecture_id)
    chunks_indexed = await vector_store.index_pages(pages, str(target))
    return IngestResult(
        lecture_id=lecture_id,
        pages_indexed=len(pages),
        chunks_indexed=chunks_indexed,
        source_path=str(target),
    )
