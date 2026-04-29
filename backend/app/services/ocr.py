from typing import List

from ..models import FormulaBlock


async def extract_formulas(image_bytes: bytes) -> List[FormulaBlock]:
    # [V] TODO: run pix2tex or other OCR and return LaTeX
    return []
