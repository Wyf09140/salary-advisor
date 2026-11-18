# Evidence-Based Salary Advisor for Early-Career Tech Candidates

CS6140 Final Project · Northeastern University · Fall 2026

Given a job title, location, current salary and resume, the advisor returns:

1. a predicted market wage range (P10 / P50 / P90),
2. where the candidate's current pay falls in that range, and
3. the missing skills most associated with higher pay in comparable roles (associational, not causal).

Baseline: BLS OEWS median wage for the matching occupation and area.

## Team and ownership

| Workstream | Owner | Folder |
| --- | --- | --- |
| Data | Yifan Wei | `src/data/` |
| Models | Son Sophak Otra | `src/models/` |
| Application (frontend) | Pubudu Gunasekara | `src/app/` |

## Deliverables (due Dec 6, 2026)

- `report/`: final report as PDF (max 8 pages, 11 pt, single-spaced)
- `presentation/`: slides plus a 5 ± 1 minute recorded video (MP4/MOV, uploaded to Canvas)

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Kaggle data needs an API token at `~/.kaggle/kaggle.json` (Kaggle → Settings → Create New Token).

## Run the pipeline

```bash
make data       # download + clean + build train.parquet
make baseline   # BLS-median baseline metrics
make train      # quantile models
make evaluate   # MAE (log wage), pinball loss, 80% interval coverage
make app        # launch Streamlit app
make test       # interface + offline end-to-end pipeline tests
```

## Repository layout

```
config/              SOC codes, skill vocabulary, data source settings
data/raw/            downloaded files (gitignored)
data/processed/      cleaned outputs (gitignored; regenerate with `make data`)
src/data/            download, clean, join, baseline           (Yifan)
src/models/          features, training, evaluation, predict    (Sophak)
src/app/             resume parser, Streamlit UI                (Pubudu)
notebooks/           EDA and experiments
prompts/             AI prompt logs, one file per member (required for report)
report/              report source, figures, final PDF
presentation/        slides, script
tests/               interface tests
```

## Interface contracts

**Data → Models:** `data/processed/train.parquet`, schema in `src/data/schema.py`; details and caveats in `src/data/README.md`.

**Models → App:** `src/models/predict.py`

```python
predict(title, location, skills, years_exp) -> {"p10", "p50", "p90", "bls_median"}
recommend(profile, top_k=5) -> [(skill, delta_p50_usd), ...]
```

The app runs against the stub in `predict.py` until trained models are saved to `models/`.

## Data sources

1. U.S. Bureau of Labor Statistics. Occupational Employment and Wage Statistics (OEWS). https://www.bls.gov/oes/
2. U.S. Department of Labor, OFLC. LCA Programs Disclosure Data. https://www.dol.gov/agencies/eta/foreign-labor/performance
3. arshkon. LinkedIn Job Postings (2023–2024). Kaggle. https://www.kaggle.com/datasets/arshkon/linkedin-job-postings
4. National Center for O*NET Development. O*NET 31.0 Database. CC BY 4.0. https://www.onetcenter.org/database.html
5. U.S. Bureau of Labor Statistics. OEWS May 2025 Area Definitions. https://www.bls.gov/oes/area_definitions_m2025.xlsx
