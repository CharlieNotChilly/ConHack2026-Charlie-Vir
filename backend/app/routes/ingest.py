from fastapi import APIRouter, UploadFile

from ..services import pdf_parser, storage

router = APIRouter()


@router.post("/upload")
async def upload_lecture(file: UploadFile) -> dict:
    # [V] TODO: stream upload to object storage, enqueue parse job
    file_path = await storage.save_upload(file)
    job_id = await pdf_parser.enqueue_parse(file_path)
    return {"job_id": job_id}


@router.get("/status/{job_id}")
async def ingest_status(job_id: str) -> dict:
    # [V] TODO: return parse/embedding status
    return {"job_id": job_id, "status": "pending"}
