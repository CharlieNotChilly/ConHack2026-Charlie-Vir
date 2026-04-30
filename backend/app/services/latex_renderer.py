import base64
import shutil
import subprocess
from pathlib import Path
from typing import Tuple


def compile_latex_to_pdf(latex_source: str, work_dir: str) -> Tuple[bytes, str | None]:
    pdflatex = shutil.which("pdflatex")
    if not pdflatex:
        return b"", "pdflatex not found; install a LaTeX engine to enable preview."

    work_path = Path(work_dir)
    tex_path = work_path / "main.tex"
    tex_path.write_text(latex_source, encoding="utf-8")

    try:
        subprocess.run(
            [
                pdflatex,
                "-interaction=nonstopmode",
                "-halt-on-error",
                "-output-directory",
                str(work_path),
                str(tex_path),
            ],
            cwd=str(work_path),
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        stderr_tail = (exc.stderr or "").splitlines()[-6:]
        detail = "\n".join(stderr_tail) or "LaTeX compilation failed."
        return b"", detail

    pdf_path = work_path / "main.pdf"
    if not pdf_path.exists():
        return b"", "LaTeX compilation did not produce a PDF."
    return pdf_path.read_bytes(), None


def pdf_bytes_to_base64(pdf_bytes: bytes) -> str:
    return base64.b64encode(pdf_bytes).decode("ascii")
