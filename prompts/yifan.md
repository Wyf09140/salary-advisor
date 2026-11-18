# AI prompt log: yifan

One entry per AI interaction. Copy the prompt verbatim.

### YYYY-MM-DD · Tool · Purpose (coding / debugging / explanation / research / writing)
Prompt: ...
Outcome: ...

### 2026-11-18 · Claude Code (Opus 5.5) · Purpose: coding / research
Prompt:
```
You are working in my local repo ~/Desktop/advisor/salary-advisor (GitHub: Wyf09140/salary-advisor, a CS6140 class project). This is a company-managed Mac, so:
- Never change global git config or ~/.ssh. Only use repo-local git config (user.name "Wyf09140", user.email "Wyf09140@gmail.com" — already set).
- Never commit .venv/, data/raw/, data/processed/, models/, or any credentials.

Task 1 — Restore the project code from my clipboard
My clipboard contains the whole repo as base64-encoded tar.gz.
1. Run: pbpaste | openssl base64 -d | md5
   It must print 312f61799ab8966cf56e601874b71194. If not, stop and tell me to re-copy.
2. Extract into the repo root: pbpaste | openssl base64 -d | tar xzf -
3. Make sure .venv is not tracked: git rm -r --cached --ignore-unmatch .venv
4. Show me `git status --short | head -40`, then commit ("Add project code and data pipeline") and push to origin main.

Task 2 — Environment
1. Use the existing .venv (Python 3.12). Activate it and run: pip install -r requirements.txt
2. If xgboost fails to import, run brew install libomp.
3. Run the tests: python -m pytest -q. Fix only genuine bugs; don't weaken assertions. Report results.

Task 3 — Verify data source URLs (no big downloads yet)
Read config/sources.yaml and src/data/README.md. Check every URL against the official pages:
- BLS OEWS May 2025 metro file + area_definitions_m2025.xlsx (https://www.bls.gov/oes/tables.htm)
- DOL LCA disclosure files FY2025 Q1–Q4 and FY2026 Q1–Q3, plus the record layout PDF (https://www.dol.gov/agencies/eta/foreign-labor/performance). Confirm whether WORKSITE_COUNTY is in the main file or a separate worksite file.
- O*NET 31.0 text zip (https://www.onetcenter.org/database.html)
- The OEWS annual top-code value in the May 2025 technical notes (set oews_topcode_annual).
Update the config with the correct URLs. Show me a table of what changed, and the approximate download size, then WAIT for my OK before downloading.

Task 4 — After I say OK
Run make data, then make baseline. If clean.py fails on real column names, fix it and add the case to tests/fixtures.py so the offline test still covers it. Show me data/processed/data_report.md and the baseline output. Commit and push the fixes.

Throughout: log every instruction I give you, verbatim with the date, in prompts/yifan.md (the course requires all AI prompts), and commit it with each change.
```
Outcome: First clipboard check failed (clipboard held this prompt, md5 d41d8cd9… = empty decode); told to re-copy.

### 2026-11-18 · Claude Code (Opus 5.5) · Purpose: coding
Prompt: (pasted the base64-encoded tar.gz of the repo, 24,770 chars; decoded md5 312f61799ab8966cf56e601874b71194 — not reproduced here)
Outcome: Checksum verified, archive listed and extracted into repo root, committed and pushed.
Outcome (Task 2–3, same session): pip install OK; xgboost needed `brew install libomp`. pytest: test_pipeline passes; test_interfaces can't import src.models (Sophak's module, not yet in repo). Verified source URLs; fixed FY2026 LCA paths, added worksite files + record layout to config; top-code left unverified. BLS/DOL block scripted downloads (403). Waiting for OK before downloading.

### 2026-11-18 · Claude Code (Opus 5.5) · Purpose: explanation
Prompt: (pasted a Chinese-language project summary written in an earlier chat with another assistant — sections "一、这个项目是什么 / 二、这几天你做了什么 / 三、现在的状态" — followed by) 对吧
Outcome: Confirmed sections 一–二 against the repo; corrected section 三 (code now pushed, deps installed, tests status, download blocker).

### 2026-11-18 · Claude Code (Opus 5.5) · Purpose: coding
Prompt: files downloaded. Kaggle data is already in data/raw/linkedin/ (downloaded manually), so make download.py skip the kaggle CLI when data/raw/linkedin/postings.csv exists. Then run make data and make baseline.
Outcome: download.py skips kaggle when postings.csv exists. Fixed two real-format bugs found before the run (area definitions column "May 2025 Area Code"; OEWS zip has BOS + MSA files and the code read only the first), mirrored both in tests/fixtures.py. Verified top-code $239,200 from the OEWS Field Descriptions sheet. baseline.py falls back to local metrics until src/models/evaluate.py exists.
Outcome (cont.): make data OK (265,003 final rows). make baseline OK. Also fixed P90_TOPCODED, which flagged 28 real May 2025 P90 values above $239,200 (no '#' markers in the 2025 file); fixture + assertions added.

### 2026-11-18 · Claude Code (Opus 5.5) · Purpose: coding / debugging
Prompt:
```
Good work. Next, in this order:

1. Restore src/models properly: change .gitignore line "models/" to "/models/" and confirm with `git check-ignore -v src/models/predict.py`. Create src/models/__init__.py (empty), evaluate.py (mae_log, pinball, coverage — same as your fallback), predict.py (stub predict() and recommend() matching the contract in README.md and tests/test_interfaces.py), and train.py (docstring plan only: SBERT title embeddings, GroupShuffleSplit on employer, log wage target, XGBoost reg:quantileerror at 0.1/0.5/0.9, statsmodels QuantReg, save to models/quantile_models.pkl). Then remove the fallback in baseline.py and run the full test suite.

2. Add FY2026 Q4 to shift_urls (file is already in data/raw/). Don't use the worksite files; add one line to src/data/README.md noting multi-worksite filings as a known limitation.

3. Diagnose title matching before tuning. Of the 10,172 Entry/Associate postings, count how many titles contain tech keywords (software, developer, engineer AND (software|data|ml|machine learning|backend|frontend|full stack), data scientist, data analyst, data engineer, machine learning, analytics, qa, test engineer, web developer, database). Report that count vs the 483 matched, and show me 30 keyword-hit titles that did NOT match (with their best SOC and score) and 20 matched titles with SOC and score. Then propose a fix (threshold change, keyword rules for common titles, or both) and show the new match count and a 30-row sample before applying it.

4. Add the LCA coverage finding (wage floor at prevailing wage inflates P10–P90 coverage to 93–97%) as a "Notes for the report" section in src/data/README.md.

Rerun make data and make baseline after steps 2–3, then commit and push. Log this message in prompts/yifan.md.
```
Outcome (steps 1, 2, 4 + step-3 diagnosis): .gitignore "/models/" (src/models no longer ignored); src/models/{__init__,evaluate,predict,train}.py added; baseline fallback removed; 6/6 tests pass. FY2026 Q4 added to shift_urls; README limitation + "Notes for the report". Title diagnosis: 354 keyword hits vs 483 matched; 103/109 keyword misses map to non-tech or out-of-scope SOCs with high scores (O*NET exact-title ties broken arbitrarily, e.g. Data Analyst -> 19-3022), not a threshold problem. Proposed keyword rules -> 552 matched; awaiting approval before applying and rerunning make data.

### 2026-11-18 · Claude Code (Opus 5.5) · Purpose: coding
Prompt:
```
OK, apply the keyword rules + exclusion list, with two tweaks: add "designer" to the exclusion list, and for 15-1299 accept only rule-based matches (drop TF-IDF matches to 15-1299). Add fixture titles for both.

Then: the postings experience filter leaves ~400 rows, too few for the skill-uplift model. Stage 1's early-career scope comes from LCA Level I/II, so postings don't need the same filter.
1. Report counts after all filters for: (a) Entry/Associate only, (b) + missing experience level, (c) all levels except Internship/Executive/Director.
2. If (c) >= 3x (a), switch postings to (c): keep the level in wage_level (entry, associate, mid-senior, unknown) and add a boolean early_career column (True for LCA I/II and postings entry/associate). Update schema.py, validate(), fixtures and src/data/README.md: Stage 1 trains on early_career rows; Stage 2 uses all
```
(message arrived truncated after "Stage 2 uses all"; interpreted as "all postings rows")
Outcome: keyword rules + exclusions (incl. "designer") in titles.py; 15-1299 accepted only from rules (none target it, so 0 postings rows). Level counts after all filters: (a) 366, (b) 693, (c) 1,338 = 3.7x (a) -> switched to (c) with early_career column; schema/validate/fixtures/README updated; new tests/test_titles.py; 8/8 tests pass. make data: 292,258 rows (291,286 early_career; postings 1,338). make baseline rerun.

### 2026-11-18 · Claude Code (Opus 5.5) · Purpose: writing
Prompt:
```
好的，Data    Yifan Wei    src/data/
Models    Son Sophak Otra    src/models/
Application (frontend)    Pubudu Gunasekara    src/app/这个Otra复制Application Pubudu负责models
```
Outcome: Swapped code ownership (interpreted 复制 as 负责): Pubudu Gunasekara -> Models (src/models/), Son Sophak Otra -> Application (src/app/). Updated README, module docstrings, data-designer agent. Report/presentation section assignments left unchanged pending confirmation.
