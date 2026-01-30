# Quick Start Guide - Wilson Center VEM Report

## 🎯 EASIEST METHOD: Use Existing Data

Since you already have Wilson Center data in JSON format, use this script:

```bash
cd python_reports
pip install -r requirements.txt

# Generate report from your existing data
python use_existing_wilson_data.py \
  --json ../data/wilson-center-analysis.json \
  --baseline-start 2025-12-01 \
  --baseline-end 2025-12-15 \
  --report-start 2025-12-16 \
  --report-end 2025-12-31 \
  --cost 0.15
```

This will:
1. ✅ Load your Wilson Center JSON data
2. ✅ Convert to CSV format
3. ✅ Generate VEM report PDF
4. ✅ No API calls needed!

---

## 🚀 Full Pipeline (When API is Ready)

### Step 1: Setup (One time)

```bash
cd python_reports
pip install -r requirements.txt
```

Make sure your `.env` file (in parent directory) has:
```env
VITE_BEST_ENERGY_API_URL=https://api.best.energy
VITE_BEST_ENERGY_API_KEY=your_api_key_here
```

### Step 2: Generate Report

#### For Wilson Center:

```bash
python full_pipeline.py \
  --customer-id wilson-center \
  --baseline-start 2024-01-01 \
  --baseline-end 2024-01-31 \
  --report-start 2024-11-01 \
  --report-end 2024-11-30 \
  --cost-per-kwh 0.12
```

#### Testing with Mock Data:

```bash
python full_pipeline.py \
  --mock \
  --baseline-start 2024-01-01 \
  --baseline-end 2024-01-31 \
  --report-start 2024-11-01 \
  --report-end 2024-11-30
```

### Output

You'll get:
- ✅ `energy_data.csv` - Raw data from API
- ✅ `VEM_Report_wilson-center_*.pdf` - Professional PDF report
- ✅ `charts/` folder - Individual chart images

## 📝 Step-by-Step Option

If you prefer to run each step separately:

### Step 1: Fetch Data from API

```bash
# Real data
python fetch_bestenergy_data.py \
  --customer-id wilson-center \
  --start-date 2024-01-01 \
  --end-date 2024-11-30 \
  --output energy_data.csv

# OR Mock data for testing
python fetch_bestenergy_data.py \
  --mock \
  --customer-id wilson-center \
  --start-date 2024-01-01 \
  --end-date 2024-11-30 \
  --output energy_data.csv
```

### Step 2: Generate Report

Edit `generate_vem_report.py` to set your dates:

```python
BASELINE_START = '2024-01-01'
BASELINE_END = '2024-01-31'
REPORT_START = '2024-11-01'
REPORT_END = '2024-11-30'
```

Then run:

```bash
python generate_vem_report.py
```

## 🔧 Customization

### Change Customer/Site

```bash
python full_pipeline.py \
  --customer-id your-site-id \
  --baseline-start 2024-01-01 \
  --baseline-end 2024-01-31 \
  --report-start 2024-11-01 \
  --report-end 2024-11-30
```

### Change Electricity Rate

```bash
python full_pipeline.py \
  --cost-per-kwh 0.15 \
  ... other args
```

### Use Different Periods

```bash
# Compare Q4 2024 vs Q4 2023
python full_pipeline.py \
  --baseline-start 2023-10-01 \
  --baseline-end 2023-12-31 \
  --report-start 2024-10-01 \
  --report-end 2024-12-31 \
  ... other args
```

## 📊 What You Get

### CSV Format (energy_data.csv)
```csv
Timestamp,Usage_kWh,Asset_Name
2024-01-01 00:00:00,125.5,RTU-1
2024-01-01 01:00:00,110.3,RTU-1
...
```

### PDF Report (VEM_Report_*.pdf)

**Page 1: Executive Summary**
- Total Savings (kWh)
- Cost Savings ($)
- Percent Reduction
- Summary narrative

**Page 2: Visual Analysis**
- Baseline vs Actual chart (with green/red fill)
- Day-of-week comparison

**Page 3: Detailed Breakdown**
- Hourly heatmap
- Asset-specific variance table

## 🐛 Troubleshooting

### API Connection Failed

```bash
# Test with mock data first
python full_pipeline.py --mock \
  --baseline-start 2024-01-01 \
  --baseline-end 2024-01-31 \
  --report-start 2024-11-01 \
  --report-end 2024-11-30
```

If mock works but real API doesn't:
1. Check `.env` file has correct API key
2. Verify customer-id is correct
3. Review API endpoint in `fetch_bestenergy_data.py`
4. Check `Core API v1.pdf` for correct endpoints

### No Data Fetched

The script tries multiple endpoint patterns:
- `/customers/{id}/consumption`
- `/v1/customers/{id}/consumption`
- `/api/v1/customers/{id}/energy`
- etc.

Check console output to see which endpoints were tried.

### Module Not Found

```bash
pip install -r requirements.txt
```

### Permission Denied

```bash
chmod +x full_pipeline.py
```

## 📖 Examples

### Monthly Comparison
```bash
python full_pipeline.py \
  --customer-id wilson-center \
  --baseline-start 2024-10-01 \
  --baseline-end 2024-10-31 \
  --report-start 2024-11-01 \
  --report-end 2024-11-30
```

### Quarterly Report
```bash
python full_pipeline.py \
  --customer-id wilson-center \
  --baseline-start 2024-01-01 \
  --baseline-end 2024-03-31 \
  --report-start 2024-04-01 \
  --report-end 2024-06-30
```

### Year-over-Year
```bash
python full_pipeline.py \
  --customer-id wilson-center \
  --baseline-start 2023-01-01 \
  --baseline-end 2023-12-31 \
  --report-start 2024-01-01 \
  --report-end 2024-12-31
```

## 🔗 Integration with React Dashboard

To connect this with your React dashboard:

1. **Run pipeline from Node.js:**
```javascript
const { exec } = require('child_process');

exec('python full_pipeline.py --mock ...', (error, stdout) => {
  if (error) {
    console.error(error);
    return;
  }
  // Report generated successfully
});
```

2. **Create API endpoint** (Express):
```javascript
app.post('/api/generate-report', async (req, res) => {
  const { customerId, baselineStart, reportStart } = req.body;
  // Run Python script
  // Return PDF path
});
```

3. **Add download button** in React:
```typescript
const handleGenerateReport = async () => {
  const response = await fetch('/api/generate-report', {
    method: 'POST',
    body: JSON.stringify({ customerId: 'wilson-center', ... })
  });
  // Download PDF
};
```

## Next Steps

1. ✅ Test with mock data
2. ✅ Configure your API credentials
3. ✅ Run with real Wilson Center data
4. ✅ Customize colors/layout if needed
5. ✅ Integrate with React dashboard (optional)

Need help? Check the main README.md for detailed documentation.

