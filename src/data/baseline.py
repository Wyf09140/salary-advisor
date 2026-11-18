"""BLS-median baseline: OEWS median for the row's occupation and area. Owner: Yifan."""
import numpy as np
import pandas as pd
from src.config import PROCESSED


def baseline_predictions(df: pd.DataFrame, oews: pd.DataFrame) -> pd.DataFrame:
    """Metro P10/P50/P90, falling back to state median of metros, then national median."""
    cols = ["A_PCT10", "A_MEDIAN", "A_PCT90"]
    by_metro = oews.set_index(["AREA", "OCC_CODE"])[cols]
    by_metro = by_metro[~by_metro.index.duplicated()]
    by_state = oews.groupby(["PRIM_STATE", "OCC_CODE"])[cols].median()
    by_occ = oews.groupby("OCC_CODE")[cols].median()
    a = df.join(by_metro, on=["metro", "soc_code"])
    b = df.join(by_state, on=["state", "soc_code"])
    c = df.join(by_occ, on="soc_code")
    out = a[cols].fillna(b[cols]).fillna(c[cols])
    out.columns = ["p10", "p50", "p90"]
    return out


def _metrics():
    """Use the model workstream's metrics when present; until src/models/ lands, a local copy
    matching the contract in tests/test_interfaces.py::test_metrics."""
    try:
        from src.models.evaluate import mae_log, pinball, coverage
    except ModuleNotFoundError:
        def mae_log(y, p):
            return float(np.mean(np.abs(np.log(np.asarray(y, float)) - np.log(np.asarray(p, float)))))

        def pinball(y, q, tau):
            d = np.asarray(y, float) - np.asarray(q, float)
            return float(np.mean(np.maximum(tau * d, (tau - 1) * d)))

        def coverage(y, lo, hi):
            y = np.asarray(y, float)
            return float(np.mean((y >= np.asarray(lo, float)) & (y <= np.asarray(hi, float))))
    return mae_log, pinball, coverage


def main() -> None:
    mae_log, pinball, coverage = _metrics()
    df = pd.read_parquet(PROCESSED / "train.parquet")
    oews = pd.read_parquet(PROCESSED / "oews.parquet")
    pred = baseline_predictions(df, oews)
    for (src, split), g in df.groupby(["source", "split"]):
        p = pred.loc[g.index].dropna()
        y = g.loc[p.index, "annual_wage"]
        print(f"{src:9s} {split:6s} n={len(y):>7,}  MAE(log)={mae_log(y, p['p50']):.4f}  "
              f"pinball50={pinball(y, p['p50'], 0.5):,.0f}  cov80={coverage(y, p['p10'], p['p90']):.3f}")


if __name__ == "__main__":
    main()
