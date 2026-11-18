"""County -> OEWS metro crosswalk from BLS area_definitions_m2025.xlsx. Owner: Yifan."""
import re
import pandas as pd
from src.config import RAW, SOURCES

STATE_FIPS = {
    "01": "AL", "02": "AK", "04": "AZ", "05": "AR", "06": "CA", "08": "CO", "09": "CT", "10": "DE",
    "11": "DC", "12": "FL", "13": "GA", "15": "HI", "16": "ID", "17": "IL", "18": "IN", "19": "IA",
    "20": "KS", "21": "KY", "22": "LA", "23": "ME", "24": "MD", "25": "MA", "26": "MI", "27": "MN",
    "28": "MS", "29": "MO", "30": "MT", "31": "NE", "32": "NV", "33": "NH", "34": "NJ", "35": "NM",
    "36": "NY", "37": "NC", "38": "ND", "39": "OH", "40": "OK", "41": "OR", "42": "PA", "44": "RI",
    "45": "SC", "46": "SD", "47": "TN", "48": "TX", "49": "UT", "50": "VT", "51": "VA", "53": "WA",
    "54": "WV", "55": "WI", "56": "WY", "72": "PR",
}
_SUFFIX = re.compile(r"\b(county|parish|borough|census area|municipality|city and|and borough)\b")


def norm_county(name) -> str:
    s = str(name).lower().replace("saint ", "st ").replace("st. ", "st ")
    s = _SUFFIX.sub(" ", s)
    return re.sub(r"[^a-z ]", "", re.sub(r"\s+", " ", s)).strip()


def _col(df: pd.DataFrame, *keys: str) -> str:
    for c in df.columns:
        lc = c.lower()
        if all(k in lc for k in keys):
            return c
    raise KeyError(f"no column containing {keys}; columns are {list(df.columns)}")


def load_crosswalk() -> pd.DataFrame:
    """One row per county: county_fips, state, county_norm, metro."""
    a = pd.read_excel(RAW / SOURCES["oews"]["area_definitions_file"], dtype=str)
    a.columns = [str(c).strip() for c in a.columns]
    st_fips = a[_col(a, "fips")].str.zfill(2)
    cty = a[_col(a, "county", "code")].str.zfill(3)
    out = pd.DataFrame({
        "county_fips": st_fips + cty,
        "state": st_fips.map(STATE_FIPS),
        "county_norm": a[_col(a, "county", "name")].map(norm_county),
        "metro": a[_col(a, "msa", "code")].str.strip().str.lstrip("0"),
    })
    return out.dropna(subset=["metro"]).drop_duplicates("county_fips")
