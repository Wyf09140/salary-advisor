"""Extract skills and years of experience from a resume. Owner: Pubudu."""
import io
import re
from src.config import SKILLS


def extract_text(file_bytes: bytes, filename: str) -> str:
    name = filename.lower()
    if name.endswith(".pdf"):
        from pypdf import PdfReader
        return "\n".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(file_bytes)).pages)
    if name.endswith(".docx"):
        import docx
        return "\n".join(p.text for p in docx.Document(io.BytesIO(file_bytes)).paragraphs)
    return file_bytes.decode("utf-8", errors="ignore")


def extract_skills(text: str) -> list[str]:
    t = text.lower()
    return [s for s, aliases in SKILLS.items()
            if any(re.search(rf"(?<![a-z]){re.escape(a)}(?![a-z])", t) for a in aliases)]


def extract_years(text: str) -> float | None:
    m = re.findall(r"(\d+(?:\.\d+)?)\+?\s*years?", text.lower())
    return max(map(float, m)) if m else None
