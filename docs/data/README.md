# Data workstream docs

Run order (Claude Code, from repo root):

1. `Use the data-explorer agent to download and profile all data sources.`
   → writes `docs/data/exploration_report.md`
2. Read the report yourself.
3. `Use the data-designer agent to check the exploration report and design the data pipeline.`
   → writes `docs/data/data_design.md`, may update `config/`
4. Implement the checklist in `data_design.md` in `src/data/clean.py`.
