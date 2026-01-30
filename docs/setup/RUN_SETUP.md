# Setup Execution Guide

Due to system permission restrictions, please run these commands manually in your terminal.

## Step 1: Install Dependencies

Open your terminal and run:

```bash
cd /Users/sargo/argo-energy-solutions
npm install
```

This will install:
- `sqlite` - SQLite wrapper
- `sqlite3` - SQLite3 bindings
- `express` - API server framework
- `cors` - CORS middleware
- `@types/express` and `@types/cors` - TypeScript types

**Expected output:** Packages should install successfully. If you see errors, make sure you have Node.js and npm properly installed.

## Step 2: Verify Environment Variables

Make sure your `.env` file exists and has:

```env
VITE_ENISCOPE_API_URL=https://core.eniscope.com
VITE_ENISCOPE_API_KEY=your_actual_api_key
VITE_ENISCOPE_EMAIL=your_actual_email
VITE_ENISCOPE_PASSWORD=your_actual_password
```

**Note:** Replace the placeholder values with your actual Eniscope API credentials.

## Step 3: Run Initial Data Ingestion

```bash
npm run ingest:full
```

**What this does:**
- Creates SQLite database at `data/eniscope.db`
- Fetches all organizations from Eniscope API
- Fetches all devices for each organization
- Fetches all channels for each organization
- Fetches readings for the last 30 days for all channels

**Expected output:**
```
🔄 Initializing database connection...
✅ Database initialized
✅ Database schema created/verified
📥 Ingesting organizations...
✅ Ingested X organizations
📥 Found X organizations, ingesting devices...
📥 Ingesting channels...
📥 Found X channels, ingesting readings...
✅ Processed X readings...

========================================
📊 INGESTION SUMMARY
========================================
Organizations: X
Devices: X
Channels: X
Readings: X
Errors: 0
========================================
```

**Time:** This may take several minutes depending on:
- Number of organizations/devices/channels
- Amount of historical data
- API response times

## Step 4: Verify Database

```bash
npm run db:check
```

**Expected output:**
```
🔍 Checking database status...

✅ Database file found: /path/to/data/eniscope.db
   Size: X.XX MB

📊 Database Statistics:

Tables found: 4
  - channels: X records
  - devices: X records
  - organizations: X records
  - readings: X records

📁 Organizations: X
📱 Devices: X
📡 Channels: X
📈 Readings: X,XXX
   Date Range: YYYY-MM-DD to YYYY-MM-DD
   Days of data: X

✅ Database check complete!
```

## Step 5: Start API Server

**In a new terminal window** (keep the first one open):

```bash
cd /Users/sargo/argo-energy-solutions
npm run api:server
```

**Expected output:**
```
🚀 API Server running on http://localhost:3001
📊 Endpoints available:
   GET /health
   GET /api/channels
   GET /api/channels/:channelId/readings
   GET /api/channels/:channelId/readings/aggregated
   GET /api/channels/:channelId/statistics
   GET /api/organizations/:organizationId/summary
   GET /api/channels/:channelId/readings/latest
   GET /api/channels/:channelId/range
```

**Keep this terminal open** - the API server needs to keep running.

## Step 6: Test the API (Optional)

In another terminal, test the health endpoint:

```bash
curl http://localhost:3001/health
```

Should return:
```json
{"status":"ok","timestamp":"2024-01-09T..."}
```

## Step 7: Start React App

**In yet another terminal window:**

```bash
cd /Users/sargo/argo-energy-solutions
npm run dev
```

The React app will start on `http://localhost:5173` (or similar).

## Troubleshooting

### npm install fails
- Make sure Node.js is installed: `node --version`
- Make sure npm is installed: `npm --version`
- Try: `npm cache clean --force` then retry

### Ingestion fails with authentication error
- Check your `.env` file has correct credentials
- Verify API credentials are valid
- Check API URL is correct

### Database not found
- Make sure Step 3 (ingestion) completed successfully
- Check `data/eniscope.db` file exists
- Run `npm run db:check` to verify

### API server won't start
- Check if port 3001 is already in use
- Try: `lsof -i :3001` to see what's using it
- Use different port: `API_PORT=3002 npm run api:server`

### "Cannot connect to API server" in React
- Make sure API server is running (Step 5)
- Check the API server terminal for errors
- Verify `VITE_STORED_DATA_API_URL` in `.env` matches the server port

## What's Next?

Once everything is running:

1. ✅ **Use the hooks in React components** - Import from `useStoredEnergyData.ts`
2. ✅ **Set up scheduled ingestion** - Add cron job for `npm run ingest:incremental`
3. ✅ **Build dashboards** - Use stored data instead of direct API calls
4. ✅ **Monitor data freshness** - Run `npm run db:check` regularly

## Quick Reference

```bash
# Data ingestion
npm run ingest:full          # Full historical data
npm run ingest:incremental   # Only new data (faster)

# Database management
npm run db:check             # Check status

# API server
npm run api:server           # Start server
npm run api:dev              # Development mode (auto-reload)

# React app
npm run dev                  # Start React dev server
```

---

**Ready to go!** Follow the steps above in order. If you encounter any issues, check the troubleshooting section or review the detailed documentation in `OPTION_2_SETUP_COMPLETE.md`.
