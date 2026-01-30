# Setup Checklist ✅

Use this checklist to track your progress setting up the SQLite data pipeline.

## Prerequisites
- [ ] Node.js installed (`node --version`)
- [ ] npm installed (`npm --version`)
- [ ] Eniscope API credentials available

## Installation
- [ ] Run `npm install` successfully
- [ ] Verify dependencies installed (check `node_modules/` exists)
- [ ] Confirm `.env` file has correct Eniscope API credentials

## Database Setup
- [ ] Run `npm run ingest:full` successfully
- [ ] Database file created at `data/eniscope.db`
- [ ] Run `npm run db:check` and see statistics
- [ ] Verify organizations, devices, channels, and readings are present

## API Server
- [ ] Start API server: `npm run api:server`
- [ ] Server running on `http://localhost:3001`
- [ ] Test health endpoint: `curl http://localhost:3001/health`
- [ ] See expected JSON response

## React App
- [ ] Start React dev server: `npm run dev`
- [ ] App loads in browser
- [ ] No console errors related to API connection
- [ ] Can import and use hooks from `useStoredEnergyData.ts`

## Testing
- [ ] Test `useStoredChannels()` hook
- [ ] Test `useStoredAggregatedReadings()` hook
- [ ] Test `useStoredEnergyStatistics()` hook
- [ ] Verify data displays correctly in components

## Optional: Scheduling
- [ ] Set up cron job for incremental ingestion
- [ ] Test incremental ingestion: `npm run ingest:incremental`
- [ ] Verify new data appears in database

## Documentation
- [ ] Read `OPTION_2_QUICK_START.md`
- [ ] Reviewed `OPTION_2_SETUP_COMPLETE.md`
- [ ] Understand architecture from `DATA_PIPELINE_GUIDE.md`

---

**Status:** Track your progress by checking off items as you complete them!

**Next:** Once all items are checked, you're ready to build on top of the stored data pipeline! 🎉
