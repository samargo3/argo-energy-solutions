# Option 2: Quick Start Guide 🚀

Get your SQLite data pipeline up and running in 5 minutes!

## Prerequisites

- Node.js installed
- Eniscope API credentials

## Step-by-Step Setup

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure Environment

Create or update `.env` file:

```env
VITE_ENISCOPE_API_URL=https://core.eniscope.com
VITE_ENISCOPE_API_KEY=your_api_key
VITE_ENISCOPE_EMAIL=your_email
VITE_ENISCOPE_PASSWORD=your_password
```

### 3. Ingest Data

```bash
npm run ingest:full
```

Wait for completion. You should see:
```
✅ Ingested X organizations
✅ Ingested X devices
✅ Ingested X channels
✅ Processed X readings
```

### 4. Verify Database

```bash
npm run db:check
```

You should see database statistics and record counts.

### 5. Start API Server

**In a new terminal window:**

```bash
npm run api:server
```

You should see:
```
🚀 API Server running on http://localhost:3001
```

### 6. Use in React

The hooks are ready to use! Example:

```typescript
import { useStoredChannels, useStoredAggregatedReadings } from './hooks/useStoredEnergyData';

function MyComponent() {
  const { data: channels } = useStoredChannels();
  const { data: readings } = useStoredAggregatedReadings(
    123, // channelId
    '2024-01-01T00:00:00Z',
    '2024-01-31T23:59:59Z',
    'day'
  );
  
  // Use the data...
}
```

## Running Both Servers

You'll need **two terminal windows**:

**Terminal 1 - React Dev Server:**
```bash
npm run dev
```

**Terminal 2 - API Server:**
```bash
npm run api:server
```

## Troubleshooting

### "Database not found"
→ Run `npm run ingest:full`

### "Cannot connect to API server"
→ Make sure `npm run api:server` is running

### "No data in database"
→ Check `npm run db:check` and verify ingestion completed

### API server won't start
→ Check if port 3001 is already in use
→ Try: `API_PORT=3002 npm run api:server`

## Next Steps

- Set up scheduled ingestion: `npm run ingest:incremental` (hourly via cron)
- Build dashboards using the stored data hooks
- See `OPTION_2_SETUP_COMPLETE.md` for full documentation

---

**That's it!** You now have a working data pipeline. 🎉
