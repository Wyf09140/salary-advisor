"""Evaluation metrics shared by the baseline and the quantile models. Owner: Pubudu.

`results_table` scores any set of P10/P50/P90 predictions per group with the same code, so the
baseline and every model are compared on identical rows. `cluster_bootstrap_ci` gives confidence
intervals that resample whole companies (rows of one company are not independent).

`python -m src.models.evaluate` is the held-out evaluation: models are fitted on the train fold
and scored on the test and shift folds only. Run it once per finished model, not while tuning.
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


def row_losses(y, pred: pd.DataFrame) -> pd.DataFrame:
    """Per-row losses whose means are the metrics in evaluate_quantiles (for bootstrapping)."""
    y = np.asarray(y, float)
    out = {"mae_log": np.abs(np.log(y) - np.log(pred["p50"].to_numpy()))}
    for tau, c in ((0.1, "p10"), (0.5, "p50"), (0.9, "p90")):
        d = y - pred[c].to_numpy()
        out[f"pinball{c[1:]}"] = np.maximum(tau * d, (tau - 1) * d)
    out["cov80"] = ((y >= pred["p10"].to_numpy()) & (y <= pred["p90"].to_numpy())).astype(float)
    return pd.DataFrame(out, index=pred.index)


def cluster_bootstrap_ci(values, clusters, n_boot: int = 2000, alpha: float = 0.05,
                         seed: int = 0) -> tuple[float, float, float]:
    """(mean, lo, hi) of `values`, resampling whole clusters with replacement.

    Pass a per-row difference (loss_model - loss_baseline) to get a paired CI for the difference.
    Each replicate's mean is sum of resampled cluster sums / sum of resampled cluster sizes.
    """
    v = pd.Series(np.asarray(values, float))
    c = pd.Series(np.asarray(clusters))
    sums = v.groupby(c).sum().to_numpy()
    sizes = v.groupby(c).size().to_numpy()
    rng = np.random.default_rng(seed)
    k = len(sums)
    draws = rng.integers(0, k, size=(n_boot, k))
    reps = sums[draws].sum(axis=1) / sizes[draws].sum(axis=1)
    lo, hi = np.quantile(reps, [alpha / 2, 1 - alpha / 2])
    return float(v.mean()), float(lo), float(hi)


def comparison_table(df: pd.DataFrame, model: pd.DataFrame, baseline: pd.DataFrame,
                     groups, by: str = "eval_fold") -> pd.DataFrame:
    """Paired model-minus-baseline differences with company-cluster bootstrap 95% CIs.

    Negative = model better for losses. For coverage, the CI is on each model's own cov80.
    """
    rows = []
    for (src, f), g in df.groupby(["source", by], sort=True):
        if f in groups:
            lm, lb = row_losses(g["annual_wage"], model.loc[g.index]), row_losses(g["annual_wage"], baseline.loc[g.index])
            row = {"source": src, by: f, "n": len(g), "companies": g["company"].nunique()}
            for m in ("mae_log", "pinball50"):
                d, lo, hi = cluster_bootstrap_ci(lm[m] - lb[m], g["company"])
                row[f"Δ{m}"] = f"{d:+.4f} [{lo:+.4f}, {hi:+.4f}]" if m == "mae_log" else f"{d:+,.0f} [{lo:+,.0f}, {hi:+,.0f}]"
            for name, l in (("cov80_model", lm), ("cov80_baseline", lb)):
                c, lo, hi = cluster_bootstrap_ci(l["cov80"], g["company"])
                row[name] = f"{c:.3f} [{lo:.3f}, {hi:.3f}]"
            rows.append(row)
    return pd.DataFrame(rows)


def main() -> None:
    # Imported here: baseline.py imports this module, and tests must not need data files.
    from src.models.train import fix_crossing, load_stage1, predict_quantreg, train_linear

    df, oews, bls = load_stage1()
    # Extra group: shift rows from companies never seen in the train fold
    df["eval_fold"] = df["fold"].where(~((df["fold"] == "shift") & ~df["shift_seen"]), "shift_unseen")
    models, X = train_linear(df, bls)  # fitted on the train fold only
    held = df[df["fold"] != "train"]
    ok = X.loc[held.index].notna().all(axis=1) & bls.loc[held.index].notna().all(axis=1)
    held = held[ok]  # identical rows for both models
    raw = predict_quantreg(models, X.loc[held.index])
    qr, _ = fix_crossing(raw)

    print("Stage 1 held-out evaluation (early_career). Models fitted on the train fold only.")
    print("'shift' = FY2026 rows from companies in the train fold; 'shift_unseen' = all others.\n")
    print("Quantile crossing before sorting:")
    for f, g in held.groupby("eval_fold"):
        _, n = fix_crossing(raw.loc[g.index])
        print(f"  {f:13s} {n:,} of {len(g):,} rows ({n / len(g):.2%})")
    preds = {"baseline": bls.loc[held.index], "quantreg": qr}
    table = results_table(held, preds, by=("source", "eval_fold"))
    print("\nMetrics (pinball in USD; cov80 nominal 0.80):\n")
    print(table.to_markdown(index=False, floatfmt=".4f"))
    print("\nQuantReg minus baseline, company-cluster bootstrap 95% CI (negative = QuantReg better):\n")
    comp = comparison_table(held, qr, bls, groups={"test", "shift", "shift_unseen"})
    print(comp.to_markdown(index=False))


if __name__ == "__main__":
    main()
