from pathlib import Path
from typing import List

import fitz

from ..models import RetrievalCandidate


def materialize_images(
    candidates: List[RetrievalCandidate], work_dir: str
) -> List[str]:
    image_paths: List[str] = []
    docs: dict[str, fitz.Document] = {}

    try:
        for idx, candidate in enumerate(candidates):
            if candidate.type != "image":
                continue
            meta = candidate.metadata or {}
            source_path = meta.get("source_path")
            xref = meta.get("image_xref")
            if not source_path or xref is None:
                continue
            doc = docs.get(source_path)
            if doc is None:
                doc = fitz.open(source_path)
                docs[source_path] = doc
            base = doc.extract_image(int(xref))
            image_bytes = base.get("image")
            if not image_bytes:
                continue
            ext = (base.get("ext") or "png").lower()
            if ext == "jpg":
                ext = "jpeg"
            filename = f"image-{idx}.{ext}"
            path = Path(work_dir) / filename
            path.write_bytes(image_bytes)
            image_paths.append(str(path))
    finally:
        for doc in docs.values():
            doc.close()

    return image_paths
