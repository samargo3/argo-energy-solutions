# Changelog

All notable changes to Argo Energy Solutions will be documented in this file.

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
