from io import BytesIO
from typing import List, Optional

from PIL import Image

from ..models import FormulaBlock

_OCR_MODEL: Optional[object] = None


def _load_pix2tex():
    global _OCR_MODEL
    if _OCR_MODEL is not None:
        return _OCR_MODEL
    try:
        from pix2tex.cli import LatexOCR
    except Exception:
        return None
    _OCR_MODEL = LatexOCR()
    return _OCR_MODEL


async def extract_formulas(image_bytes: bytes) -> List[FormulaBlock]:
    model = _load_pix2tex()
    if model is None:
        return []
    image = Image.open(BytesIO(image_bytes)).convert("RGB")
    latex = model(image)
    if not latex:
        return []
    return [FormulaBlock(latex=latex)]
