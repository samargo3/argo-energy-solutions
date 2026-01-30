# API Configuration Guide

## ✅ API Endpoints Configured for Eniscope/Best.Energy

Your API integration has been configured based on your **Wilson Center** data structure.

## 🔧 Configuration Overview

### Data Format Identified

From your `wilson-center-analysis.json`, we can see you're using **Eniscope meters** with this structure:

```json
{
  "channels": [
    {
      "channel": "RTU-2_WCDS_Wilson Ctr",
      "channelId": "162119",
      "rawReadings": [
        {
          "ts": 1764565200,      // Unix timestamp
          "E": 1290.08,           // Energy (Wh)
          "P": 1290.12,           // Power (W)
          "V": 120.31,            // Voltage (V)
          "I": 5.84,              // Current (A)
          "PF": 0.60              // Power Factor
        }
      ]
    }
  ]
}
```

### API Endpoints Configured

#### Python Scripts (`backend/python_reports/scripts/fetch_bestenergy_data.py`)

```python
# Primary endpoints tried (in order):
'/v1/readings/{customer_id}'
'/readings/{customer_id}'
'/api/v1/readings/{customer_id}'
'/v1/channels/{customer_id}/readings'
'/channels/{customer_id}/readings'
'/v1/sites/{customer_id}/data'
'/sites/{customer_id}/readings'
'/v1/devices/{customer_id}/readings'
'/data/{customer_id}'
```

**Parameters:**
- `start`: Unix timestamp (e.g., `1764565200`)
- `end`: Unix timestamp
- `resolution`: `'3600'` for hourly, `'86400'` for daily

#### React App (`src/services/api/bestEnergyApi.ts`)

**Functions configured:**
1. `getCustomerEnergyConsumption()` - Fetch channel readings
2. `getSiteEnergyConsumption()` - Fetch site-level data
3. `getGroupedEnergyConsumption()` - Aggregated data (day/week/month)

**Features:**
- ✅ Automatic date-to-Unix timestamp conversion
- ✅ Wh to kWh conversion (divides by 1000)
- ✅ Fallback endpoint patterns
- ✅ Transform Eniscope format to app format

## 🚀 Quick Start

### Option 1: Use Existing Data (No API Needed)

Since your Wilson Center data is already available as JSON:

```bash
cd python_reports
python use_existing_wilson_data.py \
  --json ../data/wilson-center-analysis.json \
  --baseline-start 2025-12-01 \
  --baseline-end 2025-12-15 \
  --report-start 2025-12-16 \
  --report-end 2025-12-31
```

### Option 2: Fetch from API (When Available)

1. **Set environment variables:**

```bash
# In .env file:
VITE_BEST_ENERGY_API_URL=https://api.eniscope.com
VITE_BEST_ENERGY_API_KEY=your_api_key_here
```

2. **Run full pipeline:**

```bash
cd python_reports
python full_pipeline.py \
  --customer-id "wilson-center" \
  --baseline-start 2025-12-01 \
  --baseline-end 2025-12-15 \
  --report-start 2025-12-16 \
  --report-end 2025-12-31
```

## 🔍 How the Integration Works

### 1. Data Fetching

The `fetch_bestenergy_data.py` script:
- Converts your date ranges to Unix timestamps
- Tries multiple endpoint patterns (Eniscope variations)
- Requests hourly resolution data (`resolution=3600`)

### 2. Data Transformation

Eniscope format → VEM format:

```python
# Eniscope Reading:
{"ts": 1764565200, "E": 1290.08, "P": 1290.12, "V": 120.31, "I": 5.84, "PF": 0.60}

# Transformed to VEM:
{
  "Timestamp": "2025-12-01 00:00:00",
  "Usage_kWh": 1.29,  # E/1000
  "Asset_Name": "RTU-2_WCDS_Wilson Ctr"
}
```

### 3. React App Integration

The React app (`src/services/api/bestEnergyApi.ts`):
- Uses same endpoint patterns
- Automatically converts dates ↔ Unix timestamps
- Transforms Eniscope response to app's data structure
- Handles pagination and grouping

## 📊 Asset Names (From Your Data)

Your Wilson Center has these channels:
- `RTU-2_WCDS_Wilson Ctr`
- `CDPK_Kitchen Main Panel(s)_WCDS_Wilson Ctr`
- `RTU-1_WCDS_Wilson Ctr`
- `1st Floor Panels_WCDS_Wilson Ctr`
- `2nd Floor Panels_WCDS_Wilson Ctr`
- And more...

## 🔐 Getting Your API Key

1. Log into Best.Energy portal
2. Navigate to **Settings** → **API Keys**
3. Generate new API key
4. Copy to `.env` file

## 📝 Testing the API

### Test API Connection (React)

Visit: `http://localhost:5173/api-test` after starting the app:

```bash
npm run dev
```

### Test API Connection (Python)

```bash
cd python_reports
python fetch_bestenergy_data.py \
  --customer-id "wilson-center" \
  --start-date 2025-12-01 \
  --end-date 2025-12-31 \
  --output test_data.csv
```

## 🐛 Troubleshooting

### Issue: "No data returned"

**Check:**
1. Is your API key valid?
2. Is the customer ID correct?
3. Does the date range have data in the portal?
4. Is the API endpoint URL correct?

### Issue: "Unauthorized" or "403"

**Solutions:**
- Verify API key is in `.env`
- Check API key permissions in portal
- Ensure `Authorization: Bearer {key}` header is sent

### Issue: "Wrong data format"

**Check:**
- Look at the raw API response
- Update transformation logic in `_transform_to_vem_format()`
- Check if Eniscope firmware version changed format

## 📖 Additional Resources

- **Portal Data Guide:** See `HOW_TO_ACCESS_PORTAL_DATA.md`
- **VEM Report Guide:** See `backend/python_reports/README.md`
- **Quick Start:** See `backend/python_reports/QUICK_START.md`
- **Ingress Setup:** See `Generic_ingress_instructions.txt`

## 🎯 Next Steps

1. ✅ **Configured** - API endpoints are ready
2. 🔄 **Test with existing data** - Run `use_existing_wilson_data.py`
3. 🔑 **Add API key** - When ready to fetch live data
4. 📊 **Generate reports** - Use full pipeline

---

**Questions?** Check the documentation files or inspect the configured code:
- Python: `/backend/python_reports/scripts/fetch_bestenergy_data.py`
- React: `/src/services/api/bestEnergyApi.ts`

