# Models workstream: status (owner: Pubudu)

_Last updated: 2026-11-20 · branch `model/eval-harness` (PR not opened yet; several steps will go in one PR)_

## Where we are

| # | Step | Status |
| --- | --- | --- |
| 1 | Evaluation harness + baseline table | ✅ done |
| 2 | Employer-grouped train/test split | ✅ done |
| 3 | Linear quantile regression (QuantReg) | ✅ done |
| 4 | Model vs baseline on same rows, LCA and postings separately | ✅ done (test fold used once for QuantReg) |
| 5 | SBERT title embeddings + XGBoost quantile models | ⏭ next |
| 6 | Ablation: with vs without `wage_level` | ⬜ |
| 7 | Stage 2 skill uplift (postings only) | ⬜ |
| 8 | Save models, real `predict()` / `recommend()` (stub stays as fallback) | ⬜ |
| 9 | Final results table + caveats for the report | ⬜ |

Interfaces unchanged: `predict()` / `recommend()` signatures and `src/data/schema.py` are untouched.
The app keeps running on the stub until Step 8.

## What's in this branch

- `src/models/evaluate.py`: `evaluate_quantiles()` (MAE on log wage, pinball at 0.1/0.5/0.9, 80% coverage,
  share below P10 / above P90) and `results_table()` (per-group scores, aligned by index, counts dropped
  rows, flags groups under 300 rows), `cluster_bootstrap_ci()` (95% CI resampling whole companies) and
  `comparison_table()` (paired model-minus-baseline differences). `make evaluate` is the held-out
  evaluation: fit on train fold, score test and shift folds.
- `src/models/split.py`: `company_key()` collapses entity variants (AMAZON COM SERVICES, AMAZON WEB
  SERVICES, ... -> AMAZON; generic first words like AMERICAN/BANK use two tokens). `assign_folds()` puts
  each company wholly in train or test (stable md5 hash, 20% test, same fold for its LCA and postings
  rows); `split == "shift"` rows are always fold `shift`, never trained on. `python -m src.models.split`
  prints the split report.
- `src/models/features.py`: Stage 1 features, restricted to what `predict()` can compute from title +
  location: log OEWS median and log(P90/P10) spread for the row's occupation/area, metro-missing flag,
  SOC one-hot (reference 15-1252). No `wage_level`, source, employer or year.
- `src/models/train.py`: `fit_quantreg()` (statsmodels QuantReg on log wage, tau 0.1/0.5/0.9),
  `predict_quantreg()`, `fix_crossing()` (sort + count). `make train` fits on the train fold and reports
  train-fold metrics only.
- `tests/test_evaluate.py`, `tests/test_split.py`, `tests/test_train.py`: hand-computed metrics; no company
  in both folds; shift never in train/test; QuantReg recovers known quantile lines on synthetic data;
  crossing fix; guard that no predict-time-unavailable column enters the features.

## Step 4: QuantReg vs BLS baseline, held out (the result to quote)

Same rows for both models. Δ = QuantReg minus baseline (negative = QuantReg better), 95% CI from a
company-cluster bootstrap (2,000 resamples).

| Group | n (companies) | MAE(log) base → QR | ΔMAE(log) [95% CI] | ΔPinball50 USD [95% CI] | Cov80 QR [CI] | Cov80 base |
| --- | --- | --- | --- | --- | --- | --- |
| LCA test | 29,972 (3,137) | 0.221 → **0.155** | −0.066 [−0.105, −0.030] | −4,222 [−6,588, −2,015] | 0.770 [0.744, 0.800] | 0.923 |
| LCA shift, seen companies | 97,335 (7,177) | 0.195 → 0.142 | −0.053 [−0.083, −0.021] | −3,268 [−5,157, −1,285] | 0.815 | 0.975 |
| LCA shift, unseen companies | 32,546 (6,802) | 0.194 → 0.159 | −0.035 [−0.070, +0.003] | −2,056 [−4,443, +688] | 0.780 | 0.969 |
| Postings test ⚠ | 75 (49) | 0.266 → 0.249 | −0.017 [−0.069, +0.029] | −1,208 [−4,577, +1,719] | **0.533** [0.405, 0.662] | 0.787 |

Quantile crossing before sorting: 0 rows in test, shift and shift_unseen.

What we can claim:
- **LCA, held-out companies: QuantReg beats the BLS median** (MAE 0.155 vs 0.221, ~30% lower; CI excludes 0),
  and its interval is far closer to 80% (0.77 vs 0.92 inflated by the wage floor).
- **Out of time (FY2026), unseen companies: improvement is smaller and the CI just touches 0.** Do not
  claim it generalises to new companies in a new year; say "smaller, not significant at 95%".
- **Postings: no detectable difference in accuracy, and the interval is worse** (53% coverage, 31% of
  wages above P90). The model is an LCA model; its interval is too narrow and too low for postings.
- CIs are wide despite 30k rows because a few companies dominate (Google ~13% of LCA test rows); the
  effective sample size is the number of companies, not rows.
- In FY2026 the model's P90 is too low (15-18% above P90): consistent with the wage-weighted H-1B
  selection raising FY2026 wages.

## Step 3: QuantReg on the train fold (in-sample, not a result to claim)

| Model | Source | n | MAE(log) | Pinball50 | Cov80 | Below P10 | Above P90 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | LCA | 128,278 | 0.2251 | 13,335 | 0.935 | 5.6% | 0.9% |
| quantreg | LCA | 128,278 | 0.1388 | 7,939 | 0.800 | 10.0% | 10.0% |
| baseline | postings ⚠ | 291 | 0.2838 | 16,183 | 0.818 | 15.5% | 2.8% |
| quantreg | postings ⚠ | 291 | 0.2501 | 13,842 | **0.601** | 17.9% | 22.0% |

- Quantile crossing: 0 of 128,569 train rows (expected for a linear model with few features; re-checked on test).
- `log_bls_p50` coefficient ≈ 0.87-0.89: early-career pay moves less than 1:1 with the local OEWS median.
- **Fitted almost entirely on LCA** (128,278 vs 291 postings rows), so the interval is calibrated for LCA
  and too narrow for postings (60% coverage in-sample). Expect the same or worse on test.
- `metro_missing` ≈ +0.15-0.20: rows without a metro pay more relative to the state fallback (median
  wage/BLS P50 = 0.96 vs 0.80 with a metro). See data issue below.

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

- **The test fold has now been used once (QuantReg).** Step 5 tuning uses GroupKFold inside the train
  fold only; XGBoost is scored on test once, when finished. Any interval recalibration for postings must
  also be fitted inside the train fold.
- **Only 75 postings rows in test (49 companies).** Postings CIs span roughly ±0.05 MAE, so no postings
  accuracy claim is supportable either way.
- **One company can move the test set:** Google (2.4% of rows) is entirely in test. Final results will
  include a check with a different hash seed.
- **Train/serve SOC mismatch:** LCA `soc_code` is employer-filed, but `predict()` gets SOC from
  `TitleMatcher`. Agreement rate to be measured before relying on SOC as a feature.
- **`years_exp` is NaN for all LCA rows** (52% present in early-career postings), so it partly encodes the
  data source. Covered by the Step 6 ablation.
- **Postings employers include staffing agencies** (DICE, JOBOT, PIPER), so `employer` is sometimes the
  recruiter, not the hiring company.
- **30,101 early-career rows (10.4%) have no county and therefore no metro**, all with `county_fips` null,
  concentrated in high-wage states (TX 5.5k, MA 3.9k, CA 3.0k, WA 2.0k, NJ 1.6k, CT 1.6k). They fall back to
  the state median, which is too low for them. Raised with Yifan (CT likely the 2022 planning-region change).
- `tests/test_pipeline.py` fails on pandas 3.x (`load_oews` reads an xlsx straight from a zip stream).
  Data-side fix; does not affect models.

## Needs from others

- Nothing blocking. Yifan: county matching gap (10% of rows, see Known issues).
- Otra: app location dropdown will use OEWS metro names; models will provide the list in `src/models/`
  (Step 8).
