"""Evaluation metrics shared by the baseline and the quantile models. Owner: Pubudu.

`results_table` scores any set of P10/P50/P90 predictions per group with the same code, so the
baseline and every model are compared on identical rows. `python -m src.models.evaluate` prints
the baseline table on Stage 1 (early_career) rows.
"""
import numpy as np
import pandas as pd

QUANTILE_COLS = ["p10", "p50", "p90"]
SMALL_N = 300  # groups below this are flagged: metrics too noisy to support a claim


def mae_log(y, p) -> float:
    """Mean absolute error on log wages (scale-free: 0.10 ~ 10% typical error)."""
    return float(np.mean(np.abs(np.log(np.asarray(y, float)) - np.log(np.asarray(p, float)))))


def pinball(y, q, tau: float) -> float:
    """Pinball (quantile) loss of prediction q at quantile tau, in the units of y."""
    d = np.asarray(y, float) - np.asarray(q, float)
    return float(np.mean(np.maximum(tau * d, (tau - 1) * d)))


def coverage(y, lo, hi) -> float:
    """Share of y inside [lo, hi]; a calibrated P10-P90 interval should give ~0.80."""
    y = np.asarray(y, float)
    return float(np.mean((y >= np.asarray(lo, float)) & (y <= np.asarray(hi, float))))


def evaluate_quantiles(y, p10, p50, p90) -> dict:
    """All Stage 1 metrics for one set of rows. Inputs must be aligned and NaN-free.

    below_p10 / above_p90 should each be ~0.10 for a calibrated interval; an asymmetric split
    (e.g. below_p10 ~ 0 on LCA, where wages are floored at the prevailing wage) shows *why*
    coverage is off, which coverage alone hides.
    """
    y, p10, p50, p90 = (np.asarray(a, float) for a in (y, p10, p50, p90))
    return {
        "n": int(len(y)),
        "mae_log": mae_log(y, p50),
        "pinball10": pinball(y, p10, 0.1),
        "pinball50": pinball(y, p50, 0.5),
        "pinball90": pinball(y, p90, 0.9),
        "cov80": coverage(y, p10, p90),
        "below_p10": float(np.mean(y < p10)),
        "above_p90": float(np.mean(y > p90)),
    }


def results_table(df: pd.DataFrame, preds: dict[str, pd.DataFrame],
                  by=("source", "split"), target: str = "annual_wage") -> pd.DataFrame:
    """One row per (model, group). `preds` maps model name -> DataFrame[p10, p50, p90] indexed like df.

    Rows where a model has any missing quantile are excluded for that model and counted in
    `n_dropped`, so silent drops are visible. Compare models only on groups where n matches.
    """
    if not df.index.is_unique:
        raise ValueError("df index must be unique to align predictions by index")
    by = list(by)
    rows = []
    for name, pred in preds.items():
        pred = pred.reindex(df.index)[QUANTILE_COLS]  # align by index, never by position
        ok = pred.notna().all(axis=1)
        for key, g in df.groupby(by, sort=True):
            idx = g.index[ok.loc[g.index].to_numpy()]
            p = pred.loc[idx]
            key = key if isinstance(key, tuple) else (key,)
            row = {"model": name, **dict(zip(by, key)), "n_dropped": int(len(g) - len(idx))}
            if len(idx):
                row.update(evaluate_quantiles(g.loc[idx, target], p["p10"], p["p50"], p["p90"]))
            else:
                row["n"] = 0
            row["small_n"] = row["n"] < SMALL_N
            rows.append(row)
    cols = ["model", *by, "n", "n_dropped", "small_n", "mae_log", "pinball10", "pinball50",
            "pinball90", "cov80", "below_p10", "above_p90"]
    return pd.DataFrame(rows).reindex(columns=cols)


def main() -> None:
    # Imported here: baseline.py imports this module, and tests must not need data files.
    from src.config import PROCESSED
    from src.data.baseline import baseline_predictions
    from src.models.split import assign_folds

    df = pd.read_parquet(PROCESSED / "train.parquet")
    oews = pd.read_parquet(PROCESSED / "oews.parquet")
    df = df[df["early_career"]]  # Stage 1 scope
    df = df.join(assign_folds(df))
    # Extra group: shift rows from companies never seen in the train fold
    df["eval_fold"] = df["fold"].where(~((df["fold"] == "shift") & ~df["shift_seen"]), "shift_unseen")
    preds = {"baseline": baseline_predictions(df, oews)}
    table = results_table(df, preds, by=("source", "eval_fold"))
    print("Stage 1 (early_career) results by fold. Pinball in USD; cov80 nominal 0.80.")
    print("'shift' = FY2026 rows from companies in the train fold; 'shift_unseen' = all others.\n")
    print(table.to_markdown(index=False, floatfmt=".4f"))


if __name__ == "__main__":
    main()
