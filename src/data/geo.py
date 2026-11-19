"""Location -> OEWS metro. Owner: Yifan.

- load_crosswalk(): county -> metro from BLS area_definitions_m2025.xlsx (used by the pipeline).
- city_to_metro() / location_to_metro(): "City, ST" -> metro at prediction time, using
  data/processed/city_metro.parquet (built by `make data` from LCA worksite city + county),
  then principal cities in OEWS area titles. Returns None when unknown: fall back to state.
"""
import re
from functools import lru_cache
import pandas as pd
from src.config import RAW, PROCESSED, SOURCES

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


def norm_city(name) -> str:
    s = str(name).lower().replace("saint ", "st ").replace("st. ", "st ").replace("ft. ", "fort ")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z ]", " ", s)).strip()


def parse_location(text) -> tuple[str | None, str | None]:
    """'San Jose, CA' / 'San Jose, CA 95112' -> ('san jose', 'CA'); a bare 'CA' -> (None, 'CA')."""
    t = str(text).strip()
    m = re.match(r"^(.*?),\s*([A-Za-z]{2})\b", t)
    if m:
        return (norm_city(m.group(1)) or None), m.group(2).upper()
    if re.fullmatch(r"[A-Za-z]{2}", t):
        return None, t.upper()
    return None, None


@lru_cache(maxsize=1)
def _city_tables() -> tuple[dict, dict]:
    lca = pd.read_parquet(PROCESSED / "city_metro.parquet")
    from_lca = dict(zip(zip(lca["city_norm"], lca["state"]), lca["metro"]))
    oews = pd.read_parquet(PROCESSED / "oews.parquet")[["AREA", "AREA_TITLE"]].drop_duplicates()
    principal = {}
    for area, title in oews.itertuples(index=False):
        if "nonmetropolitan" in title.lower():
            continue
        cities, _, states = title.rpartition(", ")
        for c in cities.split("-"):
            for st in states.split("-"):
                principal.setdefault((norm_city(c), st.strip()), area)
    return from_lca, principal


def city_to_metro(city, state) -> str | None:
    """OEWS metro area code for a city, or None if unknown (caller falls back to state)."""
    if not city or not state:
        return None
    key = (norm_city(city), str(state).strip().upper())
    from_lca, principal = _city_tables()
    return from_lca.get(key) or principal.get(key)


def location_to_metro(text) -> tuple[str | None, str | None]:
    """'San Jose, CA' -> (metro or None, state or None)."""
    city, state = parse_location(text)
    return city_to_metro(city, state), state


def _col(df: pd.DataFrame, *keys: str) -> str:
    for c in df.columns:
        lc = c.lower()
        if all(k in lc for k in keys):
            return c
    raise KeyError(f"no column containing {keys}; columns are {list(df.columns)}")


def _metro_col(df: pd.DataFrame) -> str:
    # May 2025 file names it "May 2025 Area Code" (covers metro and nonmetro areas); older files used "MSA code"
    try:
        return _col(df, "msa", "code")
    except KeyError:
        return _col(df, "area", "code")


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
        "metro": a[_metro_col(a)].str.strip().str.lstrip("0"),
    })
    return out.dropna(subset=["metro"]).drop_duplicates("county_fips")
