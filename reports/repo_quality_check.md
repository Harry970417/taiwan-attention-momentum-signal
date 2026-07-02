# Repo Quality Check (pre-publication audit)

Run 2026-07-03 against `C:\Users\user\Desktop\taiwan-attention-momentum-signal`
before any `git init` / commit / push.

## 1. requirements.txt coverage

Cross-referenced every `import` / `from` statement across `src/*.py`,
`app/*.py`, and `scripts/*.py` against `requirements.txt`. All third-party
imports (`pytrends`, `pandas`, `numpy`, `matplotlib`, `requests`, `scipy`,
`statsmodels`, `streamlit`) are listed. Standard-library imports (`json`,
`pathlib`, `subprocess`, `sys`, `time`) need no entry. **Result: PASS.**

## 2. scripts/run_all.py exists

Present at `scripts/run_all.py`; chains `run_data_collection.py` →
`run_event_study.py` → `run_momentum_control.py` →
`run_institutional_flow_analysis.py`, stopping on first failure.
**Result: PASS.**

## 3. README reproduce instructions

`README.md` §11 gives a clone → venv → `pip install -r requirements.txt` →
`python scripts/run_all.py` sequence, plus per-stage commands. Instructions
match the actual filenames in `scripts/`. **Result: PASS.**

## 4. Streamlit app launch

Started `streamlit run app/streamlit_app.py --server.headless true` against
this repo and confirmed an HTTP 200 response with no startup exceptions in
the log. The app's data-dependent pages will show a "file not found"
message (not a crash) until a user runs the data-collection and analysis
scripts locally, since `data/raw/` and the full `data/processed/` are
intentionally not committed. **Result: PASS (starts cleanly; full
interactive walkthrough of every page was not re-verified in this repo
copy — same caveat as the original research repo).**

## 5. Figure / table path correctness

All `results/figures/*.png` and `results/tables/*.csv` referenced from
`README.md`, `README_zh.md`, `docs/*.md`, and `notebooks/*.ipynb` were
checked against the files actually present in this repo. **Result: PASS**
(see item 6 for the full relative-link scan).

## 6. Markdown link check

Scanned every `.md` file for relative (non-http, non-anchor) links and
verified the target file exists on disk. **Result: PASS — no broken
links found.**

## 7. Personal absolute paths

Searched all `.py`, `.md`, `.ipynb`, `.csv`, `.txt` files for
`C:\Users\user`, `/c/Users/user`, and `C:/Users/user`. **Result: PASS —
none found.** All scripts use `Path(__file__).resolve().parent...`-style
relative paths.

## 8. API keys / tokens / secrets

Searched all text files for `api_key`, `secret`, `password`, and
`token\s*=` (case-insensitive). **Result: PASS — none found.** The FinMind
and Google Trends calls used in this project are made without any API key
(FinMind's free public endpoint; `pytrends` uses no credential).

## 9. Overclaiming language

Searched for `guaranteed`, `beat the market`, `profitable trading
strategy`, `predict stock price`, `independent alpha factor`, `we predict`
(case-insensitive). All 4 matches found are inside **negated** disclaimer
sentences (e.g., "does not constitute a profitable trading strategy", "not
an independent alpha factor", "not guaranteed to be linear") — i.e., the
report correctly denies these claims rather than making them.
**Result: PASS.**

## 10. Repo size / data hygiene

Total repo size: **863 KB**. No `data/raw/` or `data/processed/` directory
present — only `data/sample/attention_weekly_panel_sample.csv` (3 stocks x
20 weeks, ~24 KB), used solely to illustrate the panel schema.
**Result: PASS.**

## Overall

No blocking issues found. The repository is internally consistent, free of
personal paths and secrets, does not overclaim, and every documented
reproduce/demo path resolves to a real file. Recommend a final human read
of `README.md` / `README_zh.md` for tone before `git init` / commit / push,
since that step was explicitly requested to be done by the user, not by
this assistant.
