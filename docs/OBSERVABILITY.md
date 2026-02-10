## Observability & Monitoring

### Logging

- **Python logging** is centralized via `backend/python_scripts/lib/logging_config.py`.
- Entry scripts call:
  - `configure_logging()` – configures a JSON-style logger to stdout.
  - `get_logger(__name__)` – module-specific logger.
- JSON log shape (approximate):
  - `{"ts":"2026-02-10T18:30:00+0000","level":"INFO","logger":"...","msg":"...","extra":{...}}`

Key scripts wired to logging:

- `ingest/ingest_to_postgres.py`
- `ingest/historical_ingestion.py`
- `govern/validate_data.py`
- `deliver/generate_customer_report.py`
- `deliver/generate_weekly_report.py`

Logs flow to:

- **Local dev**: terminal output, plus `logs/daily_sync.log` via `operations/daily_sync.sh`.
- **GitHub Actions**: workflow logs (same JSON format).

### Sentry Error Tracking

- Optional Sentry integration lives in `backend/python_scripts/lib/sentry_client.py`.
- Entry scripts call:
  - `init_sentry(service_name="...")` near the top.
  - `capture_exception(exc)` in top-level exception handlers.
- Sentry only activates when `SENTRY_DSN` is set; otherwise it is a no-op.

To enable Sentry:

1. Create a project in Sentry and copy its DSN.
2. Add to `.env` (and GitHub Actions secrets if desired):

```env
SENTRY_DSN=your_sentry_dsn_here
ENVIRONMENT=production
```

3. Re‑run the scripts / workflows; unhandled exceptions and logged exceptions will appear in Sentry.

To disable Sentry:

- Unset `SENTRY_DSN` (or remove it from the environment). Logging continues to work normally.

### GitHub Actions Integration

- **Daily sync** and **weekly report** workflows already:
  - Fail on non‑zero script exit.
  - Create GitHub Issues on failure with links to the run.
- With Phase 3:
  - Logs in Actions are structured JSON, easier to filter/grep.
  - If `SENTRY_DSN` is set, production errors will also appear in Sentry with stack traces.

