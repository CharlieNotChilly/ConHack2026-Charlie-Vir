import base64
import shutil
import subprocess
from pathlib import Path
from typing import Tuple


_PDFLATEX_PACKAGES = (
    "\\usepackage[utf8]{inputenc}",
    "\\usepackage[T1]{fontenc}",
    "\\usepackage{textcomp}",
)


def _ensure_pdflatex_packages(latex_source: str) -> str:
    if all(pkg in latex_source for pkg in _PDFLATEX_PACKAGES):
        return latex_source

    insert = "\n".join(_PDFLATEX_PACKAGES) + "\n"

    if "\\begin{document}" in latex_source:
        return latex_source.replace("\\begin{document}", f"{insert}\\begin{{document}}", 1)

    if "\\documentclass" in latex_source:
        parts = latex_source.split("\n", 1)
        if len(parts) == 2:
            return f"{parts[0]}\n{insert}{parts[1]}"

    return f"{insert}{latex_source}"


def _find_latex_engine() -> tuple[str | None, str]:
    for engine in ("xelatex", "lualatex", "pdflatex"):
        path = shutil.which(engine)
        if path:
            return path, engine
    return None, ""


def compile_latex_to_pdf(latex_source: str, work_dir: str) -> Tuple[bytes, str | None]:
    engine_path, engine_name = _find_latex_engine()
    if not engine_path:
        return b"", "LaTeX engine not found; install MacTeX or a compatible TeX distribution."

    if engine_name == "pdflatex":
        latex_source = _ensure_pdflatex_packages(latex_source)

    work_path = Path(work_dir)
    tex_path = work_path / "main.tex"
    tex_path.write_text(latex_source.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")

    try:
        subprocess.run(
            [
                engine_path,
                "-interaction=nonstopmode",
                "-halt-on-error",
                "-file-line-error",
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
        stderr_tail = (exc.stderr or "").splitlines()[-8:]
        stdout_tail = (exc.stdout or "").splitlines()[-8:]
        detail_lines = [line for line in (stderr_tail + stdout_tail) if line]
        detail = "\n".join(detail_lines[-10:]) or "LaTeX compilation failed."
        return b"", detail

    pdf_path = work_path / "main.pdf"
    if not pdf_path.exists():
        return b"", "LaTeX compilation did not produce a PDF."
    return pdf_path.read_bytes(), None


def pdf_bytes_to_base64(pdf_bytes: bytes) -> str:
    return base64.b64encode(pdf_bytes).decode("ascii")
