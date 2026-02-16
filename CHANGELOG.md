# Changelog

All notable changes to Argo Energy Solutions will be documented in this file.

## [2026-02-16] — Phase metrics backfill support (stage: Ingest / Govern)
- Changed `ingest_to_postgres.py` from `ON CONFLICT DO NOTHING` to `ON CONFLICT DO UPDATE SET` for readings
- Enables re-ingestion to update existing rows with phase metrics (V1–V3, I1–I3, neutral current, THD, frequency, etc.) that were null before the electrical health fields were added
- Added refresh of `mv_hourly_usage` to historical-backfill workflow (Govern step) after ingestion completes
- **To backfill phase data (2025-04-29 → 2026-01-14):** Run "Historical backfill" workflow with START_DATE=2025-04-29, END_DATE=2026-01-14; the workflow now updates existing rows and refreshes materialized views

## [2026-02-15] — Fix v_clean_readings view column conflict (stage: Govern)
- Fixed `npm run db:views` failing with "cannot change name of view column 'created_at' to 'frequency_hz'"
- Updated `create-layered-views.sql`: drop `mv_hourly_usage` before `v_clean_readings` so the view can be dropped cleanly; use `CREATE VIEW` instead of `CREATE OR REPLACE` for v_clean_readings (PostgreSQL cannot rename columns via REPLACE)
- Removed "Known Issue" from `docs/PROJECT_CONTEXT.md`

## [2026-02-15] — Neutral current availability confirmed (stage: Govern / Config)
- Diagnostic (`npm run py:diagnostic:neutral-current`) confirmed neutral current (In) IS available from Wilson Center WCDS meters: API returns In; readings.neutral_current_a populated (~11% of historical readings; newer ingestion has full coverage)
- Added comment in `config/report_config.py` documenting availability
- Added `operations/diagnostic_neutral_current.py` for definitive DB/API check
- Reverted earlier "not available" copy in analyze/electrical_health.py and PDF report; neutral section shows data when present

## [2026-02-15] — Cost ingestion robustness and validation (stage: Ingest)
- Harden cost field handling in `ingest_to_postgres.py`: safe numeric conversion via `_safe_cost_value()`, support alternate API key (`Cost`), handle null/missing gracefully
- Add ingest-level warning when a channel returns no cost data for a full day (CFO report needs it)
- Add `validate_data.py` check: warn on channels with ≥100 readings and 100% null cost
- No schema changes; cost column already populated

## [2026-02-15] — Governance system implemented (stage: Infra)
- Created/updated `.cursor/rules/argo-governance.mdc` — always-active AI governance rules
- Created `.cursor/rules/workflow-changes.mdc` — auto-applied rules for workflow edits
- Created `docs/cursor-prompts.md` — task-specific prompt template library

---

## [1.0.0] - 2026-02-04

### Added
- ✅ **Data validation script** with 7 comprehensive health checks
- ✅ **GitHub Actions workflows** for automation (daily sync, weekly reports, validation)
- ✅ **Tableau export functionality** with 4 pre-built CSV formats
- ✅ **Historical ingestion script** with data integrity rules
- ✅ **Customer-ready report generator** (HTML + JSON)
- ✅ **Project organization** with dedicated export folders

### Changed
- 🔄 Reorganized Tableau exports to `exports/tableau/` folder
- 🔄 Updated documentation structure for clarity
- 🔄 Consolidated Python scripts into unified structure

### Fixed
- 🐛 Fixed authentication issues in historical ingestion
- 🐛 Corrected unit conversion (Wh → kWh, W → kW)
- 🐛 Fixed field name mapping for API responses

---

## [0.9.0] - 2026-02-03

### Added
- ✅ **Python-first migration** - All core features in Python
- ✅ **Neon PostgreSQL** integration
- ✅ **TIMESTAMPTZ migration** for timezone safety
- ✅ **Analytics modules** (sensor health, after-hours, anomalies, spikes, quick wins)
- ✅ **Natural language query** interface

### Changed
- 🔄 Migrated from Node.js to Python for data processing
- 🔄 Database schema updated to use TIMESTAMPTZ
- 🔄 Daily sync moved from Node.js to Python

---

## [0.8.0] - 2026-01-26

### Added
- ✅ **Daily sync automation** via cron job
- ✅ **Weekly report generation** with analytics
- ✅ **Database setup** (Neon PostgreSQL)

### Changed
- 🔄 Switched from API-per-report to local database approach
- 🔄 Added comprehensive test suite

---

## [0.7.0] - 2025-12-15

### Added
- ✅ Initial Eniscope API integration (Node.js)
- ✅ Basic data collection scripts
- ✅ Wilson Center analysis

---

## Upcoming Features

### Version 1.1.0 (Planned)
- [ ] Automated email delivery for weekly reports
- [ ] Multi-site support in dashboards
- [ ] Advanced anomaly detection with ML
- [ ] Cost allocation by department/area
- [ ] Real-time alerting system

### Version 1.2.0 (Planned)
- [ ] Web dashboard for real-time monitoring
- [ ] Mobile app integration
- [ ] Predictive maintenance insights
- [ ] Carbon footprint tracking
- [ ] Demand response optimization

---

## Version Numbering

Following [Semantic Versioning](https://semver.org/):

**MAJOR.MINOR.PATCH**

- **MAJOR:** Breaking changes (database schema changes, API changes)
- **MINOR:** New features (new reports, analytics, integrations)
- **PATCH:** Bug fixes (no new features)

**Examples:**
- `1.0.0 → 1.0.1` - Fixed bug in validation
- `1.0.1 → 1.1.0` - Added Tableau export feature
- `1.1.0 → 2.0.0` - Changed database schema (breaking)

---

**Maintained by:** Argo Energy Solutions
**Last Updated:** February 4, 2026
