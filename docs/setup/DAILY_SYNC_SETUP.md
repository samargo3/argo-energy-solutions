# Daily Sync Setup Guide

Automated daily synchronization of Eniscope energy data to your Neon PostgreSQL database.

---

## ✅ Quick Setup (3 Steps)

### 1. Test Manual Sync

```bash
# Test the daily sync script
npm run py:sync

# View the log
npm run py:logs
```

### 2. Set Up Automated Sync

**Option A: Interactive Setup (Recommended)**
```bash
npm run py:setup-cron
```

**Option B: Manual Setup**
```bash
crontab -e
```

Add this line:
```
0 6 * * * /Users/sargo/cursor-repo/projects/argo-energy-solutions/backend/python_scripts/daily_sync.sh
```

### 3. Verify

```bash
# Check cron jobs
crontab -l

# Monitor logs
tail -f logs/daily_sync.log
```

---

## 📅 How It Works

### Daily Sync Script

**Location:** `backend/python_scripts/daily_sync.sh`

**What it does:**
1. Activates Python virtual environment
2. Runs ingestion for last 2 days (handles late data)
3. Logs results to `logs/daily_sync.log`
4. Handles errors gracefully

**Schedule:** Runs at 6:00 AM daily (configurable)

### Data Fetched

- **Site:** Wilson Center (ID: 23271)
- **Channels:** 17 active energy meters
- **Interval:** 15-minute readings
- **Days:** Last 2 days (to catch any late-arriving data)

---

## 🎯 Available Commands

### Sync Operations

```bash
# Run manual sync (test)
npm run py:sync

# Run one-time ingestion (1 day)
npm run py:ingest

# Run full historical load (90 days)
npm run py:ingest:full
```

### Monitoring

```bash
# View live logs
npm run py:logs

# View last 50 lines
tail -n 50 logs/daily_sync.log

# Check database
npm run db:test-neon
```

### Cron Management

```bash
# Interactive cron setup
npm run py:setup-cron

# View current cron jobs
crontab -l

# Edit cron jobs
crontab -e

# Remove all cron jobs (careful!)
crontab -r
```

---

## ⏰ Cron Schedule Examples

```bash
# Every day at 6:00 AM (default)
0 6 * * * /path/to/daily_sync.sh

# Every 4 hours
0 */4 * * * /path/to/daily_sync.sh

# Twice daily (8 AM and 8 PM)
0 8,20 * * * /path/to/daily_sync.sh

# Every hour during business hours (9 AM - 5 PM)
0 9-17 * * * /path/to/daily_sync.sh

# Every 30 minutes
*/30 * * * * /path/to/daily_sync.sh
```

---

## 📊 Expected Results

### Successful Sync

```
========================================
🕐 Daily sync started: Tue Feb  3 12:51:26 EST 2026
🌐 Eniscope → PostgreSQL Data Ingestion
📊 Site ID: 23271
📅 Days to fetch: 2
✅ Authenticated with Eniscope
✅ Organization: Site 23271
✅ Found 20 channels
✅ 17 valid channels stored
📥 Fetching readings...
   [1/17] RTU-1_WCDS_Wilson Ctr... ✅ 192 readings
   [2/17] RTU-2_WCDS_Wilson Ctr... ✅ 192 readings
   ...
✅ Ingestion complete!
   Total readings: 3,264
   Duration: 82.7s
📊 Total readings in database: 151,742
✅ Daily sync completed successfully: Tue Feb  3 12:52:54 EST 2026
```

### Normal Behavior

- **3 channels fail** (WCDS Reference, Argo Home Test, Air Sense) - these are test channels
- **Duration:** ~80-90 seconds
- **New readings:** ~3,000-3,500 per day (17 channels × 192 intervals)

---

## 🔍 Troubleshooting

### Check if Cron Job is Running

```bash
# View cron jobs
crontab -l

# Check system log (macOS)
log show --predicate 'process == "cron"' --last 1h
```

### Common Issues

#### 1. Cron Job Not Running

**Problem:** No new entries in `logs/daily_sync.log`

**Solutions:**
- Verify cron job exists: `crontab -l`
- Check script permissions: `ls -l backend/python_scripts/daily_sync.sh`
- Test manually: `npm run py:sync`

#### 2. Permission Denied

**Problem:** `Permission denied` error

**Solution:**
```bash
chmod +x backend/python_scripts/daily_sync.sh
```

#### 3. Virtual Environment Not Found

**Problem:** `venv/bin/activate: No such file or directory`

**Solution:**
```bash
cd /Users/sargo/cursor-repo/projects/argo-energy-solutions
python3 -m venv venv
source venv/bin/activate
pip install -r backend/python_scripts/requirements.txt
```

#### 4. Authentication Failed

**Problem:** `401 Unauthorized` or `Authentication failed`

**Solution:**
- Check `.env` file has correct credentials
- Verify `ENISCOPE_API_KEY`, `ENISCOPE_EMAIL`, `ENISCOPE_PASSWORD`
- Test manual ingestion: `npm run py:ingest`

#### 5. Database Connection Failed

**Problem:** `could not connect to server`

**Solution:**
- Check `DATABASE_URL` in `.env`
- Verify Neon database is active
- Test connection: `npm run db:test-neon`

### View Detailed Logs

```bash
# Last 100 lines with timestamps
tail -n 100 logs/daily_sync.log

# Search for errors
grep "❌\|Error\|Failed" logs/daily_sync.log

# Watch in real-time
tail -f logs/daily_sync.log
```

---

## 📈 Monitoring Best Practices

### 1. Regular Log Review

```bash
# Weekly review
grep "✅ Daily sync completed" logs/daily_sync.log | tail -n 7

# Count successful vs failed syncs
echo "Successful: $(grep -c '✅ Daily sync completed' logs/daily_sync.log)"
echo "Failed: $(grep -c '❌ Daily sync failed' logs/daily_sync.log)"
```

### 2. Database Growth Tracking

```bash
# Check total readings
npm run db:test-neon

# Expected growth: ~3,000-3,500 readings per day
```

### 3. Set Up Alerts (Optional)

Create a monitoring script that emails you on failures:

```bash
#!/bin/bash
# Check last sync status
if tail -n 5 logs/daily_sync.log | grep -q "❌ Daily sync failed"; then
    echo "Daily sync failed!" | mail -s "Argo Alert: Sync Failed" your@email.com
fi
```

---

## 🔄 Backup & Recovery

### Backup Strategy

1. **Neon handles database backups** (automatic point-in-time recovery)
2. **Local logs:** Keep `logs/` directory backed up
3. **Re-ingestion:** Can always re-fetch data from Eniscope API

### Recovery from Missed Syncs

```bash
# If sync missed for 7 days, run:
source venv/bin/activate
python backend/python_scripts/ingest_to_postgres.py --site 23271 --days 7

# Or use npm:
# (modify package.json script temporarily)
```

---

## 📝 Summary

### ✅ What You Have Now

- ✅ **Automated daily sync** at 6:00 AM
- ✅ **Logging system** in `logs/daily_sync.log`
- ✅ **Easy commands** via npm scripts
- ✅ **Robust error handling**
- ✅ **2-day fetch** (catches late data)

### 🎯 Next Steps

1. **Monitor for 1 week** - Verify daily syncs work
2. **Review logs weekly** - Check for patterns/issues
3. **Enable TimescaleDB** - Better performance for time-series queries (optional)
4. **Build analytics** - Start querying your data!

---

## 🆘 Need Help?

- **Test manually:** `npm run py:sync`
- **View logs:** `npm run py:logs`
- **Check database:** `npm run db:test-neon`
- **Re-run setup:** `npm run py:setup-cron`

---

## 📚 Related Documentation

- [Neon Setup Guide](NEON_SETUP_GUIDE.md)
- [Python Scripts README](../../backend/python_scripts/README.md)
- [Python Migration Plan](../../PYTHON_MIGRATION_PLAN.md)
