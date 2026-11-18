"""Models -> App interface. Owner: Pubudu.

STUB: returns fixed, plausible numbers so the app and tests run before models are trained.
Replace the bodies once train.py saves models/quantile_models.pkl; keep the signatures and
return shapes unchanged (see README.md "Interface contracts" and tests/test_interfaces.py).
"""
from src.config import SKILLS

_STUB_P50 = 120_000.0


def predict(title: str, location: str, skills: list[str], years_exp: float | None) -> dict:
    """Return {"p10", "p50", "p90", "bls_median"} in USD/year, with p10 <= p50 <= p90."""
    p50 = _STUB_P50
    return {"p10": 0.75 * p50, "p50": p50, "p90": 1.40 * p50, "bls_median": p50}


def recommend(profile: dict, top_k: int = 5) -> list[tuple[str, float]]:
    """Return up to top_k (skill, delta_p50_usd) for skills missing from profile["skills"],
    largest predicted P50 uplift first. Associations, not causal effects."""
    have = {s.lower() for s in profile.get("skills", [])}
    missing = [s for s in SKILLS if s not in have]
    return [(s, 5_000.0 - 500.0 * i) for i, s in enumerate(missing[:top_k])]
