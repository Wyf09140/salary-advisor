"""Clean and join sources into data/processed/train.parquet. Owner: Yifan.

Also writes data/processed/data_report.md with row counts at every filter step
(reusable in the report's Dataset section).
"""
import re
import zipfile
import numpy as np
import pandas as pd
from src.config import RAW, PROCESSED, SOURCES, SOC_CODES, SKILLS
from src.data.geo import load_crosswalk, norm_county
from src.data.schema import ALL_COLUMNS, SKILL_COLUMNS, validate
from src.data.titles import load_onet_titles, match_titles

ANNUAL = {"YEAR": 1, "HOUR": 2080, "WEEK": 52, "BI-WEEKLY": 26, "MONTH": 12,
          "YEARLY": 1, "HOURLY": 2080, "WEEKLY": 52, "BIWEEKLY": 26, "MONTHLY": 12}
_CORP = re.compile(r"\b(INC|LLC|L L C|CORP|CORPORATION|CO|COMPANY|LTD|LP|LLP|PLLC|PC|USA|US|THE)\b")
_YEARS = re.compile(r"(\d{1,2})\s*\+?\s*(?:(?:-|–|to)\s*\d{1,2}\s*)?years?\s+(?:of\s+)?"
                    r"(?:\w+\s+){0,3}experience", re.I)

POSTING_LEVELS = {"Entry level": "entry", "Associate": "associate", "Mid-Senior level": "mid-senior"}

REPORT: list[str] = []


def log(step: str, n: int) -> None:
    REPORT.append(f"| {step} | {n:,} |")
    print(f"{step:<60} {n:>10,}")


def to_annual(amount, unit) -> pd.Series:
    return pd.to_numeric(amount, errors="coerce") * pd.Series(unit).astype(str).str.upper().map(ANNUAL).values


def norm_employer(s: pd.Series) -> pd.Series:
    s = s.astype(str).str.upper().str.replace(r"[^A-Z0-9 ]", " ", regex=True)
    return s.str.replace(_CORP, " ", regex=True).str.replace(r"\s+", " ", regex=True).str.strip()


def tag_skills(text: pd.Series) -> pd.DataFrame:
    text = text.fillna("").str.lower()
    out = {}
    for skill, aliases in SKILLS.items():
        pattern = "|".join(rf"(?<![a-z]){re.escape(a)}(?![a-z])" for a in aliases)
        out[f"skill_{skill}"] = text.str.contains(pattern, regex=True).astype(float)
    return pd.DataFrame(out, index=text.index)


def extract_years(text: pd.Series) -> pd.Series:
    return text.fillna("").str.extract(_YEARS)[0].astype(float)


# ---------- OEWS ----------
def load_oews() -> pd.DataFrame:
    # The zip holds MSA_M2025_dl.xlsx (metros), BOS_M2025_dl.xlsx (nonmetro areas) and file_descriptions.xlsx
    with zipfile.ZipFile(RAW / SOURCES["oews"]["file"]) as z:
        names = [n for n in z.namelist() if n.lower().endswith("_dl.xlsx")]
        if not names:
            raise FileNotFoundError(f"no *_dl.xlsx data file in {z.namelist()}")
        df = pd.concat([pd.read_excel(z.open(n), dtype=str) for n in names], ignore_index=True)
    df.columns = df.columns.str.upper()
    df = df[df["OCC_CODE"].isin(SOC_CODES)].copy()
    # Flag only literal '#' markers: May 2025 publishes real P90 values above the cap without '#'
    topcoded = df["A_PCT90"].astype(str).str.strip() == "#"
    REPORT.append(f"\nOEWS rows with top-coded annual P90 ('#'): {int(topcoded.sum())}\n")
    cap = SOURCES["oews_topcode_annual"]
    for c in ["A_PCT10", "A_MEDIAN", "A_PCT90"]:
        df[c] = pd.to_numeric(df[c].str.strip().replace("#", cap), errors="coerce")  # '*' = not available
    df["P90_TOPCODED"] = topcoded
    df["AREA"] = df["AREA"].str.strip().str.lstrip("0")
    return df[["AREA", "AREA_TITLE", "PRIM_STATE", "OCC_CODE", "A_PCT10", "A_MEDIAN", "A_PCT90", "P90_TOPCODED"]]


# ---------- LCA ----------
def load_lca_file(path, split: str) -> pd.DataFrame:
    df = pd.read_excel(path, dtype=str)
    df.columns = df.columns.str.upper()
    fy = int(re.search(r"FY(\d{4})", path.name).group(1))
    log(f"LCA {path.name}: raw", len(df))
    keep = (df["CASE_STATUS"].str.strip().str.lower() == "certified")
    if "VISA_CLASS" in df:
        keep &= df["VISA_CLASS"].str.strip() == "H-1B"
    if "FULL_TIME_POSITION" in df:
        keep &= df["FULL_TIME_POSITION"].str.strip() == "Y"
    df = df[keep].copy()
    df["SOC7"] = df["SOC_CODE"].astype(str).str.strip().str[:7]
    df = df[df["SOC7"].isin(SOC_CODES)]
    log(f"  certified H-1B full-time, tech SOC", len(df))
    df = df[df["PW_WAGE_LEVEL"].astype(str).str.strip().isin(SOURCES["lca"]["wage_levels"])]
    log(f"  wage level {'/'.join(SOURCES['lca']['wage_levels'])}", len(df))
    return pd.DataFrame({
        "title": df["JOB_TITLE"],
        "soc_code": df["SOC7"],
        "state": df["WORKSITE_STATE"].str.strip().str.upper(),
        "county_norm": df.get("WORKSITE_COUNTY", pd.Series(index=df.index, dtype=str)).map(norm_county),
        "wage_level": df["PW_WAGE_LEVEL"].str.strip(),
        "early_career": True,  # filtered to PW_WAGE_LEVEL I/II above
        "years_exp": np.nan,
        "year": fy,
        "annual_wage": to_annual(df["WAGE_RATE_OF_PAY_FROM"], df["WAGE_UNIT_OF_PAY"]),
        "employer": norm_employer(df["EMPLOYER_NAME"]),
        "source": "lca",
        "split": split,
    })


def load_lca(xwalk: pd.DataFrame) -> pd.DataFrame:
    frames = []
    for key, split in (("train_urls", "train"), ("shift_urls", "shift")):
        for url in SOURCES["lca"][key]:
            path = RAW / url.rsplit("/", 1)[-1]
            if path.exists():
                frames.append(load_lca_file(path, split))
            else:
                print(f"missing {path.name}, skipped")
    df = pd.concat(frames, ignore_index=True)
    m = xwalk[["state", "county_norm", "county_fips", "metro"]].drop_duplicates(["state", "county_norm"])
    df = df.merge(m, on=["state", "county_norm"], how="left").drop(columns="county_norm")
    log("LCA total, metro matched", int(df["metro"].notna().sum()))
    for c in SKILL_COLUMNS:
        df[c] = np.nan  # no job description in LCA
    return df


# ---------- Postings ----------
def load_postings(xwalk: pd.DataFrame, onet: pd.DataFrame) -> pd.DataFrame:
    p = pd.read_csv(RAW / "linkedin" / "postings.csv")
    log("Postings: raw", len(p))
    p = p[p["normalized_salary"].notna()]
    if "currency" in p:
        p = p[p["currency"].fillna("USD") == "USD"]
    if "compensation_type" in p:
        p = p[p["compensation_type"].fillna("BASE_SALARY") == "BASE_SALARY"]
    if "work_type" in p:
        p = p[p["work_type"].fillna("FULL_TIME") == "FULL_TIME"]
    log("  salary present, USD, base, full-time", len(p))
    k = SOURCES["kaggle"]
    p = p[~p["formatted_experience_level"].isin(k["exclude_levels"])]
    log(f"  experience level not in {k['exclude_levels']}", len(p))

    soc, score = match_titles(p["title"], onet, SOURCES["title_match_min_score"])
    p = p.assign(soc_code=soc.values, match_score=score.values)
    p = p[p["soc_code"].isin(SOC_CODES)].copy()
    log("  title matched to tech SOC", len(p))

    p["county_fips"] = pd.to_numeric(p["fips"], errors="coerce").astype("Int64").astype(str).str.zfill(5)
    p.loc[p["county_fips"].str.contains("NA"), "county_fips"] = pd.NA
    p = p.merge(xwalk[["county_fips", "state", "metro"]], on="county_fips", how="left")
    loc_state = p["location"].astype(str).str.extract(r",\s*([A-Z]{2})\b")[0]
    p["state"] = p["state"].fillna(loc_state)
    log("  metro matched", int(p["metro"].notna().sum()))

    desc = p["title"].astype(str) + " " + p["description"].fillna("")
    out = pd.DataFrame({
        "title": p["title"],
        "soc_code": p["soc_code"],
        "county_fips": p["county_fips"],
        "metro": p["metro"],
        "state": p["state"],
        "wage_level": p["formatted_experience_level"].map(POSTING_LEVELS).fillna("unknown"),
        "early_career": p["formatted_experience_level"].isin(k["early_career_levels"]),
        "years_exp": extract_years(p["description"]),
        "year": pd.to_datetime(p["listed_time"], unit="ms", errors="coerce").dt.year,
        "annual_wage": p["normalized_salary"],
        "employer": norm_employer(p["company_name"]),
        "source": "postings",
        "split": "train",
    })
    return pd.concat([out, tag_skills(desc)], axis=1)


def main() -> None:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    REPORT.extend(["# Data report", "", "| Step | Rows |", "| --- | --- |"])
    oews = load_oews()
    oews.to_parquet(PROCESSED / "oews.parquet", index=False)
    xwalk = load_crosswalk()
    onet = load_onet_titles()

    df = pd.concat([load_lca(xwalk), load_postings(xwalk, onet)], ignore_index=True)
    lo, hi = SOURCES["min_annual_wage"], SOURCES["max_annual_wage"]
    df = df[df["annual_wage"].between(lo, hi)].dropna(subset=["title", "state"])
    df = df[df["employer"].str.len() > 0]
    log("Final rows (wage in range, state known)", len(df))
    log("  of which early_career", int(df["early_career"].sum()))

    df = df[ALL_COLUMNS]
    validate(df)
    df.to_parquet(PROCESSED / "train.parquet", index=False)

    summary = df.groupby(["source", "split", "early_career", "soc_code"]).size().unstack(fill_value=0)
    REPORT.extend(["", "## Rows by source, split, early_career and SOC", "", summary.to_markdown()])
    (PROCESSED / "data_report.md").write_text("\n".join(REPORT))
    print(summary)


if __name__ == "__main__":
    main()
