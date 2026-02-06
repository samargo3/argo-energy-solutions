# ✅ Daily Sync Ready!

Your automated daily data synchronization is set up and ready to go!

---

## 🚀 Quick Start

### Set Up Automated Sync (One Time)

```bash
npm run py:setup-cron
```

This will schedule daily sync at 6:00 AM.

---

## 📋 Daily Commands

```bash
# Test manual sync
npm run py:sync

# View live sync logs
npm run py:logs

# Check database status
npm run db:test-neon
```

---

## 📊 What Happens Daily

**At 6:00 AM every day:**

1. ✅ Connects to Eniscope API
2. ✅ Fetches last 2 days of data (17 channels)
3. ✅ Stores ~3,000-3,500 readings in Neon PostgreSQL
4. ✅ Logs results to `logs/daily_sync.log`
5. ✅ Takes ~80-90 seconds

**Result:** Always have fresh Wilson Center energy data ready for analysis!

---

## 🔍 Monitor Progress

```bash
# View last sync result
tail -n 20 logs/daily_sync.log

# Count total readings in database
npm run db:test-neon

# Watch sync in real-time
npm run py:logs
```

---

## 📅 Expected Growth

| Timeline | Readings | Storage |
|----------|----------|---------|
| 1 day    | ~3,500   | ~350 KB |
| 1 week   | ~24,000  | ~2.4 MB |
| 1 month  | ~100,000 | ~10 MB  |
| 1 year   | ~1.2M    | ~120 MB |

**Your free Neon tier:** 512 MB storage (enough for ~5 years!)

---

## ⚙️ Change Schedule

Edit your cron job:

```bash
crontab -e
```

**Common schedules:**

```bash
# Every day at 6 AM (default)
0 6 * * * /Users/sargo/cursor-repo/projects/argo-energy-solutions/backend/python_scripts/daily_sync.sh

# Every 4 hours
0 */4 * * * /Users/sargo/cursor-repo/projects/argo-energy-solutions/backend/python_scripts/daily_sync.sh

# Twice daily (8 AM and 8 PM)
0 8,20 * * * /Users/sargo/cursor-repo/projects/argo-energy-solutions/backend/python_scripts/daily_sync.sh
```

---

## 🔧 Manual Operations

### One-Time Ingest

```bash
# Last 1 day
npm run py:ingest

# Last 90 days (full historical)
npm run py:ingest:full

# Custom days (e.g., 7 days)
source venv/bin/activate
python backend/python_scripts/ingest_to_postgres.py --site 23271 --days 7
```

### Verify Setup

```bash
# Check cron job exists
crontab -l | grep daily_sync

# Test script runs
npm run py:sync

# Check database has data
npm run db:test-neon
```

---

## ✅ Current Status

### Completed ✓

- [x] Python 3.9.6 installed
- [x] Virtual environment created (`venv/`)
- [x] Dependencies installed (pandas, psycopg2, requests, etc.)
- [x] Python ingestion script working (`ingest_to_postgres.py`)
- [x] Daily sync script created (`daily_sync.sh`)
- [x] Cron setup helper created (`setup_cron.sh`)
- [x] Logging system configured (`logs/daily_sync.log`)
- [x] npm shortcuts added (`py:sync`, `py:logs`, etc.)
- [x] 151,742 readings loaded in Neon PostgreSQL
- [x] Script tested successfully (17 readings added)

### Ready to Go 🚀

- [ ] Run `npm run py:setup-cron` to enable automation
- [ ] Monitor for 1 week
- [ ] Start building analytics!

---

## 🎯 Next Steps

### 1. Enable Automation (Now)

```bash
npm run py:setup-cron
```

### 2. Monitor for 1 Week

Check logs daily:
```bash
npm run py:logs
```

### 3. Start Using Your Data

Your data is now continuously updated and ready for:
- Weekly reports
- Anomaly detection
- Cost analysis
- Energy optimization
- Predictive analytics

---

## 📚 Documentation

- **Full Guide:** [docs/setup/DAILY_SYNC_SETUP.md](docs/setup/DAILY_SYNC_SETUP.md)
- **Python Scripts:** [backend/python_scripts/README.md](backend/python_scripts/README.md)
- **Neon Database:** [docs/setup/NEON_SETUP_GUIDE.md](docs/setup/NEON_SETUP_GUIDE.md)
- **Troubleshooting:** See [DAILY_SYNC_SETUP.md](docs/setup/DAILY_SYNC_SETUP.md#troubleshooting)

---

## 🆘 Quick Help

**Problem?**

1. Test manually: `npm run py:sync`
2. Check logs: `tail -n 50 logs/daily_sync.log`
3. Verify database: `npm run db:test-neon`
4. Re-run setup: `npm run py:setup-cron`

**Everything working?**

Your Wilson Center data is now automatically synced every day! 🎉

---

**Ready to set up automation?**

```bash
npm run py:setup-cron
```
