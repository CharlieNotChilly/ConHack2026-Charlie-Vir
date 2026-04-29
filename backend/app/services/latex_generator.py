from typing import List

from ..models import AidSheetDraft, AidSheetRequest, RetrievalCandidate


def _escape_latex(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    for src, dest in replacements.items():
        text = text.replace(src, dest)
    return text


def append_images(latex_source: str, image_paths: List[str]) -> str:
    if not image_paths:
        return latex_source

    blocks = [
        "\\section*{Figures}",
        "\\vspace{0.4em}",
    ]
    for path in image_paths:
        safe_path = path.replace("\\", "/")
        blocks.append("\\begin{center}")
        blocks.append(f"\\includegraphics[width=0.9\\linewidth]{{{safe_path}}}")
        blocks.append("\\end{center}")
        blocks.append("\\vspace{0.6em}")
    block = "\n".join(blocks)

    marker = "\\end{document}"
    if marker in latex_source:
        return latex_source.replace(marker, f"{block}\n{marker}", 1)
    return f"{latex_source}\n{block}"


async def build_draft(
    request: AidSheetRequest, candidates: List[RetrievalCandidate]
) -> AidSheetDraft:
    title = _escape_latex(request.course_id)
    instructions = _escape_latex(request.instructions or "")
    bullets = []
    for candidate in candidates[:12]:
        content = candidate.content.strip()
        if content:
            bullets.append(f"\\item { _escape_latex(content[:240]) }")

    bullet_block = "\n".join(bullets) if bullets else "\\item TODO: Add content"

    latex = f"""\\documentclass[10pt]{{article}}
\\usepackage[margin=0.5in]{{geometry}}
\\usepackage{{multicol}}
\\usepackage{{amsmath,amssymb}}
\\usepackage{{graphicx}}
\\setlength{{\\parindent}}{{0pt}}

\\begin{{document}}
\\begin{{center}}\\textbf{{{title}}}\\end{{center}}
\\vspace{{0.2em}}

\\textbf{{Instructions:}} {instructions}

\\begin{{multicols}}{{2}}
\\begin{{itemize}}
{bullet_block}
\\end{{itemize}}
\\end{{multicols}}
\\end{{document}}
"""

    return AidSheetDraft(latex_source=latex)
