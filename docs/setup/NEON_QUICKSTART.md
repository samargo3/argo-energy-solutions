# Neon Setup Quick Reference

## 5-Minute Setup

### 1. Sign Up for Neon
```
1. Go to: https://neon.tech
2. Click "Sign Up" → "Continue with GitHub"
3. Create project: "argo-energy-production"
4. Choose region: US East (Ohio) or closest to you
5. Copy the connection string (looks like this):
   postgresql://user:pass@ep-xxx.us-east-2.aws.neon.tech/neondb
```

### 2. Add to .env File
```bash
# Open .env and add:
DATABASE_URL=postgresql://your-connection-string-here
```

### 3. Run Automated Setup
```bash
# This installs dependencies, tests connection, creates tables, loads data
bash backend/scripts/database/neon-quickstart.sh
```

**That's it!** The script will guide you through everything.

---

## Manual Setup (Alternative)

If you prefer step-by-step:

```bash
# 1. Install PostgreSQL client
npm install pg

# 2. Test connection
npm run db:test-neon

# 3. Create tables
npm run db:setup

# 4. Load data (choose one):
# Option A: Migrate from SQLite
npm run db:migrate:sqlite-to-postgres

# Option B: Pull fresh from API
npm run ingest:full -- --db postgres --days 90

# 5. Verify
npm run db:test-neon
```

---

## Daily Use

### Generate Reports
```bash
npm run report:weekly -- --site 23271 --db postgres
```

### Sync New Data
```bash
npm run ingest:incremental -- --db postgres
```

### Check Database
```bash
npm run db:test-neon
```

---

## Enable TimescaleDB (Recommended)

For 10-100× faster queries on time-series data:

1. Go to https://console.neon.tech
2. Open your project → SQL Editor
3. Run:
```sql
CREATE EXTENSION IF NOT EXISTS timescaledb;
SELECT create_hypertable('readings', 'timestamp', if_not_exists => TRUE);
```

---

## Set Up Daily Sync

Add to crontab (runs every morning at 6 AM):

```bash
crontab -e

# Add this line:
0 6 * * * cd /Users/sargo/cursor-repo/projects/argo-energy-solutions && npm run ingest:incremental -- --db postgres >> logs/sync.log 2>&1
```

---

## Free Tier Limits

- **Storage:** 3 GB (enough for 5-10 customers for 1-2 years)
- **Compute:** 191.9 hours/month (plenty)
- **Data Transfer:** 5 GB/month
- **Backups:** 7 days retention

**Monitor usage:** https://console.neon.tech → Usage tab

---

## Troubleshooting

### Connection Failed
```bash
# Check DATABASE_URL is correct
grep DATABASE_URL .env

# Test manually
npm run db:test-neon
```

### Tables Not Found
```bash
# Create schema
npm run db:setup
```

### No Data
```bash
# Pull from API
npm run ingest:full -- --db postgres --days 90
```

---

## Next Steps

1. ✅ Complete setup (see above)
2. ✅ Generate test report: `npm run report:weekly -- --site 23271 --db postgres`
3. ✅ Set up daily sync (crontab)
4. ✅ Enable TimescaleDB
5. ✅ Add more customers

---

## Need Help?

- **Full Guide:** `docs/setup/NEON_SETUP_GUIDE.md`
- **Neon Docs:** https://neon.tech/docs
- **Support:** https://discord.gg/neon

---

## Summary

| Step | Command | Time |
|------|---------|------|
| Sign up | https://neon.tech | 2 min |
| Add to .env | `DATABASE_URL=...` | 1 min |
| Run setup | `bash backend/scripts/database/neon-quickstart.sh` | 2 min |
| **Total** | | **5 min** |

**Then you're running on cloud PostgreSQL!** 🚀
