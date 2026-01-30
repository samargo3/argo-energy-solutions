# How to Access the Wilson Center Report

## Quick Start

### 1. Open Terminal
Open Terminal (or Command Prompt on Windows) and navigate to the project:

```bash
cd /Users/sargo/argo-energy-solutions
```

### 2. Install Dependencies (First Time Only)
```bash
npm install
```

### 3. Check Environment Variables
Make sure you have a `.env` file with your Eniscope credentials:

```env
VITE_ENISCOPE_API_URL=https://core.eniscope.com
VITE_ENISCOPE_API_KEY=your_api_key_here
VITE_ENISCOPE_EMAIL=your_email@example.com
VITE_ENISCOPE_PASSWORD=your_password_here
```

### 4. Start the Web Server
```bash
npm run dev
```

### 5. Open Your Browser
Go to: **http://localhost:5173**

### 6. Access the Report
- Click **"Reports"** in the top menu
- Click **"Generate Report"** on the Wilson Center card
- OR go directly to: **http://localhost:5173/reports/wilson-center**

## What You'll See

1. **Reports Page** (`/reports`)
   - Overview of available reports
   - Click "Generate Report" for Wilson Center

2. **Wilson Center Report Page** (`/reports/wilson-center`)
   - Unit selector (choose from 9 units)
   - Date range picker
   - Resolution selector
   - Anomaly detection results
   - Equipment health status
   - Recommendations

## Troubleshooting

### Port Already in Use
If you see "port 5173 already in use":
```bash
# Kill the process using port 5173
lsof -ti:5173 | xargs kill -9

# Or use a different port
npm run dev -- --port 3000
```

### Can't Find Reports Link
- Hard refresh: `Cmd+Shift+R` (Mac) or `Ctrl+Shift+R` (Windows)
- Check the URL: `http://localhost:5173/reports`
- Or go directly: `http://localhost:5173/reports/wilson-center`

### API Errors
- Verify your `.env` file has correct credentials
- Check that the Eniscope API is accessible
- Review error messages in the browser console (F12)

## Alternative: Command Line Scripts

If you prefer command-line tools, you can also use:

```bash
# Analyze Wilson Center data via command line
npm run analyze:wilson

# Explore available channels
npm run explore:channels
```

These scripts generate JSON and Markdown reports in the `data/` directory.

## Next Steps

Once you have the web app running:
1. Select a unit from the dropdown
2. Choose a date range
3. Click to analyze
4. Review anomalies and recommendations

For detailed instructions, see `WILSON_CENTER_REPORT_GUIDE.md`
