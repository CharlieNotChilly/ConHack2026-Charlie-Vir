import hashlib
from pathlib import Path
from typing import Dict, List

import fitz

from ..models import RetrievalCandidate


def materialize_images(
    candidates: List[RetrievalCandidate], work_dir: str
) -> List[Dict[str, object]]:
    image_entries: List[Dict[str, object]] = []
    docs: dict[str, fitz.Document] = {}
    supported_exts = {"png", "jpg", "jpeg", "pdf"}
    seen: set[tuple[str, int]] = set()
    seen_hashes: set[str] = set()

    try:
        for idx, candidate in enumerate(candidates):
            if candidate.type != "image":
                continue
            meta = candidate.metadata or {}
            source_path = meta.get("source_path")
            xref = meta.get("image_xref")
            if not source_path or xref is None:
                continue
            key = (str(source_path), int(xref))
            if key in seen:
                continue
            seen.add(key)

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
            if ext not in supported_exts:
                # Rasterize unsupported formats (e.g., jp2/jpx/jbig2) to PNG for pdflatex.
                pix = fitz.Pixmap(doc, int(xref))
                if pix.n - pix.alpha > 3:
                    pix = fitz.Pixmap(fitz.csRGB, pix)
                image_bytes = pix.tobytes("png")
                image_hash = hashlib.sha256(image_bytes).hexdigest()
                if image_hash in seen_hashes:
                    pix = None
                    continue
                filename = f"image-{len(image_entries)}.png"
                path = Path(work_dir) / filename
                path.write_bytes(image_bytes)
                pix = None
            else:
                image_hash = hashlib.sha256(image_bytes).hexdigest()
                if image_hash in seen_hashes:
                    continue
                filename = f"image-{len(image_entries)}.{ext}"
                path = Path(work_dir) / filename
                path.write_bytes(image_bytes)
            seen_hashes.add(image_hash)
            image_entries.append(
                {
                    "path": str(Path(filename)),
                    "page_number": meta.get("page_number"),
                    "source_path": source_path,
                    "image_xref": int(xref),
                }
            )
    finally:
        for doc in docs.values():
            doc.close()

    return image_entries
