# Project Organization Guide

## 📁 Folder Structure (Optimized)

```
argo-energy-solutions/
├── .github/
│   ├── workflows/              # GitHub Actions automation
│   │   ├── daily-sync.yml
│   │   ├── weekly-report.yml
│   │   └── data-validation.yml
│   └── README.md              # Workflow documentation
│
├── backend/
│   ├── python_scripts/         # ⭐ Primary: Python data processing
│   │   ├── ingest_to_postgres.py           # Daily data sync
│   │   ├── historical_ingestion.py         # Backfill historical data
│   │   ├── generate_customer_report.py     # Customer-ready reports
│   │   ├── generate_weekly_report.py       # JSON reports
│   │   ├── validate_data.py                # Data quality checks
│   │   ├── export_for_tableau.py           # Tableau CSV exports
│   │   ├── query_energy_data.py            # Natural language queries
│   │   ├── test_analytics.py               # Analytics test suite
│   │   ├── run_migration.py                # Database migrations
│   │   ├── daily_sync.sh                   # Cron wrapper script
│   │   ├── setup_cron.sh                   # Cron setup script
│   │   └── analytics/                      # Analytics modules
│   │       ├── sensor_health.py
│   │       ├── after_hours_waste.py
│   │       ├── anomaly_detection.py
│   │       ├── spike_detection.py
│   │       ├── quick_wins.py
│   │       └── statistics.py
│   │
│   └── scripts/                # Legacy: Node.js scripts (being phased out)
│       ├── data-collection/
│       ├── analysis/
│       └── utilities/
│
├── docs/                       # 📚 Documentation
│   ├── api/                   # API documentation
│   ├── guides/                # How-to guides
│   │   ├── integrations/     # BI tool integrations (Tableau, etc.)
│   │   └── reports/          # Report guides
│   ├── setup/                # Setup instructions
│   ├── troubleshooting/      # Problem resolution
│   └── reference/            # API reference docs
│
├── exports/                    # 📤 Data exports for external tools
│   ├── tableau/               # ⭐ Tableau CSV files (current)
│   ├── excel/                 # Excel exports (future)
│   └── archive/               # Old exports (monthly cleanup)
│
├── reports/                    # 📊 Generated reports
│   ├── weekly-report-*.html   # Customer HTML reports
│   ├── weekly-report-*.json   # JSON data for analysis
│   └── test-*.json            # Test/validation reports
│
├── src/                        # Frontend (React - optional)
│   ├── components/
│   ├── pages/
│   └── services/
│
├── logs/                       # 📝 Application logs
│   └── daily_sync.log         # Cron job logs
│
├── venv/                       # Python virtual environment
│
├── .env                        # 🔐 Environment variables (SECRET!)
├── .gitignore                 # Git ignore rules
├── package.json               # NPM scripts
├── requirements.txt           # Python dependencies
│
└── README.md                  # Main project README
```

---

## 🎯 Key Principles

### 1. **Python-First Architecture**
- All data processing in Python
- Better for analytics (pandas, numpy, scipy)
- Easier for data scientists to extend
- Node.js only for frontend (if needed)

### 2. **Clear Separation**
- **backend/python_scripts/** - Production code
- **exports/** - External BI tools
- **reports/** - Generated reports for customers
- **docs/** - All documentation
- **logs/** - Runtime logs

### 3. **Export Organization**
```
exports/
└── tableau/
    ├── tableau_daily_summary.csv      # ⭐ Start here
    ├── tableau_readings.csv           # Detailed data
    ├── tableau_channel_summary.csv    # Metadata
    └── tableau_hourly_patterns.csv    # Time-of-day analysis
```

### 4. **Report Organization**
```
reports/
├── weekly-report-23271-20260126.html  # Customer deliverable
├── weekly-report-23271-20260126.json  # Data for analysis
└── test-*.json                        # Internal testing
```

### 5. **Documentation Structure**
```
docs/
├── api/              # API documentation
├── guides/           # Step-by-step guides
│   ├── integrations/ # Tableau, Salesforce, etc.
│   └── reports/      # Report generation
├── setup/            # Initial setup
└── troubleshooting/  # Problem solving
```

---

## 🧹 What to Clean Up (Not Done Yet)

### Files to Keep
- ✅ All Python scripts in `backend/python_scripts/`
- ✅ All documentation in `docs/`
- ✅ Current exports in `exports/tableau/`
- ✅ Latest reports in `reports/`
- ✅ GitHub workflows in `.github/workflows/`

### Files to Consider Removing/Archiving

**Legacy Node.js scripts** (if not using):
- `backend/scripts/` - Most features now in Python
- Keep if frontend uses them
- Otherwise, archive or remove

**Old data files:**
- `data/wilson-center-*.csv` - Old CSV exports
- Can move to `exports/archive/`

**Large reports folder:**
- `reports/` is 31MB
- Archive old reports monthly
- Keep only last 3 months active

**Old documentation:**
- Consolidate duplicate guides
- Remove outdated setup instructions

---

## 🔄 Maintenance Workflows

### Daily (Automated)
```bash
# GitHub Actions runs automatically
# OR local cron job at 2 AM
```

### Weekly
```bash
# Generate fresh Tableau exports
npm run py:export:tableau

# Generate customer reports (if needed)
npm run py:report:customer
```

### Monthly (First Monday)
```bash
# Archive old reports
mv reports/weekly-report-*-$(date -d "3 months ago" +%Y%m)*.* exports/archive/

# Archive old Tableau custom exports
mv exports/tableau/tableau_custom_2025*.csv exports/archive/

# Run comprehensive validation
npm run py:validate

# Review GitHub Actions usage
# Settings → Billing → Actions
```

### Quarterly
```bash
# Update dependencies
pip install --upgrade -r requirements.txt

# Run full test suite
npm run py:test:verbose

# Review documentation accuracy
# Update any outdated guides

# Clean up archive folder
# Delete files older than 6 months
```

---

## 📦 .gitignore Strategy

**Always ignore:**
```gitignore
# Secrets
.env
.env.local
.env.production

# Python
venv/
__pycache__/
*.pyc

# Logs
logs/
*.log

# Large data files
*.csv
*.xlsx
```

**Allow specific files:**
```gitignore
# Allow these
!exports/tableau/*.csv
!package.json
!requirements.txt
```

**Current strategy:**
- ✅ Secrets ignored
- ✅ Virtual env ignored
- ✅ Logs ignored
- ⚠️ Some CSVs allowed (Tableau exports)
- ⚠️ Large reports might be committed (watch size)

---

## 🔐 Security Checklist

### Secrets Management
- [x] `.env` file in `.gitignore`
- [x] GitHub Secrets configured (or will be)
- [x] No credentials in code
- [x] Connection strings use environment variables
- [x] API keys not hardcoded

### Access Control
- [ ] Neon database: Read-only user for Tableau
- [ ] GitHub: Branch protection for `main`
- [ ] Restrict who can run GitHub Actions
- [ ] Audit logs reviewed monthly

### Data Privacy
- [x] Energy data only (not personal)
- [x] No customer financial data in exports
- [x] Reports reviewed before sharing
- [ ] Encryption for sensitive reports

---

## 📊 Project Health Metrics

### Current Status ✅

| Metric | Status | Count |
|--------|--------|-------|
| **Python Scripts** | ✅ Production | 18 files |
| **GitHub Workflows** | ✅ Configured | 3 workflows |
| **Database Size** | ✅ Healthy | 151,742 readings |
| **Documentation** | ✅ Complete | 45+ guides |
| **Tests** | ✅ Passing | 7 modules |
| **Validation** | ✅ Clean | 0 critical issues |

### Code Quality

```bash
# Check Python code quality
flake8 backend/python_scripts/ --exclude=venv

# Check for security issues
bandit -r backend/python_scripts/

# Run all tests
npm run py:test
```

### Database Health

```bash
# Run validation
npm run py:validate

# Check schema
npm run db:check-schema

# Monitor size
# Neon dashboard: console.neon.tech
```

---

## 🎯 Recommended Improvements

### Immediate (This Week)
1. ✅ **Organize Tableau exports** (DONE!)
2. [ ] **Push to GitHub** with new structure
3. [ ] **Configure GitHub Secrets** for workflows
4. [ ] **Test one workflow** manually

### Short-Term (This Month)
1. [ ] **Archive old reports** (reports/ is 31MB)
2. [ ] **Remove legacy Node.js scripts** (if unused)
3. [ ] **Set up branch protection** on main
4. [ ] **Create release v1.0.0** with git tag

### Long-Term (This Quarter)
1. [ ] **Automated email delivery** for reports
2. [ ] **Multi-site dashboard** (if you add more sites)
3. [ ] **API rate limit monitoring**
4. [ ] **Cost tracking** (Neon usage, API calls)

---

## 📚 Documentation Index

**Start here:**
- [README.md](README.md) - Project overview
- [SETUP_COMPLETE.md](SETUP_COMPLETE.md) - Current status

**Setup guides:**
- [docs/setup/NEON_SETUP_GUIDE.md](docs/setup/NEON_SETUP_GUIDE.md)
- [PYTHON_MIGRATION_COMPLETE.md](PYTHON_MIGRATION_COMPLETE.md)

**User guides:**
- [CUSTOMER_REPORTS_GUIDE.md](CUSTOMER_REPORTS_GUIDE.md)
- [GITHUB_GUIDE.md](GITHUB_GUIDE.md)
- [TABLEAU_QUICK_START.md](TABLEAU_QUICK_START.md)

**Technical docs:**
- [SCHEMA_ANALYSIS.md](SCHEMA_ANALYSIS.md)
- [MIGRATION_COMPLETE.md](MIGRATION_COMPLETE.md)
- [TESTING_COMPLETE.md](TESTING_COMPLETE.md)

**BI Integration:**
- [docs/guides/integrations/NEON_TABLEAU_DIRECT_CONNECT.md](docs/guides/integrations/NEON_TABLEAU_DIRECT_CONNECT.md)
- [TABLEAU_NO_DRIVER_WORKAROUND.md](TABLEAU_NO_DRIVER_WORKAROUND.md)

---

## 🎨 Code Style Guide

### Python
```python
# Use type hints
def fetch_data(site_id: str, days: int) -> List[Dict]:
    ...

# Clear variable names
avg_power_kw = sum(readings) / len(readings)

# Docstrings for functions
"""
Fetch energy readings from database
Args:
    site_id: Organization ID
    days: Number of days to fetch
Returns:
    List of reading dictionaries
"""

# Use constants
BUSINESS_HOURS_START = 7
BUSINESS_HOURS_END = 18
```

### File Naming
```
✅ Good:
snake_case.py          # Python scripts
kebab-case.yml         # YAML configs
PascalCase.tsx         # React components
SCREAMING_SNAKE.md     # Documentation

❌ Avoid:
camelCase.py
random_Naming_123.py
```

### Commit Messages
```
✅ Good format:
Add data validation script with 7 health checks
Fix: Correct unit conversion in historical ingestion
Update: Reorganize Tableau exports to dedicated folder

❌ Avoid:
updated stuff
fix
wip
asdf
```

---

## 🚀 Quick Reference

```bash
# VALIDATION & HEALTH
npm run py:validate           # Check data quality

# DATA SYNC
npm run py:ingest            # Sync latest data (7 days)
npm run py:ingest:full       # Sync 90 days
npm run py:sync              # Daily sync script (cron)

# REPORTS
npm run py:report:customer   # Generate customer HTML report
npm run py:report:customer:json  # Generate JSON only

# EXPORTS
npm run py:export:tableau    # Export for Tableau (last 90 days)

# TESTING
npm run py:test             # Run analytics tests
npm run py:test:verbose     # Detailed test output

# DATABASE
npm run db:check-schema     # Check timestamp columns
npm run py:query            # Natural language queries

# VIEW LOGS
npm run py:logs             # Tail daily sync logs
```

---

## 🎉 Project Status Summary

### ✅ What's Production-Ready

1. **Data Pipeline**
   - Daily automated sync (cron + GitHub Actions)
   - Historical backfill capability
   - Data validation (7 health checks)
   - Composite primary key (no duplicates)
   - Timezone-safe (TIMESTAMPTZ)

2. **Analytics**
   - Sensor health monitoring
   - After-hours waste detection
   - Anomaly detection
   - Spike analysis
   - Quick wins recommendations

3. **Reporting**
   - Customer-ready HTML reports
   - JSON exports for analysis
   - Tableau CSV exports (4 formats)
   - Natural language querying

4. **Infrastructure**
   - Neon PostgreSQL (cloud database)
   - GitHub Actions (automation)
   - Comprehensive documentation
   - Organized folder structure

### 📋 What's Well-Organized Now

- ✅ **Exports** - Dedicated `exports/tableau/` folder
- ✅ **Reports** - Clean `reports/` folder for customer deliverables
- ✅ **Python Scripts** - All in `backend/python_scripts/`
- ✅ **Documentation** - Comprehensive guides in `docs/`
- ✅ **Automation** - GitHub workflows in `.github/workflows/`

### 🔧 What Could Be Improved

1. **Archive old reports** (reports/ is 31MB)
2. **Remove unused Node.js scripts** (if Python does everything)
3. **Consolidate duplicate docs** (multiple COMPLETE.md files)
4. **Add automated backup** (export database weekly)

---

## 📞 Need Help?

**Common tasks:**
- Generate Tableau export: `npm run py:export:tableau`
- Check data health: `npm run py:validate`
- Generate report: `npm run py:report:customer`
- Query database: `npm run py:query`

**Documentation:**
- Setup: [SETUP_COMPLETE.md](SETUP_COMPLETE.md)
- GitHub: [GITHUB_GUIDE.md](GITHUB_GUIDE.md)
- Tableau: [TABLEAU_QUICK_START.md](TABLEAU_QUICK_START.md)
- Reports: [CUSTOMER_REPORTS_GUIDE.md](CUSTOMER_REPORTS_GUIDE.md)

---

**Last Updated:** February 4, 2026
**Version:** 1.0.0
**Maintainer:** Argo Energy Solutions
