# Models workstream: status (owner: Pubudu)

_Last updated: 2026-11-20 · branch `model/eval-harness` (PR not opened yet; several steps will go in one PR)_

## Where we are

| # | Step | Status |
| --- | --- | --- |
| 1 | Evaluation harness + baseline table | ✅ done |
| 2 | Employer-grouped train/test split | ✅ done |
| 3 | Linear quantile regression (QuantReg) | ⏭ next |
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
  rows, flags groups under 300 rows). `make evaluate` prints the baseline table by fold.
- `src/models/split.py`: `company_key()` collapses entity variants (AMAZON COM SERVICES, AMAZON WEB
  SERVICES, ... -> AMAZON; generic first words like AMERICAN/BANK use two tokens). `assign_folds()` puts
  each company wholly in train or test (stable md5 hash, 20% test, same fold for its LCA and postings
  rows); `split == "shift"` rows are always fold `shift`, never trained on. `python -m src.models.split`
  prints the split report.
- `tests/test_evaluate.py`, `tests/test_split.py`: hand-computed metrics; no company in both folds;
  shift never in train/test; assignment stable under row shuffling and subsetting.

## Split (early-career rows)

| Source | Train | Test | Shift |
| --- | --- | --- | --- |
| LCA | 128,278 | 29,972 (18.9%) | 129,881 |
| Postings | 291 | **75** (20.5%) | 0 |

- 26,563 employer names -> 20,494 companies; 0 companies in both train and test.
- Largest companies: Amazon 7.6% (train), Tata 3.3% (train), **Google 2.4% (test)**, Microsoft 2.4% (train).
- 75% of shift rows come from companies seen in train; 32,546 shift rows are from unseen companies.

## Current numbers: BLS-median baseline by fold (early-career)

| Group | n | MAE(log) | Pinball50 (USD) | Cov80 | Below P10 | Above P90 |
| --- | --- | --- | --- | --- | --- | --- |
| LCA train | 128,278 | 0.2251 | 13,335 | 0.935 | 5.6% | 0.9% |
| LCA test | 29,972 | 0.2214 | 13,376 | 0.923 | 6.5% | 1.2% |
| LCA shift (seen companies) | 97,335 | 0.1952 | 12,206 | 0.975 | 1.5% | 1.0% |
| LCA shift (unseen companies) | 32,546 | 0.1944 | 12,256 | 0.969 | 1.9% | 1.2% |
| Postings train | 291 ⚠ | 0.2838 | 16,183 | 0.818 | 15.5% | 2.8% |
| Postings test | 75 ⚠ | 0.2660 | 15,294 | 0.787 | 17.3% | 4.0% |

⚠ = under 300 rows: too noisy to support a claim on its own. A calibrated interval has ~10% in each tail.

## Findings so far

- **BLS P90 is too high for early-career pay:** only 1-4% of wages exceed it (vs 10% nominal), because OEWS
  percentiles cover all experience levels. Main argument for an early-career model.
- **LCA coverage is inflated by the prevailing-wage floor** (few LCA wages fall below P10). Compare models
  on pinball and MAE; read LCA coverage with this in mind.
- **Postings coverage (~0.8) hides a shift:** ~16% below P10 vs ~3% above P90, so BLS sits too high for
  these jobs.
- **FY2026 shift is easier than FY2025** for the baseline (MAE 0.195 vs 0.22), consistent with the
  wage-weighted H-1B selection. A good shift score is not by itself evidence of generalisation.

## Known issues / risks

- **Only 75 postings rows in test.** Postings results will get bootstrap confidence intervals.
- **One company can move the test set:** Google (2.4% of rows) is entirely in test. Final results will
  include a check with a different hash seed.
- **Train/serve SOC mismatch:** LCA `soc_code` is employer-filed, but `predict()` gets SOC from
  `TitleMatcher`. Agreement rate to be measured before relying on SOC as a feature.
- **`years_exp` is NaN for all LCA rows** (52% present in early-career postings), so it partly encodes the
  data source. Covered by the Step 6 ablation.
- **Postings employers include staffing agencies** (DICE, JOBOT, PIPER), so `employer` is sometimes the
  recruiter, not the hiring company.
- `tests/test_pipeline.py` fails on pandas 3.x (`load_oews` reads an xlsx straight from a zip stream).
  Data-side fix; does not affect models.

## Needs from others

- Nothing blocking right now.
- Otra: app location dropdown will use OEWS metro names; models will provide the list in `src/models/`
  (Step 8).
