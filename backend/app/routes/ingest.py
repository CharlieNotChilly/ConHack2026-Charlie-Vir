import logging
import os
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, HTTPException, UploadFile

from ..models import IngestResult
from ..services import pdf_parser, storage, vector_store

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/upload", response_model=IngestResult)
async def upload_lecture(file: UploadFile) -> IngestResult:
    lecture_id = uuid4().hex
    job_id = lecture_id
    stage = "saving"
    file_path = ""

    try:
        file_path = await storage.save_upload(file)
        file_size = os.path.getsize(file_path)
        logger.info(
            "Saved upload",
            extra={"lecture_id": lecture_id, "file_path": file_path, "bytes": file_size},
        )
        stage = "parsing"
        pdf_parser.set_job_status(job_id, "parsing", source_path=file_path)
        logger.info(
            "Parsing PDF",
            extra={"lecture_id": lecture_id, "file_path": file_path},
        )
        pages = await pdf_parser.parse_pdf(file_path, lecture_id)
        logger.info(
            "Parsed PDF",
            extra={"lecture_id": lecture_id, "file_path": file_path, "page_count": len(pages)},
        )
        stage = "indexing"
        pdf_parser.set_job_status(job_id, "indexing", pages_parsed=len(pages))
        logger.info(
            "Indexing pages",
            extra={"lecture_id": lecture_id, "file_path": file_path, "page_count": len(pages)},
        )
        chunks_indexed = await vector_store.index_pages(pages, file_path)
        logger.info(
            "Indexed pages",
            extra={
                "lecture_id": lecture_id,
                "file_path": file_path,
                "page_count": len(pages),
                "chunk_count": chunks_indexed,
            },
        )
        pdf_parser.set_job_status(
            job_id,
            "completed",
            pages_parsed=len(pages),
            chunks_indexed=chunks_indexed,
        )
    except Exception as exc:
        pdf_parser.set_job_status(job_id, "error", error=str(exc))
        logger.exception(
            "Ingest failed",
            extra={"lecture_id": lecture_id, "file_path": file_path, "stage": stage},
        )
        raise HTTPException(
            status_code=500,
            detail=f"Ingest failed during {stage}: {exc}",
        ) from exc
    return IngestResult(
        lecture_id=lecture_id,
        pages_indexed=len(pages),
        chunks_indexed=chunks_indexed,
        source_path=file_path,
    )


@router.get("/status/{job_id}")
async def ingest_status(job_id: str) -> dict:
    return {"job_id": job_id, **pdf_parser.get_job_status(job_id)}


@router.post("/from-path", response_model=IngestResult)
async def ingest_from_path(path: str) -> IngestResult:
    base_dir = Path(__file__).resolve().parents[3] / "test_lectures"
    target = (base_dir / path).resolve()
    if base_dir not in target.parents and target != base_dir:
        raise HTTPException(status_code=400, detail="Invalid path")
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    lecture_id = uuid4().hex
    job_id = lecture_id
    stage = "parsing"
    pdf_parser.set_job_status(job_id, "parsing", source_path=str(target))
    try:
        pages = await pdf_parser.parse_pdf(str(target), lecture_id)
        stage = "indexing"
        pdf_parser.set_job_status(job_id, "indexing", pages_parsed=len(pages))
        chunks_indexed = await vector_store.index_pages(pages, str(target))
        pdf_parser.set_job_status(
            job_id,
            "completed",
            pages_parsed=len(pages),
            chunks_indexed=chunks_indexed,
        )
    except Exception as exc:
        pdf_parser.set_job_status(job_id, "error", error=str(exc))
        logger.exception(
            "Ingest from path failed",
            extra={"lecture_id": lecture_id, "file_path": str(target), "stage": stage},
        )
        raise HTTPException(
            status_code=500,
            detail=f"Ingest failed during {stage}: {exc}",
        ) from exc
    return IngestResult(
        lecture_id=lecture_id,
        pages_indexed=len(pages),
        chunks_indexed=chunks_indexed,
        source_path=str(target),
    )
