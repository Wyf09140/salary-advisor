"""Feature builders for the Stage 1 wage-range models. Owner: Pubudu.

Rule: a feature is allowed only if predict(title, location, skills, years_exp) can compute it.
  - soc_code   <- TitleMatcher(title)            (src/data/titles.py)
  - metro/state <- location_to_metro(location)   (src/data/geo.py)
  - OEWS P10/P50/P90 for (metro, soc), falling back to state then national, exactly as the baseline.
NOT allowed: wage_level (derived from OEWS prevailing-wage levels and unknown at predict time),
source, employer, year.

Linear features (QuantReg):
  log_bls_p50    log of the OEWS median for the row's occupation and area
  log_bls_spread log(P90) - log(P10): how wide the local wage distribution is
  metro_missing  1 if the metro was unknown and the state/national fallback was used
  soc_*          one-hot occupation, reference = 15-1252 (Software Developers, the largest group)
"""
import numpy as np
import pandas as pd

from src.config import SOC_CODES

REFERENCE_SOC = "15-1252"
SOC_DUMMIES = [f"soc_{s}" for s in sorted(SOC_CODES) if s != REFERENCE_SOC]
LINEAR_COLUMNS = ["const", "log_bls_p50", "log_bls_spread", "metro_missing", *SOC_DUMMIES]


def bls_quantiles(df: pd.DataFrame, oews: pd.DataFrame) -> pd.DataFrame:
    """OEWS P10/P50/P90 per row, same lookup and fallbacks as the baseline."""
    from src.data.baseline import baseline_predictions
    return baseline_predictions(df, oews)


def linear_features(df: pd.DataFrame, bls: pd.DataFrame) -> pd.DataFrame:
    """Design matrix with a fixed column order (LINEAR_COLUMNS), indexed like df.

    Rows whose SOC is outside the project's SOC list get all soc_* = 0, i.e. treated as the
    reference occupation; rows with no OEWS value at all come out NaN and must be dropped.
    """
    X = pd.DataFrame(index=df.index)
    X["const"] = 1.0
    X["log_bls_p50"] = np.log(bls["p50"])
    X["log_bls_spread"] = np.log(bls["p90"]) - np.log(bls["p10"])
    X["metro_missing"] = df["metro"].isna().astype(float)
    soc = df["soc_code"].astype("string")
    for col in SOC_DUMMIES:
        X[col] = (soc == col.removeprefix("soc_")).astype(float).fillna(0.0)
    return X[LINEAR_COLUMNS]
