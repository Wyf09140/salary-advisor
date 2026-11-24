# AI prompt log: sophak

One entry per AI interaction. Copy the prompt verbatim.

### YYYY-MM-DD · Tool · Purpose (coding / debugging / explanation / research / writing)
Prompt: ...
Outcome: ...

### 2026-11-24 · Claude Code (Opus 5.5) · Purpose: research / coding (environment setup)
Prompt:
```
https://github.com/Wyf09140/salary-advisor.git

how to setup this repo for work
```
Outcome: Claude inspected the already-cloned repo (README, CONTRIBUTING, Makefile, requirements), created a `.venv` with Python 3.11, installed `requirements.txt`, and ran `python -m pytest -q` (8 passed). It gave Windows/PowerShell equivalents for the Makefile targets, noted that the Kaggle token goes in `C:\Users\User\.kaggle\kaggle.json`, and summarized the team workflow from CONTRIBUTING.md.

### 2026-11-24 · Claude Code (Opus 5.5) · Purpose: explanation
Prompt:
```
Are you understand the project?
```
Outcome: Claude read the data schema, data README, app, resume parser, training plan, metrics and tests, then summarized the project. Its summary covered the pipeline (LCA + LinkedIn postings + OEWS/O*NET → train.parquet → quantile models → Streamlit app), the two model stages (wage range on early-career rows; skill uplift on postings), the evaluation plan and the LCA coverage caveat. It reported the current status: data mostly built, models not yet implemented (predict.py is a stub), app basic. It also corrected an earlier point: BLS/DOL files must be downloaded manually in a browser. Weak spots it flagged in the app: the `extract_years` regex, no handling for unmatched titles/locations, and a plain progress-bar display.

### 2026-11-24 · Claude Code (Opus 5.5) · Purpose: explanation (planning)
Prompt:
```
what is my tasks?
```
Outcome: Claude used the README milestones and the code to list app-workstream tasks: log prompts; harden the resume parser (fix `extract_years`, handle empty/scanned PDFs, add tests); improve the UI (range chart, input validation, editable skills); connect to the real `predict()`/`recommend()` by Nov 29; handle unmatched titles/locations (agree a contract with Pubudu); cache model loading with `st.cache_resource`; merge before the Nov 30 code freeze. It suggested claiming the "Results: app screenshots" report section and the video Demo segment, both still TBD.

### 2026-11-24 · Claude Code (Opus 5.5) · Purpose: writing
Prompt:
```
Can you log my promt
```
Outcome: Claude added the entries above (and this one) to `prompts/sophak.md`, following the format of the existing template and teammates' logs.

### 2026-11-24 · Claude Code (Opus 5.5) · Purpose: explanation (git workflow)
Prompt:
```
My work stream is front end can you please give me the branch name for this
```
Outcome: Claude explained the `app/<task>` naming rule in CONTRIBUTING.md and suggested `app/resume-parser`, `app/ui-range-chart` and `app/model-integration`.

### 2026-11-24 · Claude Code (Opus 5.5) · Purpose: explanation (git workflow)
Prompt:
```
how can you delete the app/resume-parser
```
Outcome: Claude checked that the local branch had no commits of its own, then deleted it itself (`git checkout main; git branch -d app/resume-parser`) and listed the delete commands.

Prompt:
```
don't do it agenticly
```
Outcome: Claude apologized and agreed that for "how do I" questions it will only explain the commands, and will run commands that change things only when explicitly asked.

### 2026-11-24 · Claude Code (Opus 5.5) · Purpose: explanation (git workflow)
Prompt:
```
please give me an name for the frontend branch
```
Outcome: Claude suggested `app/frontend`.

Prompt:
```
app/frontend

this is my branch how do I access this?
```
Outcome: Claude explained `git checkout app/frontend` (or `git checkout -b` to create it), how to check the current branch, and the add/commit/push workflow.

Prompt: (pasted terminal error) `error: pathspec 'app/frontend' did not match any file(s) known to git`
Outcome: Claude explained that the branch was not known locally and said to run `git fetch origin` and `git branch -a`, then `git checkout app/frontend`.

Prompt: (pasted `git fetch origin` output showing `[new branch] app/frontend -> origin/app/frontend`)
Outcome: Claude said to run `git checkout app/frontend` to create a local tracking branch.

### 2026-11-24 · Claude Code (Opus 5.5) · Purpose: coding
Prompt:
```
I'm able to access it rn give me something to commit
```
Outcome: Claude fixed `extract_years` in `src/app/resume_parser.py`. It previously returned the largest "N years" anywhere in the resume (e.g. "50 years of history"). Now it only counts "N years/yrs ... experience" and ignores values over 40. Claude added `test_extract_years_ignores_unrelated_numbers` to `tests/test_interfaces.py`, updated this log, and ran the tests (9 passed). Sophak made the commit.
