"""Contract between the data and model workstreams.

Skill columns are 1/0 for postings and NaN for LCA rows (LCA has no job description).
Stage 1 (wage range) trains on early_career rows (LCA Level I/II + postings entry/associate);
Stage 2 (skill uplift) uses all postings rows (source == "postings"), with wage_level as a feature.
"""
from src.config import SKILLS

BASE_COLUMNS = {
    "title": "string",        # raw job title
    "soc_code": "string",     # 2018 SOC, e.g. 15-1252
    "county_fips": "string",  # 5-digit; null if unmatched
    "metro": "string",        # OEWS area code; null if unmatched
    "state": "string",        # two-letter code
    "wage_level": "string",   # LCA: I/II; postings: entry/associate/mid-senior/unknown
    "early_career": "bool",   # True for LCA I/II and postings entry/associate
    "years_exp": "float",     # null if not stated
    "year": "int",            # LCA fiscal year or posting year
    "annual_wage": "float",   # USD per year
    "employer": "string",     # normalized; used for employer-held-out split
    "source": "string",       # "lca" or "postings"
    "split": "string",        # "train" (FY2025 LCA + postings) or "shift" (FY2026 LCA)
}
SKILL_COLUMNS = [f"skill_{s}" for s in SKILLS]
ALL_COLUMNS = list(BASE_COLUMNS) + SKILL_COLUMNS


def validate(df) -> None:
    missing = [c for c in ALL_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"train.parquet missing columns: {missing}")
    if (df["annual_wage"] <= 0).any():
        raise ValueError("annual_wage must be positive")
    if df["early_career"].isna().any() or df["early_career"].dtype != bool:
        raise ValueError("early_career must be a non-null bool")
    allowed = {"lca": {"I", "II"}, "postings": {"entry", "associate", "mid-senior", "unknown"}}
    for src, levels in allowed.items():
        bad = set(df.loc[df["source"] == src, "wage_level"]) - levels
        if bad:
            raise ValueError(f"unexpected wage_level for {src}: {sorted(bad)}")
    lca = df["source"] == "lca"
    if not df.loc[lca, "early_career"].all():
        raise ValueError("all LCA rows are Level I/II and must be early_career")
    post = df["source"] == "postings"
    expect = df.loc[post, "wage_level"].isin(["entry", "associate"])
    if (df.loc[post, "early_career"] != expect).any():
        raise ValueError("postings early_career must equal wage_level in {entry, associate}")
    lca_skills = df.loc[df["source"] == "lca", SKILL_COLUMNS]
    if lca_skills.notna().any().any():
        raise ValueError("LCA rows must have NaN skill columns")
