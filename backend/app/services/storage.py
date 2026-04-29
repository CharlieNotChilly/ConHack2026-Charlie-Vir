import logging
import os
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from ..config import settings

logger = logging.getLogger(__name__)


async def save_upload(file: UploadFile) -> str:
    # [V] TODO: swap for object storage in production
    uploads_dir = Path(settings.uploads_dir)
    uploads_dir.mkdir(parents=True, exist_ok=True)

    filename = os.path.basename(file.filename or "upload.pdf")
    dest_name = f"{uuid4().hex}-{filename}"
    dest_path = uploads_dir / dest_name

    content = await file.read()
    dest_path.write_bytes(content)
    logger.info(
        "Upload saved",
        extra={"path": str(dest_path), "bytes": len(content), "upload_name": filename},
    )
    return str(dest_path)
