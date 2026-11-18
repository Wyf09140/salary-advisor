"""Train P10/P50/P90 wage models. Owner: Pubudu.

PLAN ONLY - not implemented yet.

Input: data/processed/train.parquet (schema in src/data/schema.py; caveats in src/data/README.md).

1. Features
   - Title: SBERT sentence embeddings of `title` (sentence-transformers, e.g. all-MiniLM-L6-v2),
     optionally reduced with PCA.
   - Location: metro (fall back to state), occupation `soc_code`, `wage_level`, `years_exp`.
   - Skills: `skill_*` columns (postings only; NaN for LCA rows).
2. Target: log(annual_wage). Predictions are exponentiated back to USD.
3. Split: GroupShuffleSplit grouped on `employer`, so no employer appears in both train and test.
   Rows with split == "shift" (FY2026 LCA, wage-weighted H-1B selection) are held out entirely
   as an out-of-time test set.
4. Models, one per quantile tau in {0.1, 0.5, 0.9}:
   - XGBoost with objective="reg:quantileerror", quantile_alpha=tau.
   - statsmodels QuantReg (linear quantile regression) as an interpretable comparison.
   Fix any quantile crossing by sorting the three predictions per row.
5. Evaluation (src/models/evaluate.py): mae_log on P50, pinball loss at each tau, and P10-P90
   coverage. Compare against the BLS median baseline (src/data/baseline.py) on the same rows.
6. Save: models/quantile_models.pkl (fitted models, feature pipeline, and SBERT model name),
   loaded by src/models/predict.py.
"""


def main() -> None:
    raise NotImplementedError("training not implemented yet; see module docstring for the plan")


if __name__ == "__main__":
    main()
