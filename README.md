# Sales Data AI Agent

Natural-language Q&A over a SQLite **Superstore** database (Claude + tools), with optional Excel export, interactive **Plotly** charts (HTML + optional PNG), saved SQL reports, data-quality checks, session export (JSON / Markdown / PDF), database backups, and scheduled KPI digests.

## Features

| Area | What’s included |
|------|------------------|
| **Data & analysis** | Saved report library (`saved_queries.json`), row-count **estimates** for SELECTs, SQLite **EXPLAIN QUERY PLAN**, automated **data quality** checks (row counts, nulls, date range, orphan FKs). |
| **Export & sharing** | Excel export (excel agent), chart **HTML** + optional **PNG** (requires `kaleido`), conversation export as **JSON**, **Markdown**, or **PDF** (`fpdf2`). |
| **UX & trust** | System prompts ask the model to **cite** which query or saved report supports metrics; session exports bundle chat + query log + chart paths. |
| **Ops & safety** | Default **read-only** SQLite connections for normal queries; **`backup_database()`** uses SQLite’s backup API (timestamped files under `backups/`). **Rate limiting** is not implemented. |
| **Testing** | **`pytest`** golden SQL tests (`tests/golden_questions.json`) run against `superstore.db` with **no LLM API**. |

## Requirements

- Python 3.10+ recommended  
- `superstore.db` in the project root (see schema in `Capstone_DB_Schema.sql`)  
- `ANTHROPIC_API_KEY` in `.env` for agent scripts and Streamlit  

Install dependencies:

```bash
pip install -r requirements.txt
```

## Quick start

```bash
# Interactive CLI agent
python qa_agent.py

# Agent + Excel export tool
python qa_agent_with_excel.py

# Streamlit UI
streamlit run web_app.py
```

## Configuration

### Environment (`.env`)

| Variable | Purpose |
|----------|---------|
| `ANTHROPIC_API_KEY` | Claude API key (required for agents) |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` | Optional; for `scheduled_digest.py` email |
| `DIGEST_FROM_EMAIL`, `DIGEST_TO_EMAIL` | Optional; recipients for digest email (comma-separated `DIGEST_TO_EMAIL`) |

### Saved reports

Edit **`saved_queries.json`** to add reusable `id`, `title`, `description`, and `sql`. The agent exposes **`list_saved_reports`** and **`run_saved_report`**.

### Scheduled digest

**`digest_config.json`** lists titled SQL snippets. Run manually:

```bash
python scheduled_digest.py
```

Writes **`exports/digest_YYYYMMDD_HHMMSS.md`**. If SMTP + `DIGEST_TO_EMAIL` are set, sends the same content by email. Automate with **cron** or Task Scheduler (example in `scheduled_digest.py` docstring).

### Read-only mode

`DatabaseQAAgent(..., read_only=True)` (default) opens the DB with SQLite **`?mode=ro`**. Backups open a separate read-write connection via the backup API.

### Chart PNG

If **`kaleido`** is installed, `create_visualization` also writes a **PNG** next to the HTML under `charts_output/`. If not, HTML-only still works.

## Testing

```bash
pytest tests/ -v
```

Golden tests only require `superstore.db` and do not call Anthropic.

## Project layout (main files)

| File | Role |
|------|------|
| `qa_agent.py` | Main Claude agent + tools |
| `qa_agent_with_excel.py` | Same + `export_to_excel` |
| `database_tools.py` | SQL, Excel export, estimates, explain, backup, read-only |
| `visualization_tools.py` | Plotly HTML/PNG charts |
| `data_quality.py` | Quality report + Markdown summary |
| `saved_queries.json` / `saved_queries.py` | Report library |
| `agent_analysis_tools.py` | Anthropic tool specs for analysis features |
| `conversation_export.py` | Markdown / PDF / JSON bundle helpers |
| `scheduled_digest.py` | Cron-friendly digest + optional email |
| `web_app.py` | Streamlit UI + exports + quality + backup |
| `tests/` | Golden SQL regression tests |

## License

See `LICENSE` in the repository.
