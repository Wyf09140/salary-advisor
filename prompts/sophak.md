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

### 2026-11-24 · Claude Code (Opus 5.5) · Purpose: research (tooling)
Prompt:
```
I wanted to know where is all my claude skill
```
Outcome: Claude listed the skill locations under `C:\Users\User\.claude`: account-synced skills, synced engineering/zapier plugin skills, and one local plugin. It noted that the repo's `.claude/agents` are subagents, not skills.

Prompt:
```
I wanted to add skill into my claude that works either with terminal or this chat how would I do that?
```
Outcome: Claude explained personal skills (`~/.claude/skills/<name>/SKILL.md`), project skills (`.claude/skills/`) and claude.ai uploads, with an example SKILL.md. After a pasted PowerShell error (the path had been run as a command), it explained how to create the folder and file. It then checked the install: the `oil-ui` UI/UX skill was installed and loaded.

### 2026-11-24 · Claude Code (Opus 5.5) · Purpose: coding (frontend)
Prompt:
```
please build me the UI for this project: with this style from the skills:

fly-island

please commit every step of the way
```
Outcome: Claude used the oil-ui skill. "fly-island" is not a named style in that skill, so it was read as a floating-islands look: results float as white rounded panels over a sky gradient. Committed on `app/frontend` in steps:
1. Theme: `.streamlit/config.toml` and `src/app/theme.py` (CSS variables, Manrope font, island styling).
2. Layout: an input island and a range island with an HTML P10–P90 band, P50 tick, dashed BLS median line and a coral "You" marker (`src/app/components.py`).
3. Skills island: ranked uplift bars from `recommend()`. The resume parse is cached and fills editable skills and years-of-experience inputs.
4. States: missing title/location, missing salary hint, unreadable resume, failed prediction; component unit tests (13 tests pass).
5. Independent visual review of screenshots, then fixes.
Screenshots were taken with Playwright driving Edge (the skill's screenshot tool needs Node 22; Node 20 is installed).

### 2026-11-24 · Claude Code (Opus 5.5) · Purpose: explanation
Prompt:
```
how do I run the app
```
Outcome: Claude explained activating `.venv` and running `streamlit run src/app/app.py` on the `app/frontend` branch, and noted the stub numbers.

Prompt:
```
why is it on streamlit?
```
Outcome: Claude explained that the team scaffold already chose Streamlit (requirements.txt, Makefile `make app`, README, the starter app.py) and listed the trade-offs and alternatives.

Prompt:
```
So are you building on streamlit or on a dedicated front end?
```
Outcome: Claude confirmed the UI so far was Streamlit only (app.py, theme.py, components.py).

### 2026-11-24 · Claude Code (Opus 5.5) · Purpose: coding (frontend)
Prompt:
```
I wanted to build on a dedicated frontend, keep the streamlit. but with the skill built me the frontend that  i wanted to project it to me. With this style fly-island from the skills
```
Outcome: Claude kept the Streamlit app unchanged and built a dedicated web frontend with the oil-ui skill in the same floating-island style. It committed each step on `app/frontend`:
1. `src/app/server.py`: a stdlib-only JSON API and static server (`/api/skills`, `/api/parse-resume`, `/api/estimate`) wrapping the same `predict()`/`recommend()` and resume parser; 4 new tests.
2. `web/index.html`: the page layout (sky, islands with cast shadows, profile form).
3. Interaction: resume upload fills editable skill chips and years; inline field errors; verdict-first range island; mint skills island framed as associations.
4. `make web` in the Makefile and README.
5. An independent design review (7/10), then fixes: the hero floats highest, layered clouds, coral verdict matching the You pin, BLS line drawn on the bar, hero-sized empty preview, phone scrolls to the verdict.
Claude opened the page in the browser at http://localhost:8600. 17 tests pass.

### 2026-11-24 · Claude Code (Opus 5.5) · Purpose: explanation
Prompts:
```
how do I run the project
```
```
how do I run the front end
```
```
Answer my question is the LLM and everything else has been implemented by my teammate?
```
```
Answer only:

So where does the project answer came from?
```
Outcome: Claude gave run commands for both front ends, the tests and the pipeline. It checked GitHub: there is no LLM in the design; Yifan's data pipeline is merged; Pubudu's `model/eval-harness` branch has finished 4 of 9 steps (QuantReg beats the BLS baseline on held-out LCA companies) but is not merged, and `predict()` is still a stub. Current answers therefore come from the fixed stub numbers in `src/models/predict.py`.

### 2026-11-24 · Claude Code (Opus 5.5) · Purpose: coding (frontend)
Prompt:
```
https://oil-ui-gallery.vercel.app/works/fly-island/live/index.html

I wanted to UI to be a notch instead so it's more easier to access
```
Outcome: Claude rendered the reference page with Playwright: a dark notch docked to the top edge that expands from a 291×35 pill into a 510×308 tabbed panel (0.52 s spring curve). It rebuilt `web/index.html` around that pattern with the app's own content and colours. The collapsed pill shows the verdict and a mini range glyph; click, `/` or the hero button opens Profile / Range / Skills tabs; Esc or clicking outside collapses it. Claude fixed a CSS class clash that hid the status dot and removed a misplaced badge, then committed `baceb53`.

### 2026-11-25 · Claude Code (Opus 5.5) · Purpose: explanation (git)
Prompts:
```
how do I run it
```
```
please give me the push command
```
Outcome: Claude gave the command to run the web notch (`python -m src.app.server`) and the push command (`git push`, or `git push -u origin app/frontend`).

### 2026-11-25 · Claude Code (Opus 5.5) · Purpose: research / planning
Prompt:
```
This is still base on web.

I wanted to make it as a application where it runs on your desktop give me a plan how can you do that?
```
Outcome: Claude recommended wrapping the existing notch page in pywebview (Edge WebView2): a frameless, always-on-top window docked to the top of the screen with a Python bridge, a global hotkey, a tray icon, and PyInstaller packaging. It compared Electron, Tauri and PySide6, and flagged risks: bundle size once PyTorch/SBERT models land, Windows only, transparency.

### 2026-11-25 · Claude Code (Opus 5.5) · Purpose: coding (desktop app)
Prompts:
```
yes please
```
```
again please commit every step
```
```
there is a white box on my screen
```
Outcome: Claude worked on new branch `app/desktop` with defaults: Windows only, keep the web version, dev command plus `.exe`. The first transparent-window attempt left a white, then dark, box on screen, because WebView2 ignores WinForms transparency keys. Claude closed that test window and switched approach: the window itself is the island, resized, re-centred and clipped to rounded bottom corners whenever the page reports a size change. Commits:
1. `0dcdd12`: desktop shell shaped like the island (`src/desktop/app.py`, desktop mode in `web/index.html`, `requirements-desktop.txt`).
2. `5f289dc`: Python bridge through a shared `server.dispatch()`, so web and desktop give identical answers.
3. `33efc61`: Ctrl+Alt+S global hotkey, tray icon (Open / Quit), no taskbar button, collapse when clicking into another app.
4. `87bebab`: PyInstaller build (`python -m src.desktop.build` gives `dist/SalaryAdvisor/SalaryAdvisor.exe`, ~75 MB).
5. README "Desktop app" section, `make desktop` / `make desktop-exe`, desktop tests (20 tests pass).

### 2026-11-25 · Claude Code (Opus 5.5) · Purpose: explanation / planning
Prompts:
```
I don't see the desktop branch on my github
```
```
how do I run it?
```
```
just answer my question so for instance I wanted this to natively for linkend like with this notch turn on you past in your resume then it will estimate your range and also in real time will filter out the job on linkend. is it possible with the current LLM or do we need anything more?
```
```
So what is the best approach for this project to make it impressive and with in the time frame
```
Outcome: Claude explained that the branch was only local (`git push -u origin app/desktop`) and how to run the desktop app. On LinkedIn, it explained that the blocker is access, not AI: LinkedIn has no public jobs API and its User Agreement forbids scraping; a browser extension reading the page the user is viewing is the realistic route, and an LLM is optional. It recommended making this future work. It then gave a priority plan: real `predict()` from Pubudu's QuantReg first, a "why this range" panel, one demo frontend, merges before the Nov 30 freeze, and a scripted demo story.

### 2026-11-25 · Claude Code (Opus 5.5) · Purpose: coding (frontend)
Prompts:
```
with this design reference please and animation and make it look interactive
```
(attached screenshot: a wide notch dashboard with media player, calendar, app grid, to-do list and focus timer widgets)
```
please commit every step of the way
```
Outcome: Claude rebuilt the expanded notch (`web/index.html`, used by both the web and desktop apps) as one wide bar of live widgets:
- pay card (gradient tile, verdict, range scrubber, −5k/+5k what-if salary)
- profile with an experience picker
- skill tiles
- a skills-to-add checklist (tick to add, then re-estimate)
- a typical/low/high/BLS number cycler with auto-play
- a resume button
Estimates update live with no Estimate button. Animations: staggered widget pop-in, gliding range markers, counting numbers, pay-card bump on mood change, springy tiles and ticks; all off under reduced motion. Commits on `app/desktop`: `f0a114b` (layout), `cdfb75c` (interactions), `636c2ba` (animations), and the responsive/desktop fit. Verified in a browser at 1600/1024/390 px and in the desktop window (1200×288 open, 374×38 collapsed).
