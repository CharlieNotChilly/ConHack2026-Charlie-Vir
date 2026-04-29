import os
from pathlib import Path

from fastapi import UploadFile

from ..config import settings


async def save_upload(file: UploadFile) -> str:
    # [V] TODO: swap for object storage in production
    uploads_dir = Path(settings.uploads_dir)
    uploads_dir.mkdir(parents=True, exist_ok=True)

    filename = os.path.basename(file.filename or "upload.pdf")
    dest_path = uploads_dir / filename

    content = await file.read()
    dest_path.write_bytes(content)
    return str(dest_path)
