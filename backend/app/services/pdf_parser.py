import os
from typing import List

import fitz

from ..models import PageRecord


async def enqueue_parse(file_path: str) -> str:
    # [V] TODO: push job to queue
    return os.path.basename(file_path)


async def parse_pdf(file_path: str, lecture_id: str) -> List[PageRecord]:
    pages: List[PageRecord] = []
    with fitz.open(file_path) as doc:
        for page_number, page in enumerate(doc, start=1):
            text = page.get_text("text")
            rect = page.rect
            pages.append(
                PageRecord(
                    lecture_id=lecture_id,
                    page_number=page_number,
                    text=text,
                    width=int(rect.width),
                    height=int(rect.height),
                )
            )
    return pages
