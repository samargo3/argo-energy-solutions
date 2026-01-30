# Fix for CORS/Network Error

## Problem
The Eniscope API doesn't allow direct browser requests due to CORS (Cross-Origin Resource Sharing) restrictions. This is why you get a "Network Error" when trying to access data from the React app.

## Solution
A backend proxy server has been added to handle Eniscope API calls. The React app now calls the proxy server, which then calls the Eniscope API.

## How to Run

### Option 1: Run Both Servers Manually (Recommended)

**Terminal 1 - Start the API Server:**
```bash
npm run api:server
```

You should see:
```
🚀 API Server running on http://localhost:3001
```

**Terminal 2 - Start the React App:**
```bash
npm run dev
```

You should see:
```
  VITE v7.x.x  ready in xxx ms
  ➜  Local:   http://localhost:5173/
```

### Option 2: Run Both with One Command

If you have `concurrently` installed:
```bash
npm install -g concurrently
npm run dev:all
```

Or install it locally:
```bash
npm install --save-dev concurrently
npm run dev:all
```

## Verify It's Working

1. Open your browser to `http://localhost:5173`
2. Navigate to Reports → Wilson Center Report
3. Select a unit and date range
4. The data should now load without errors!

## Troubleshooting

### Port 3001 Already in Use
If you see "port 3001 already in use":
```bash
# Kill the process
lsof -ti:3001 | xargs kill -9

# Or use a different port
API_PORT=3002 npm run api:server
```

Then update `.env`:
```env
VITE_API_SERVER_URL=http://localhost:3002
```

### Still Getting Network Errors

1. **Check API Server is Running:**
   - Visit `http://localhost:3001/health` in your browser
   - Should return: `{"status":"ok","timestamp":"..."}`

2. **Check Environment Variables:**
   - Make sure `.env` has all Eniscope credentials:
     ```env
     VITE_ENISCOPE_API_URL=https://core.eniscope.com
     VITE_ENISCOPE_API_KEY=your_key
     VITE_ENISCOPE_EMAIL=your_email
     VITE_ENISCOPE_PASSWORD=your_password
     ```

3. **Check Browser Console:**
   - Open Developer Tools (F12)
   - Look for error messages in the Console tab
   - Check the Network tab to see if requests are being made

4. **Check API Server Logs:**
   - Look at the terminal running `npm run api:server`
   - You should see request logs and any error messages

## What Changed

1. **`backend/server/api-server.js`** - Added Eniscope API proxy endpoints:
   - `/api/eniscope/readings/:channelId` - Get channel readings
   - `/api/eniscope/channels` - Get channels
   - `/api/eniscope/devices` - Get devices

2. **`src/hooks/useEniscopeChannel.ts`** - Updated to call the proxy instead of Eniscope directly

3. **`vite.config.ts`** - Added proxy configuration to forward `/api` requests to the backend

## Architecture

```
Browser (React App)
    ↓
Vite Dev Server (localhost:5173)
    ↓ (proxies /api/*)
API Server (localhost:3001)
    ↓
Eniscope API (core.eniscope.com)
```

This setup avoids CORS issues because:
- Browser → Vite Dev Server (same origin)
- Vite → API Server (proxy, no CORS)
- API Server → Eniscope (server-to-server, no CORS)

## Production Deployment

For production, you'll need to:
1. Build the React app: `npm run build`
2. Serve the built files and API server together
3. Or use a reverse proxy (nginx, etc.) to route requests
