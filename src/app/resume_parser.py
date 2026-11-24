"""Extract skills and years of experience from a resume. Owner: Sophak."""
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


_MAX_YEARS = 40  # anything larger is not a candidate's experience
# "N years" counts only when "experience" follows within a few words,
# e.g. "3 years of experience", "5+ yrs professional Python experience".
_YEARS_EXP = re.compile(
    r"(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)(?:\s+of)?(?:\s+[a-z+#/.-]+){0,3}?\s+experience\b"
)


def extract_years(text: str) -> float | None:
    """Largest stated years of experience, or None. Ignores unrelated numbers such as
    "a company with 50 years of history"."""
    vals = [float(v) for v in _YEARS_EXP.findall(text.lower()) if float(v) <= _MAX_YEARS]
    return max(vals) if vals else None
