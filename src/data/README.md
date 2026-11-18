# Data pipeline (owner: Yifan)

`make data` downloads everything into `data/raw/`, then writes:

- `data/processed/train.parquet`: one row per wage observation (schema in `schema.py`)
- `data/processed/oews.parquet`: OEWS May 2025 P10/P50/P90 by metro and SOC
- `data/processed/data_report.md`: row counts after each filter (paste into the report)

## Sources and filters

| Source | Kept rows | Location key | Experience proxy |
| --- | --- | --- | --- |
| DOL LCA FY2025 (`split=train`) | Certified, H-1B, full-time, tech SOC, PW level I/II | WORKSITE_COUNTY + STATE → county → metro | `wage_level` I/II |
| DOL LCA FY2026 Q1–Q3 (`split=shift`) | same | same | same |
| Kaggle arshkon postings (`split=train`) | USD base salary, full-time, Entry/Associate, title matched to tech SOC | `fips` → metro | `wage_level` entry/associate, `years_exp` from description |
| BLS OEWS May 2025 | tech SOCs | metro AREA code | none (baseline only) |
| O*NET 31.0 | all titles | none | none (title → SOC matching) |

## Notes for the model workstream

- **Skill columns are NaN for LCA rows** (LCA has no job description). Train the wage-range model
  (Stage 1) on all rows without skill features; train the skill-uplift model (Stage 2) on postings only.
- **`split=shift`** is FY2026 LCA, filed under the wage-weighted H-1B selection rule. Use it as an
  out-of-time test, not for training.
- Group the train/test split by `employer` (already normalized: suffixes and punctuation removed).
- **Known limitation, multi-worksite filings:** LCA rows use only the first worksite in the main file; filings with `TOTAL_WORKSITE_LOCATIONS` > 1 have their other worksites in separate `LCA_Worksites_*` files, which we don't join.
- OEWS P90 can be top-coded (`P90_TOPCODED`); top-coded values are set to the cap in config.

## Before the first real run

1. Confirm every URL in `config/sources.yaml` on the source pages (names change each release).
2. Open one FY2025 LCA record layout PDF and check that `WORKSITE_COUNTY` is in the main file.
3. Check the OEWS top-code value in the May 2025 technical notes and set `oews_topcode_annual`.
4. Tune `title_match_min_score` by eyeballing 50 matched posting titles.

## Notes for the report

- **LCA coverage of the BLS P10–P90 interval is inflated (93% FY2025, 97% FY2026, vs 80% nominal).**
  H-1B employers must pay at least the prevailing wage, which for Level I/II is pegged to OEWS
  percentiles (~17th / ~34th) for the same occupation and area. LCA wages are therefore floored
  near the bottom of the OEWS distribution and rarely fall below P10, so coverage is high by
  construction, not because the BLS interval is well calibrated for early-career candidates.
  Postings (no wage floor) show 80.5%. Compare models to the baseline on pinball loss and MAE,
  and read LCA coverage with this floor in mind.
