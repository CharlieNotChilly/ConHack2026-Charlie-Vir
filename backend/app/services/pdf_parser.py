import asyncio
import logging
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures.process import BrokenProcessPool
from datetime import datetime
from uuid import uuid4
from typing import List

from ..models import PageRecord

logger = logging.getLogger(__name__)

_PROCESS_POOL: ProcessPoolExecutor | None = None


def _get_process_pool() -> ProcessPoolExecutor:
    global _PROCESS_POOL
    if _PROCESS_POOL is None:
        _PROCESS_POOL = ProcessPoolExecutor(max_workers=1)
    return _PROCESS_POOL

JOB_STATUS: dict = {}


def set_job_status(job_id: str, status: str, **updates) -> None:
    payload = JOB_STATUS.get(job_id, {})
    payload.update(updates)
    payload["status"] = status
    payload["updated_at"] = datetime.utcnow().isoformat() + "Z"
    JOB_STATUS[job_id] = payload


def get_job_status(job_id: str) -> dict:
    return JOB_STATUS.get(job_id, {"status": "unknown"})


async def enqueue_parse(file_path: str) -> str:
    job_id = uuid4().hex
    set_job_status(job_id, "pending", source_path=file_path)
    return job_id


def _parse_pdf_sync(file_path: str, lecture_id: str) -> List[dict]:
    import fitz

    pages: List[dict] = []
    with fitz.open(file_path) as doc:
        for page_number, page in enumerate(doc, start=1):
            text = page.get_text("text")
            rect = page.rect
            pages.append(
                {
                    "lecture_id": lecture_id,
                    "page_number": page_number,
                    "text": text,
                    "width": int(rect.width),
                    "height": int(rect.height),
                }
            )
    return pages


async def parse_pdf(file_path: str, lecture_id: str) -> List[PageRecord]:
    loop = asyncio.get_running_loop()
    try:
        logger.info(
            "PDF parse start",
            extra={"file_path": file_path, "lecture_id": lecture_id},
        )
        raw_pages = await loop.run_in_executor(
            _get_process_pool(),
            _parse_pdf_sync,
            file_path,
            lecture_id,
        )
    except BrokenProcessPool as exc:
        logger.exception("PDF parse worker crashed", extra={"file_path": file_path})
        raise RuntimeError("PDF parser crashed; file may be malformed") from exc
    except Exception:
        logger.exception("PDF parse failed", extra={"file_path": file_path})
        raise

    logger.info(
        "PDF parse complete",
        extra={"file_path": file_path, "lecture_id": lecture_id, "page_count": len(raw_pages)},
    )
    return [PageRecord(**page) for page in raw_pages]
