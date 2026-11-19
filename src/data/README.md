# Data pipeline (owner: Yifan)

**Raw data:** BLS and DOL block scripted downloads (HTTP 403), so download these in a browser into
`data/raw/` (URLs in `config/sources.yaml`): `oesm25ma.zip`, `area_definitions_m2025.xlsx`, and the eight
`LCA_Disclosure_Data_FY2025_Q1..Q4` / `FY2026_Q1..Q4` files. Put the Kaggle dataset in `data/raw/linkedin/`
(or let the kaggle CLI fetch it). `make data` skips files that already exist, fetches O*NET, then writes:

- `data/processed/train.parquet`: one row per wage observation (schema in `schema.py`)
- `data/processed/oews.parquet`: OEWS May 2025 P10/P50/P90 by metro and SOC
- `data/processed/city_metro.parquet`: (city, state) → metro lookup built from LCA worksites, used by `geo.city_to_metro`
- `data/processed/data_report.md`: row counts after each filter (paste into the report)

## Sources and filters

| Source | Kept rows | Location key | Experience proxy |
| --- | --- | --- | --- |
| DOL LCA FY2025 (`split=train`) | Certified, H-1B, full-time, tech SOC, PW level I/II | WORKSITE_COUNTY + STATE → county → metro | `wage_level` I/II |
| DOL LCA FY2026 Q1–Q4 (`split=shift`) | same | same | same |
| Kaggle arshkon postings (`split=train`) | USD base salary, full-time, all levels except Internship/Executive/Director, title matched to tech SOC | `fips` → metro | `wage_level` entry/associate/mid-senior/unknown, `early_career` = entry/associate, `years_exp` from description |
| BLS OEWS May 2025 | tech SOCs | metro AREA code | none (baseline only) |
| O*NET 31.0 | all titles | none | none (title → SOC matching) |

## Notes for the model workstream

- **Prediction-time conversion (use the same code as the pipeline):**
  ```python
  from src.data.titles import TitleMatcher
  from src.data.geo import location_to_metro
  matcher = TitleMatcher()                    # build once (needs data/raw/db_31_0_text.zip)
  soc = matcher.soc("Software Engineer, New Grad")  # '15-1252'; None = no match; check `in SOC_CODES`
  metro, state = location_to_metro("San Jose, CA")  # ('41940', 'CA'); metro None -> fall back to state
  ```
  `location_to_metro` checks the LCA worksite city table, then principal cities in OEWS area titles.
- **LCA quarterly files are not cumulative** (each covers its own quarter's decision dates), but ~1% of
  `CASE_NUMBER`s reappear in a later file (e.g. certified, then withdrawn). The pipeline keeps each case's
  latest decision before filtering, so no case appears twice or in both `train` and `shift`.
- **`years_exp` is always NaN for LCA rows** (no experience field in LCA); postings have it for ~54% of rows.
- **`early_career` defines the Stage 1 scope.** It is True for every LCA row (Level I/II) and for postings
  with level Entry/Associate. **Stage 1** (wage range) trains on `early_career` rows only; **Stage 2**
  (skill uplift) uses all postings rows, with `wage_level` as a feature. Postings keep mid-senior and
  unknown levels because the entry/associate filter alone left ~370 rows, too few for Stage 2.
- **Posting titles → SOC:** keyword rules first (with an exclusion list, e.g. "designer", "business
  developer"), then TF-IDF against O*NET titles. TF-IDF matches to 15-1299 are dropped (that catch-all
  attracts "Project Manager", "Data Center Technician"); 15-1299 is accepted only from rules, and no
  rule currently targets it.
- **Skill columns are NaN for LCA rows** (LCA has no job description). Train the wage-range model
  (Stage 1) on `early_career` rows without skill features; train the skill-uplift model (Stage 2) on
  all postings rows.
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
