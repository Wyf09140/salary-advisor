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
