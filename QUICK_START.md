# Argo Energy Solutions - Quick Start

## ⚡ Most Common Commands

```bash
# TABLEAU EXPORTS
npm run py:export:tableau              # Generate all 4 CSV files

# REPORTS
npm run py:report:customer             # Customer HTML report

# DATA VALIDATION
npm run py:validate                    # Check data quality

# DATABASE QUERIES  
npm run py:query                       # Natural language queries

# TESTING
npm run py:test                        # Run all analytics tests

# MAINTENANCE
npm run py:cleanup:dry-run            # Preview cleanup actions
npm run py:cleanup                     # Archive old files
```

---

## 📊 Where Everything Is

### For Tableau Analysis
```
📁 exports/tableau/
   ├── tableau_daily_summary.csv      ⭐ Start here (fast)
   ├── tableau_readings.csv           (detailed, 15-min intervals)
   ├── tableau_channel_summary.csv    (metadata & stats)
   └── tableau_hourly_patterns.csv    (time-of-day patterns)
```

### For Customer Deliverables
```
📁 reports/
   ├── weekly-report-23271-*.html     # Send to customers
   └── weekly-report-23271-*.json     # For your analysis
```

### For Configuration
```
📁 Project root
   ├── .env                           # 🔐 Your secrets (NEVER commit!)
   ├── package.json                   # All npm commands
   └── requirements.txt               # Python dependencies
```

### For Documentation
```
📁 docs/
   ├── guides/integrations/
   │   └── NEON_TABLEAU_DIRECT_CONNECT.md
   ├── setup/
   └── troubleshooting/
```

---

## 🎯 Common Tasks

### 1. Export Fresh Data for Tableau

```bash
# Generate CSVs (last 90 days)
npm run py:export:tableau

# Then in Tableau:
File → Connect → Text File → Select exports/tableau/
```

**Files appear in:** `exports/tableau/`

### 2. Generate Customer Report

```bash
# Wilson Center (site 23271)
npm run py:report:customer

# Opens latest: reports/weekly-report-23271-*.html
```

**Share via:** Email attachment, Google Drive, Dropbox

### 3. Check Data Health

```bash
npm run py:validate
```

**Shows:**
- ✅ 151,742 readings
- ✅ 17 active channels
- ✅ Data quality status
- ⚠️ Any warnings

### 4. Query Database

```bash
npm run py:query

# Then ask:
"Show me total energy last week"
"Which channel uses most power?"
"What was peak demand yesterday?"
```

### 5. Clean Up Old Files

```bash
# Preview what would be cleaned
npm run py:cleanup:dry-run

# Actually perform cleanup
npm run py:cleanup
```

**Automatically archives:**
- Reports older than 90 days
- Custom exports older than 30 days
- Logs older than 30 days

---

## 📈 Project Stats

### Current Data
- **151,742 readings** in database
- **17 active channels** (Wilson Center)
- **Nov 5, 2025 → Today** (complete history)
- **~3,600 new readings** per day

### File Sizes
- Python scripts: 238 KB
- Documentation: 3.6 MB
- Tableau exports: 30.7 MB (regenerate anytime)
- Virtual env: 219 MB

### Code Quality
- ✅ 18 production Python scripts
- ✅ 7-module analytics suite
- ✅ Comprehensive test coverage
- ✅ Data validation passing

---

## 🔐 Security Reminders

### NEVER Commit
- ❌ `.env` file
- ❌ Database credentials
- ❌ API keys
- ❌ Customer financial data

### Safe to Commit
- ✅ Python scripts
- ✅ Documentation
- ✅ GitHub workflows
- ✅ Small test data
- ✅ Empty folder structure

### Safe to Share (Exports)
- ✅ Tableau CSV files
- ✅ Customer HTML reports
- ✅ JSON analytics data

**Use encrypted sharing** for customer reports (Google Drive with access control, encrypted email)

---

## 📞 Get Help

### Check Status
```bash
npm run py:validate              # Database health
npm run py:test                  # Analytics tests
npm run py:cleanup:dry-run       # Disk usage
```

### Documentation
- **Quick Start:** This file
- **Full Organization:** [PROJECT_ORGANIZATION.md](PROJECT_ORGANIZATION.md)
- **Tableau:** [TABLEAU_QUICK_START.md](TABLEAU_QUICK_START.md)
- **GitHub:** [GITHUB_GUIDE.md](GITHUB_GUIDE.md)

### Common Issues

**"No Tableau files"**
→ Run: `npm run py:export:tableau`
→ Check: `exports/tableau/` folder

**"Validation warnings"**
→ Usually informational
→ See validation output for details

**"Can't connect to database"**
→ Check `.env` has DATABASE_URL
→ Test: `npm run py:query`

---

## 🎉 You're Ready!

Your project is:
- ✅ Well-organized
- ✅ Well-documented
- ✅ Production-ready
- ✅ Easy to maintain

**Most common workflow:**
1. `npm run py:export:tableau` (weekly)
2. Open Tableau → Refresh data source
3. `npm run py:report:customer` (weekly)
4. Email report to customer

**That's it!** Everything else runs automatically (daily sync via cron or GitHub Actions).

---

**Last Updated:** February 4, 2026
**Version:** 1.0.0
