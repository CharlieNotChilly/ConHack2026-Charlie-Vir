import logging
from typing import Dict, List, Optional

import requests

from ..config import settings
from ..models import AidSheetDraft, AidSheetRequest, RetrievalCandidate

logger = logging.getLogger(__name__)

_GEMINI_MODELS = ["gemini-2.5-flash-lite", "gemini-2.5-flash", "gemini-3-flash-preview"]


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


def _deduplicate(candidates: List[RetrievalCandidate]) -> List[RetrievalCandidate]:
    seen: set = set()
    out: List[RetrievalCandidate] = []
    for c in candidates:
        key = " ".join(c.content.split())[:180]
        if key not in seen:
            seen.add(key)
            out.append(c)
    return out


def _call_gemini(prompt: str) -> Optional[str]:
    if not settings.gemini_api_key:
        return None
    for model in _GEMINI_MODELS:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:generateContent?key={settings.gemini_api_key}"
        )
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 8192},
        }
        try:
            resp = requests.post(url, json=payload, timeout=90)
            if resp.ok:
                text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
                logger.info("Gemini generation succeeded", extra={"model": model})
                return text
            logger.warning("Gemini model failed", extra={"model": model, "status": resp.status_code})
        except Exception:
            logger.exception("Gemini call error", extra={"model": model})
    return None


def _extract_latex(raw: str) -> str:
    """Strip markdown fences if Gemini wraps the output."""
    if "```latex" in raw:
        return raw.split("```latex", 1)[1].split("```", 1)[0].strip()
    if "```" in raw:
        return raw.split("```", 1)[1].split("```", 1)[0].strip()
    return raw.strip()


def _ensure_graphicx(latex_source: str) -> str:
    if "\\usepackage{graphicx}" in latex_source:
        return latex_source

    insert = "\\usepackage{graphicx}\n"
    if "\\begin{document}" in latex_source:
        return latex_source.replace("\\begin{document}", f"{insert}\\begin{{document}}", 1)

    if "\\documentclass" in latex_source:
        parts = latex_source.split("\n", 1)
        if len(parts) == 2:
            return f"{parts[0]}\n{insert}{parts[1]}"

    return f"{insert}{latex_source}"


def append_images(
    latex_source: str,
    image_entries: List[Dict[str, object]],
) -> str:
    if not image_entries:
        return latex_source

    latex_source = _ensure_graphicx(latex_source)

    blocks = ["\\section*{Relevant Images}", "\\vspace{0.4em}"]
    for entry in image_entries:
        path = str(entry.get("path") or "")
        if not path:
            continue
        safe = path.replace("\\", "/")
        blocks += [
            "\\begin{center}",
            f"\\includegraphics[width=0.9\\linewidth]{{{safe}}}",
            "\\end{center}",
            "\\vspace{0.6em}",
        ]
    block = "\n".join(blocks)
    if "\\end{document}" in latex_source:
        return latex_source.replace("\\end{document}", f"{block}\n\\end{{document}}", 1)
    return f"{latex_source}\n{block}"


async def build_draft(
    request: AidSheetRequest, candidates: List[RetrievalCandidate]
) -> AidSheetDraft:
    candidates = _deduplicate(candidates)

    if candidates and settings.gemini_api_key:
        context = "\n\n---\n\n".join(
            f"[Page {c.metadata.get('page_number', '?')}]\n{c.content.strip()}"
            for c in candidates[:20]
        )

        prompt = f"""You are generating a LaTeX aid/cheat sheet for the course **{request.course_id}**.

User instructions: {request.instructions or "Summarize the most important concepts, definitions, and formulas."}
Target length: {request.target_pages} page(s), two-column layout, 10pt font, 0.5in margins.

Retrieved course content (use this as your source material):
{context}

Rules:
- Output ONLY a complete, compilable LaTeX document. No explanations, no markdown outside the document.
- Use \\documentclass[10pt]{{article}} with \\usepackage[margin=0.5in]{{geometry}}, \\usepackage{{multicol}}, \\usepackage{{amsmath,amssymb}}.
- Wrap all body content in \\begin{{multicols}}{{2}} ... \\end{{multicols}}.
- Use \\section* for topic headers and \\subsection* for subtopics.
- Preserve ALL mathematical formulas in proper LaTeX math mode ($...$ or \\[...\\]).
- Keep bullet points short and dense — this is a reference sheet, not an essay.
- Do NOT include problem lists, recommended readings, or administrative course info.
- Do NOT repeat the same content. Merge duplicates.
- Fill the requested page count with meaningful content.
"""

        raw = _call_gemini(prompt)
        if raw:
            latex = _extract_latex(raw)
            if "\\documentclass" in latex:
                return AidSheetDraft(latex_source=latex)
            logger.warning("Gemini output did not contain \\documentclass, falling back")

    # Fallback: template-based bullet list
    title = _escape_latex(request.course_id)
    bullets = []
    for c in candidates[:12]:
        text = c.content.strip()
        if text:
            bullets.append(f"\\item {_escape_latex(text[:240])}")
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

\\begin{{multicols}}{{2}}
\\begin{{itemize}}
{bullet_block}
\\end{{itemize}}
\\end{{multicols}}
\\end{{document}}
"""
    return AidSheetDraft(latex_source=latex, warnings=["Gemini unavailable; showing raw chunks."])
