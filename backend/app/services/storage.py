from fastapi import UploadFile


async def save_upload(file: UploadFile) -> str:
    # [V] TODO: store upload in object storage and return path
    return "/tmp/placeholder.pdf"
