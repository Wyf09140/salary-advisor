# Models workstream: status (owner: Pubudu)

_Last updated: 2026-11-20 · branch `model/eval-harness`_

## Where we are

| # | Step | Status |
| --- | --- | --- |
| 1 | Evaluation harness + baseline table | ✅ done (this branch, PR open) |
| 2 | Employer-grouped train/test split | ⏭ next (`model/split-quantreg`) |
| 3 | Linear quantile regression (QuantReg) | ⬜ |
| 4 | Model vs baseline on same rows, LCA and postings separately | ⬜ |
| 5 | SBERT title embeddings + XGBoost quantile models | ⬜ |
| 6 | Ablation: with vs without `wage_level` | ⬜ |
| 7 | Stage 2 skill uplift (postings only) | ⬜ |
| 8 | Save models, real `predict()` / `recommend()` (stub stays as fallback) | ⬜ |
| 9 | Final results table + caveats for the report | ⬜ |

Interfaces unchanged: `predict()` / `recommend()` signatures and `src/data/schema.py` are untouched.
The app keeps running on the stub until Step 8.

## What's in this branch

- `src/models/evaluate.py`: `evaluate_quantiles()` (MAE on log wage, pinball at 0.1/0.5/0.9, 80% coverage,
  share below P10 / above P90) and `results_table()` (per-group scores, aligned by index, counts dropped
  rows, flags groups under 300 rows). `make evaluate` prints the baseline table.
- `tests/test_evaluate.py`: hand-computed metric values, pinball direction check, index-alignment and
  dropped-row checks.

## Current numbers: BLS-median baseline, early-career rows (all rows, before the train/test split)

| Group | n | MAE(log) | Pinball50 (USD) | Cov80 | Below P10 | Above P90 |
| --- | --- | --- | --- | --- | --- | --- |
| LCA train (FY2025) | 158,250 | 0.2244 | 13,343 | 0.933 | 5.7% | 1.0% |
| LCA shift (FY2026) | 129,881 | 0.1950 | 12,219 | 0.974 | 1.6% | 1.0% |
| Postings | 366 | 0.2801 | 16,001 | 0.811 | 15.9% | 3.0% |

Matches `make baseline` exactly. A calibrated interval would have ~10% in each tail.

## Findings so far

- **BLS P90 is too high for early-career pay:** only 1-3% of wages exceed it (vs 10% nominal), because OEWS
  percentiles cover all experience levels. Main argument for an early-career model.
- **LCA coverage is inflated by the prevailing-wage floor** (few LCA wages fall below P10). Compare models
  on pinball and MAE; read LCA coverage with this in mind.
- **Postings coverage (0.81) hides a shift:** 15.9% below P10 vs 3% above P90, so BLS sits too high for
  these jobs.
- **FY2026 shift is easier than FY2025** for the baseline (MAE 0.195 vs 0.224), consistent with the
  wage-weighted H-1B selection. A good shift score is not by itself evidence of generalisation.

## Known issues / risks

- **Only 366 early-career postings rows**, so roughly 70 in a test split. Postings results will get bootstrap
  confidence intervals and be labelled as small-sample.
- **Same company under several employer names** (e.g. 5+ Amazon entities, 6+ Deloitte). Step 2 will group
  these before splitting so a company can't be in both train and test.
- **10,005 employers appear in both LCA train and shift**, so shift is an out-of-time test but not
  employer-held-out; it will be reported both ways.
- **Train/serve SOC mismatch:** LCA `soc_code` is employer-filed, but `predict()` gets SOC from
  `TitleMatcher`. Agreement rate to be measured before relying on SOC as a feature.
- **`years_exp` is NaN for all LCA rows** (52% present in early-career postings), so it partly encodes the
  data source. Covered by the Step 6 ablation.
- `tests/test_pipeline.py` fails on pandas 3.x (`load_oews` reads an xlsx straight from a zip stream).
  Data-side fix; does not affect models.

## Needs from others

- Nothing blocking right now.
- Otra: app location dropdown will use OEWS metro names; models will provide the list in `src/models/`
  (Step 8).
