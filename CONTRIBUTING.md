# Workflow

- Branch per task: `data/<task>`, `model/<task>`, `app/<task>`
- Open a pull request into `main`; one other member reviews
- Do not change `src/data/schema.py` or the `predict()` / `recommend()` signatures without telling both affected owners
- Log every AI prompt in `prompts/<your-name>.md` and commit it with your code
- Never commit raw data, API keys or `kaggle.json`

## Milestones

| Date | Milestone |
| --- | --- |
| Nov 18 | Interfaces frozen |
| Nov 22 | train.parquet + baseline (data); training framework (models); app on stub (app) |
| Nov 29 | Trained models; app integrated with real models |
| Nov 30 | Code freeze |
| Dec 3 | Report sections and slides drafted; backup demo clip |
| Dec 4 | Rehearsal; report merged |
| Dec 5 | Record video |
| Dec 6 | Submit PDF + video |
