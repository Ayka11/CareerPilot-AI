# CareerPilot AI

> An AI-powered career assistant that discovers remote and flexible jobs, matches them to your profile with semantic scoring, generates tailored application materials, and tracks your applications — with minimal manual effort.

[![CI](https://github.com/Ayka11/CareerPilot-AI/actions/workflows/ci.yml/badge.svg)](https://github.com/Ayka11/CareerPilot-AI/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## Features

- **Resilient multi-source collection** — pulls from Remotive and RemoteOK via
  their official JSON APIs (no fragile scraping). Each source is isolated, so a
  single failure never aborts the run. Results are deduplicated across sources.
- **Semantic matching** — scores jobs against your profile using sentence
  embeddings, catching relevant roles that don't share exact keywords. Falls
  back to keyword matching automatically if no embedding backend is installed.
- **Tailored documents** — generates a formatted resume and a per-job cover
  letter, saved to `outputs/`.
- **Application tracking** — every application is recorded in a local SQLite
  database with status history.
- **Human-in-the-loop** — opens top job links in your browser; you review and
  submit. (Auto-*submitting* applications violates many job boards' terms and is
  intentionally not done.)
- **Cross-platform automation** — run manually or on a schedule via cron
  (macOS/Linux) or Task Scheduler (Windows).
- **Daily reports** — console + log file, with optional Gmail email summary.

---

## Why no LinkedIn scraping?

LinkedIn's Terms of Service prohibit automated scraping, and doing it will get
your IP flagged or blocked. The LinkedIn collector is included as a documented
stub that returns nothing by default. Use their official partner feeds if you
have access, or apply manually via the links CareerPilot opens from compliant
sources.

---

## Quick start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up your config (these files are gitignored — your data stays private)
cp .env.example .env
cp config/profile.example.yaml config/profile.yaml
#    then edit both with your details

# 3. Run
python -m agents.core.orchestrator
```

Check the `outputs/` folder for generated documents, and view tracked
applications with:

```bash
python view_tracked.py
```

---

## Configuration

**`config/profile.yaml`** — your name, contact info, summary, skills, and target
roles. The `summary` and `skills` fields drive job matching, so make them
representative of the work you actually want.

**`.env`** — runtime settings and secrets. Key options:

| Variable | Default | Purpose |
| --- | --- | --- |
| `EMBEDDING_BACKEND` | `auto` | `auto`, `local`, or `openai` |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | local sentence-transformers model |
| `MATCH_THRESHOLD` | `0.35` | drop jobs scoring below this (0–1) |
| `TOP_K_JOBS` | `10` | how many top matches to keep |
| `AUTO_OPEN_BROWSER` | `true` | open top links automatically |
| `OPENAI_API_KEY` | — | only for OpenAI embeddings / LLM letters |
| `GMAIL_APP_PASSWORD` | — | Gmail **App Password**, never your real password |

> **Security:** never commit `.env`, `config/profile.yaml`, your photo, the
> SQLite database, or logs. They're all covered by `.gitignore`.

---

## Scheduling

**macOS / Linux (cron)** — run daily at noon:

```cron
0 12 * * * cd /path/to/CareerPilot-AI && /usr/bin/python3 -m agents.core.orchestrator >> daily_log.txt 2>&1
```

**Windows (Task Scheduler)** — create a daily 12:00 PM task that runs
`run_careerpilot.bat`.

---

## Architecture

```
CareerPilot-AI/
├── agents/
│   ├── collector/collectors.py   # resilient API-first job collection + dedup
│   ├── core/orchestrator.py      # cross-platform coordinator (entry point)
│   ├── matcher.py                # embedding-based matching + keyword fallback
│   ├── resume.py                 # resume generation
│   ├── coverletter.py            # cover letter generation
│   ├── tracker.py                # SQLite application tracking
│   └── reporter.py               # daily reports
├── config/
│   └── profile.example.yaml      # template — copy to profile.yaml
├── tests/                        # offline pytest suite (runs in CI)
├── outputs/                      # generated resumes & cover letters (gitignored)
├── .env.example                  # env template — copy to .env
└── requirements.txt
```

Pipeline: **collect → deduplicate → match/rank → open links → track → report.**

---

## Development

```bash
pip install -r requirements.txt
pytest -q
```

Tests run fully offline against the keyword fallback, so they pass in CI without
network access or API keys. Add new job sources by writing a collector that
returns `list[Job]` and registering it in `COLLECTORS` in `collectors.py`.

---

## Tech stack

Python 3.11+ · requests · sentence-transformers · SQLAlchemy · python-docx ·
PyYAML · python-dotenv · pytest

---

## License

MIT — see [LICENSE](LICENSE).

Made by Aygun Aliyeva.
