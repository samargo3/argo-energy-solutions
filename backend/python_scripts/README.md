# Python Scripts for Argo Energy Solutions

Python-based backend for data ingestion, analytics, and reporting.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Using pip
pip install -r requirements.txt

# Or using virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

Make sure your `.env` file has:
```bash
DATABASE_URL=postgresql://...  # Neon PostgreSQL connection
VITE_ENISCOPE_API_URL=https://core.eniscope.com
VITE_ENISCOPE_API_KEY=your_api_key
VITE_ENISCOPE_EMAIL=your_email
VITE_ENISCOPE_PASSWORD=your_password
```

### 3. Run Data Ingestion

```bash
# Ingest Wilson Center data (last 90 days)
python ingest_to_postgres.py --site 23271 --days 90

# Ingest just 1 day (for daily sync)
python ingest_to_postgres.py --site 23271 --days 1

# Help
python ingest_to_postgres.py --help
```

## 📁 Project Structure

```
python_scripts/
├── requirements.txt              # Python dependencies
├── ingest_to_postgres.py        # Data ingestion from Eniscope API
├── generate_weekly_report.py    # Weekly report generator
├── daily_sync.sh                # Automated daily sync script
├── setup_cron.sh                # Cron job setup helper
├── README.md                     # This file
│
├── lib/                         # Utility libraries
│   ├── stats_utils.py           # Statistical functions
│   └── date_utils.py            # Date/time utilities
│
├── config/                      # Configuration
│   └── report_config.py         # Report configuration
│
└── analytics/                   # Analytics modules
    ├── anomaly_detection.py     # Anomaly detection
    ├── after_hours_waste.py     # After-hours waste analysis
    ├── spike_detection.py       # Spike detection
    ├── sensor_health.py         # Sensor health monitoring
    └── quick_wins.py            # Quick wins recommendations
```

## 🔧 Scripts

### Data Ingestion

**`ingest_to_postgres.py`**

Pulls energy data from Eniscope API and stores in PostgreSQL.

**Features:**
- Automatic authentication with Eniscope API
- Rate limiting with exponential backoff
- Batch inserts for performance (1000 rows at a time)
- Unit conversion (Wh → kWh, W → kW)
- Duplicate prevention (unique constraint on channel_id + timestamp)
- Progress reporting

**Usage:**
```bash
# Basic usage
python ingest_to_postgres.py --site 23271 --days 90

# Arguments:
#   --site    Site/organization ID (default: 23271)
#   --days    Number of days to fetch (default: 90)
```

**Performance:**
- ~17 channels in ~5 minutes
- ~147,000 readings
- ~1,000 readings/second throughput

### Report Generation

**`generate_weekly_report.py`**

Generates comprehensive weekly energy analytics report from PostgreSQL data.

**Features:**
- Direct PostgreSQL data fetching (fast!)
- Runs all analytics modules:
  - Sensor health checks
  - After-hours waste analysis
  - Anomaly detection
  - Spike detection
  - Quick wins recommendations
- JSON output format
- Command-line interface
- Progress indicators
- Flexible date ranges

**Usage:**
```bash
# Generate report for last complete week
python generate_weekly_report.py --site 23271

# Custom date range
python generate_weekly_report.py \
  --site 23271 \
  --start 2026-01-20 \
  --end 2026-01-26 \
  --out reports/my-report.json

# Different timezone
python generate_weekly_report.py \
  --site 23271 \
  --timezone America/Los_Angeles

# Arguments:
#   --site <id>        Site organization ID (required)
#   --start <iso>      Report start date (ISO format, optional)
#   --end <iso>        Report end date (ISO format, optional)
#   --out <file>       Output file path (optional)
#   --timezone <tz>    Timezone override (default: America/New_York)
```

**Performance:**
- ~16-20 seconds for weekly report
- Fetches ~12,500 report readings + ~50,000 baseline readings
- All analytics processed in-memory
- JSON output (~10-50 KB depending on findings)

**Output Structure:**
```json
{
  "metadata": { "generatedAt", "site", "period", "baseline", ... },
  "summary": { "headline", "topRisks", "topOpportunities", "totalPotentialSavings" },
  "sections": {
    "sensorHealth": { "summary", "issues", ... },
    "afterHoursWaste": { "summary", "topMeters", ... },
    "anomalies": { "summary", "timeline", "byChannel" },
    "spikes": { "summary", "topSpikes", "byChannel" },
    "quickWins": [ ... recommendations ... ]
  },
  "charts": { ... },
  "dataQuality": { ... }
}
```

## 🧪 Testing

```bash
# Run tests (when available)
pytest tests/

# With coverage
pytest --cov=. tests/
```

## 📊 Data Flow

```
Eniscope API
    ↓ (ingest_to_postgres.py)
PostgreSQL (Neon)
    ↓ (analytics scripts - coming soon)
Reports & Insights
```

## 🔄 Daily Sync Setup

**Easy Setup (Recommended):**

```bash
# Interactive cron setup
npm run py:setup-cron

# Or run the script directly
./backend/python_scripts/setup_cron.sh
```

**Manual Test:**

```bash
# Test daily sync (fetches last 2 days)
npm run py:sync

# View logs
npm run py:logs
```

**What It Does:**
- Runs automatically at 6:00 AM daily
- Fetches last 2 days of data (catches late arrivals)
- Logs to `logs/daily_sync.log`
- Handles errors gracefully

**Full Guide:** See [docs/setup/DAILY_SYNC_SETUP.md](../../docs/setup/DAILY_SYNC_SETUP.md)

---

## 📋 Quick Reference - npm Commands

### Data Ingestion
```bash
npm run py:ingest          # Ingest 1 day (daily sync)
npm run py:ingest:full     # Ingest 90 days (historical)
```

### Report Generation
```bash
npm run py:report          # Generate Wilson Center report
npm run py:report:custom   # Custom report (add args after --)
```

### Automation & Monitoring
```bash
npm run py:sync            # Manual daily sync
npm run py:setup-cron      # Set up automated sync
npm run py:logs            # View sync logs
```

### Database
```bash
npm run db:test-neon       # Test database connection
npm run db:check           # Check database status
```

## 📦 Dependencies

Core dependencies:
- **psycopg2-binary** - PostgreSQL adapter
- **requests** - HTTP client for API calls
- **python-dotenv** - Environment variable management
- **pandas** - Data manipulation (for future analytics)
- **numpy** - Numerical computing (for analytics)

See `requirements.txt` for full list.

## 🐛 Troubleshooting

### "No module named 'psycopg2'"
```bash
pip install psycopg2-binary
```

### "DATABASE_URL not found"
Make sure `.env` file exists in project root with DATABASE_URL set.

### "Rate limited" errors
The script handles this automatically with retries. If it persists, increase the delay in the code.

### "null value in column timestamp"
This means the API returned readings without timestamps. The script filters these out automatically.

## 📝 Next Steps

See `PYTHON_MIGRATION_PLAN.md` in the project root for the roadmap of converting remaining scripts to Python.

## 🤝 Contributing

When adding new scripts:
1. Follow PEP 8 style guide
2. Add type hints
3. Include docstrings
4. Add tests in `tests/` directory
5. Update this README

## 📚 Documentation

- [Daily Sync Setup Guide](../../docs/setup/DAILY_SYNC_SETUP.md) - Automated daily data sync
- [Python Migration Plan](../../PYTHON_MIGRATION_PLAN.md) - Roadmap for Python conversion
- [Neon Setup Guide](../../docs/setup/NEON_SETUP_GUIDE.md) - PostgreSQL database setup
- [Data Storage Strategy](../../docs/guides/DATA_STORAGE_STRATEGY.md) - Architecture overview
