"""HTML building blocks for the floating-island UI. Owner: Sophak.

Pure functions that return HTML strings, so they can be unit-tested without Streamlit.
Styling lives in theme.py; class names here start with "sa-".
"""
from html import escape


_LABELS = {
    "sql": "SQL", "javascript": "JavaScript / TypeScript", "cpp": "C++", "go": "Go", "aws": "AWS",
    "gcp": "Google Cloud", "power_bi": "Power BI", "nlp": "NLP", "llm": "LLMs", "git": "Git",
}


def skill_label(skill: str) -> str:
    """Display name for a canonical skill key from config/skills.yaml."""
    return _LABELS.get(skill, skill.replace("_", " ").capitalize())


def money(x: float) -> str:
    return f"${x:,.0f}"


def short_money(x: float) -> str:
    return f"${x / 1000:,.0f}k" if x >= 1000 else money(x)


def verdict(current: float, r: dict) -> tuple[str, str]:
    """(headline, detail) describing where current pay sits against the predicted range."""
    gap = current - r["p50"]
    if current < r["p10"]:
        head = "Below the market range"
    elif current < r["p50"]:
        head = "In range, below typical"
    elif current <= r["p90"]:
        head = "At or above typical"
    else:
        head = "Above the market range"
    side = "below" if gap < 0 else "above"
    detail = f"{money(abs(gap))} {side} the typical (P50) pay" if abs(gap) >= 500 else "Right at the typical (P50) pay"
    return head, detail


def _pct(x: float, lo: float, hi: float) -> float:
    return min(max((x - lo) / (hi - lo) * 100, 0.0), 100.0)


def range_band(r: dict, current: float | None) -> str:
    """Horizontal P10-P90 band with a P50 tick, dashed BLS median line and a 'You' marker."""
    values = [r["p10"], r["p90"], r["bls_median"]] + ([current] if current else [])
    lo, hi = min(values), max(values)
    pad = (hi - lo) * 0.08 or hi * 0.1
    lo, hi = lo - pad, hi + pad
    p10, p50, p90, bls = (_pct(r[k], lo, hi) for k in ("p10", "p50", "p90", "bls_median"))

    you = ""
    if current:
        x = _pct(current, lo, hi)
        anchor = "left" if x < 12 else "right" if x > 88 else "center"
        you = (
            f'<div class="sa-you sa-you-{anchor}" style="left:{x:.2f}%">'
            f'<span class="sa-you-pill sa-num">You · {short_money(current)}</span>'
            f'<span class="sa-you-stem"></span><span class="sa-you-dot"></span></div>'
        )

    return f"""
<div class="sa-band-wrap">
  <div class="sa-track">
    <div class="sa-band" style="left:{p10:.2f}%;width:{p90 - p10:.2f}%"></div>
    <div class="sa-p50" style="left:{p50:.2f}%"></div>
    <div class="sa-bls" style="left:{bls:.2f}%"></div>
    {you}
  </div>
  <div class="sa-ticks sa-num">
    <div class="sa-tick" style="left:{p10:.2f}%"><b>{short_money(r['p10'])}</b><span>Low · P10</span></div>
    <div class="sa-tick sa-tick-mid" style="left:{p50:.2f}%"><b>{short_money(r['p50'])}</b><span>Typical · P50</span></div>
    <div class="sa-tick" style="left:{p90:.2f}%"><b>{short_money(r['p90'])}</b><span>High · P90</span></div>
  </div>
  <div class="sa-legend sa-num"><i class="sa-legend-bls"></i>BLS median for this occupation and area: {money(r['bls_median'])}</div>
</div>"""


def skills_island(recs: list[tuple[str, float]], n_skills: int, years: float | None) -> str:
    """Ranked bars of predicted P50 uplift for skills missing from the profile."""
    using = f"Based on {n_skills} skill{'s' if n_skills != 1 else ''}"
    using += f" and {years:g} years of experience" if years else ""
    head = '<p class="sa-eyebrow">Next steps</p><p class="sa-h">Skills linked to higher pay</p>'
    if not recs:
        return head + '<p class="sa-note">Your profile already lists every skill we track.</p>'
    top = max(d for _, d in recs) or 1
    rows = "".join(
        f'<div class="sa-rec"><span class="sa-rec-name">{escape(skill_label(s))}</span>'
        f'<span class="sa-rec-bar"><i style="width:{max(d / top, 0.04) * 100:.1f}%"></i></span>'
        f'<span class="sa-rec-val sa-num">+{money(d)}</span></div>'
        for s, d in recs
    )
    return (
        f'{head}<div class="sa-recs">{rows}</div>'
        f'<p class="sa-note">{using}. Change in predicted typical pay if the skill were added to your '
        "profile. These are associations in the data, not guaranteed raises.</p>"
    )


def range_island(title: str, location: str, r: dict, current: float | None) -> str:
    where = escape(f"{title.strip()} · {location.strip()}")
    if current:
        head, detail = verdict(current, r)
        status = f'<div class="sa-verdict"><b>{head}</b><span class="sa-num">{detail}</span></div>'
    else:
        status = '<div class="sa-verdict"><b>Add your salary</b><span>to see where you stand in this range</span></div>'
    return f"""
<p class="sa-eyebrow">Market range</p>
<div class="sa-hero">
  <div>
    <div class="sa-big sa-num">{money(r['p50'])}</div>
    <div class="sa-sub">typical yearly pay for <b>{where}</b></div>
  </div>
  {status}
</div>
{range_band(r, current)}"""
