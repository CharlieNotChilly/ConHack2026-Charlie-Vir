from typing import List

from ..models import PageRecord


async def enqueue_parse(file_path: str) -> str:
    # [V] TODO: push job to queue
    return "job-placeholder"


async def parse_pdf(file_path: str) -> List[PageRecord]:
    # [V] TODO: extract text, images, and layout per page
    return []
