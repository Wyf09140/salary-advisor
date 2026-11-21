"""Train P10/P50/P90 wage models. Owner: Pubudu.

Input: data/processed/train.parquet (schema in src/data/schema.py; caveats in src/data/README.md).

1. Features (src/models/features.py): only what predict() can compute from title + location.
   - Linear (done): log OEWS median and spread for the row's occupation/area, metro-missing flag,
     SOC one-hot.
   - Planned (Step 5): SBERT sentence embeddings of `title` (all-MiniLM-L6-v2), optionally PCA.
   - Not used: `wage_level` (not available at predict time; Step 6 ablation only), skills (Stage 2).
2. Target: log(annual_wage). Predictions are exponentiated back to USD. Quantiles commute with
   monotone transforms, so exp(q_tau(log y)) = q_tau(y) and pinball in USD stays valid.
3. Split: src/models/split.py. Employer names are collapsed to a company key (all AMAZON * entities
   -> AMAZON) and each company goes wholly to train or test (stable md5 hash, 20% test), so no
   company appears in both. Rows with split == "shift" (FY2026 LCA, wage-weighted H-1B selection)
   are held out entirely as an out-of-time test set.
4. Models, one per quantile tau in {0.1, 0.5, 0.9}:
   - statsmodels QuantReg (linear quantile regression), interpretable comparison (done).
   - XGBoost with objective="reg:quantileerror", quantile_alpha=tau (Step 5).
   Crossing (p10 > p50 or p50 > p90) is fixed by sorting the three predictions per row and the
   number of crossed rows is reported.
5. Evaluation (src/models/evaluate.py): mae_log on P50, pinball loss at each tau, and P10-P90
   coverage, against the BLS median baseline on the same rows. `make train` reports the train
   fold only; the test fold is scored once, in `make evaluate`.
6. Save (Step 8): models/quantile_models.pkl, loaded by src/models/predict.py.
"""
import numpy as np
import pandas as pd

TAUS = (0.1, 0.5, 0.9)
QCOLS = {0.1: "p10", 0.5: "p50", 0.9: "p90"}


def fit_quantreg(X: pd.DataFrame, y_log: pd.Series, taus=TAUS, max_iter: int = 5000) -> dict:
    """Fit one linear quantile regression per tau on log wage. Returns {tau: params Series}."""
    from statsmodels.regression.quantile_regression import QuantReg
    models = {}
    for tau in taus:
        res = QuantReg(y_log.to_numpy(), X.to_numpy()).fit(q=tau, max_iter=max_iter)
        models[tau] = pd.Series(res.params, index=X.columns, name=f"tau={tau}")
    return models


def predict_quantreg(models: dict, X: pd.DataFrame) -> pd.DataFrame:
    """Raw (unsorted) quantile predictions in USD, columns p10/p50/p90, indexed like X."""
    return pd.DataFrame({QCOLS[t]: np.exp(X.to_numpy() @ models[t][X.columns].to_numpy())
                         for t in sorted(models)}, index=X.index)


def fix_crossing(pred: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Sort p10/p50/p90 per row; return (fixed frame, number of rows that were crossed)."""
    cols = ["p10", "p50", "p90"]
    vals = pred[cols].to_numpy()
    crossed = int(((vals[:, 0] > vals[:, 1]) | (vals[:, 1] > vals[:, 2])).sum())
    return pd.DataFrame(np.sort(vals, axis=1), index=pred.index, columns=cols), crossed


def load_stage1():
    """Early-career rows with folds and OEWS quantiles attached, plus the OEWS table."""
    from src.config import PROCESSED
    from src.models.features import bls_quantiles
    from src.models.split import assign_folds
    df = pd.read_parquet(PROCESSED / "train.parquet")
    oews = pd.read_parquet(PROCESSED / "oews.parquet")
    df = df[df["early_career"]]
    df = df.join(assign_folds(df))
    return df, oews, bls_quantiles(df, oews)


def train_linear(df: pd.DataFrame, bls: pd.DataFrame):
    """Fit QuantReg on the train fold. Returns (models, design matrix for all rows)."""
    from src.models.features import linear_features
    X = linear_features(df, bls)
    fit_rows = (df["fold"] == "train") & X.notna().all(axis=1)
    models = fit_quantreg(X[fit_rows], np.log(df.loc[fit_rows, "annual_wage"]))
    return models, X


def main() -> None:
    from src.models.evaluate import results_table
    df, oews, bls = load_stage1()
    models, X = train_linear(df, bls)
    tr = df[df["fold"] == "train"]
    raw = predict_quantreg(models, X.loc[tr.index].dropna())
    fixed, crossed = fix_crossing(raw)
    print(f"QuantReg fitted on {len(raw):,} train-fold rows "
          f"(LCA {int((tr.source == 'lca').sum()):,}, postings {int((tr.source == 'postings').sum()):,}).")
    print(f"Quantile crossing on train fold: {crossed:,} rows ({crossed / len(raw):.2%}), fixed by sorting.\n")
    print("Coefficients (log-wage scale):")
    print(pd.DataFrame(models).round(4).to_markdown())
    print("\nTrain fold only (in-sample; the test fold is scored in `make evaluate`):\n")
    table = results_table(tr, {"baseline": bls.loc[tr.index], "quantreg": fixed})
    print(table.drop(columns=["split", "fold"], errors="ignore").to_markdown(index=False, floatfmt=".4f"))


if __name__ == "__main__":
    main()
