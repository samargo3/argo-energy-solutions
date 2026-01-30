# API Endpoints - Configuration Summary

## ✅ Configured for Eniscope/Best.Energy

Your API integration is now configured to work with **Eniscope meters** used at Wilson Center.

---

## 📡 Endpoint Patterns Configured

### Python Scripts
Location: `/backend/python_reports/scripts/fetch_bestenergy_data.py`

```python
# Endpoint Priority Order (tries each until success):
[
    '/v1/readings/{customer_id}',           # ⭐ Primary
    '/readings/{customer_id}',
    '/api/v1/readings/{customer_id}',
    '/v1/channels/{customer_id}/readings',  # ⭐ Alternative
    '/channels/{customer_id}/readings',
    '/v1/sites/{customer_id}/data',
    '/sites/{customer_id}/readings',
    '/v1/devices/{customer_id}/readings',
    '/data/{customer_id}',
]
```

**Parameters Sent:**
```python
{
    'start': 1764565200,        # Unix timestamp
    'end': 1764652800,          # Unix timestamp
    'resolution': '3600',       # Hourly (3600 seconds)
    'from': 1764565200,         # Alternative param name
    'to': 1764652800,           # Alternative param name
    'startTime': 1764565200,    # Alternative param name
    'endTime': 1764652800,      # Alternative param name
}
```

### React App
Location: `/src/services/api/bestEnergyApi.ts`

```typescript
// Customer/Channel Readings
GET /v1/readings/{customerId}
GET /readings/{customerId}
GET /v1/channels/{customerId}/readings

// Site-level Data
GET /v1/sites/{siteId}/data

// Aggregated Data (with resolution)
GET /v1/readings/{customerId}?resolution=86400  // Daily
```

---

## 🔄 Data Transformation

### Input (Eniscope API Response)

```json
{
  "channels": [
    {
      "channel": "RTU-2_WCDS_Wilson Ctr",
      "channelId": "162119",
      "rawReadings": [
        {
          "ts": 1764565200,      // Unix timestamp
          "E": 1290.08,           // Energy (Wh) ⚠️ Note: Wh, not kWh
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

### Output (VEM Format for Reports)

```csv
Timestamp,Usage_kWh,Asset_Name
2025-12-01 00:00:00,1.29,RTU-2_WCDS_Wilson Ctr
```

**Key Transformations:**
- `ts` (Unix) → `Timestamp` (datetime string)
- `E` (Wh) → `Usage_kWh` (divided by 1000)
- `channel` → `Asset_Name`

---

## 🎯 Customer/Channel IDs

Based on your Wilson Center data, you have these channels:

| Channel ID | Channel Name |
|------------|--------------|
| 162119 | RTU-2_WCDS_Wilson Ctr |
| 162122 | CDPK_Kitchen Main Panel(s)_WCDS_Wilson Ctr |
| 162125 | RTU-1_WCDS_Wilson Ctr |
| 162128 | 1st Floor Panels_WCDS_Wilson Ctr |
| 162131 | 2nd Floor Panels_WCDS_Wilson Ctr |
| ... | (and more) |

**Usage:**
```bash
# Fetch data for a specific channel
python fetch_bestenergy_data.py --customer-id "162119" ...

# Or use the full name
python fetch_bestenergy_data.py --customer-id "RTU-2_WCDS_Wilson Ctr" ...
```

---

## 🔑 Authentication

### Header Configuration

```python
# Python (axios-style)
headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {API_KEY}'
}
```

```typescript
// React (TypeScript)
headers: {
  'Content-Type': 'application/json',
  'Authorization': `Bearer ${API_KEY}`
}
```

### Environment Variables

**File:** `.env`
```bash
VITE_BEST_ENERGY_API_URL=https://api.eniscope.com
VITE_BEST_ENERGY_API_KEY=your_api_key_here
VITE_API_TIMEOUT=30000
```

**Common Base URLs:**
- `https://api.eniscope.com`
- `https://api.best.energy`
- `https://portal.best.energy/api`
- `https://cloud.eniscope.com/api`

---

## 📊 Resolution Options

| Resolution | Seconds | Description |
|------------|---------|-------------|
| `'3600'` | 1 hour | Hourly readings (default) |
| `'86400'` | 24 hours | Daily aggregation |
| `'604800'` | 7 days | Weekly aggregation |
| `'2592000'` | 30 days | Monthly aggregation |

---

## 🧪 Testing Commands

### 1. Use Existing Data (No API)
```bash
cd python_reports
python use_existing_wilson_data.py \
  --json ../data/wilson-center-analysis.json
```

### 2. Test API Connection
```bash
cd python_reports
python fetch_bestenergy_data.py \
  --customer-id "162119" \
  --start-date 2025-12-01 \
  --end-date 2025-12-31 \
  --output test_api.csv
```

### 3. Full Pipeline
```bash
cd python_reports
python full_pipeline.py \
  --customer-id "wilson-center" \
  --baseline-start 2025-12-01 \
  --baseline-end 2025-12-15 \
  --report-start 2025-12-16 \
  --report-end 2025-12-31
```

### 4. React App Test
```bash
# Start dev server
npm run dev

# Visit in browser
http://localhost:5173/api-test
```

---

## 🔍 Endpoint Detection Logic

Both Python and React implementations use a **fallback pattern**:

1. Try primary endpoint
2. If fails (404/500), try next endpoint
3. Continue until success or all fail
4. Return most informative error

This ensures compatibility across different Eniscope/Best.Energy API versions.

---

## 📝 API Response Examples

### Success Response
```json
{
  "summary": {
    "totalChannels": 9,
    "totalDataPoints": 5952,
    "totalEnergy": 7572.50
  },
  "channels": [
    {
      "channel": "RTU-2_WCDS_Wilson Ctr",
      "status": "success",
      "dataPoints": 744,
      "rawReadings": [...]
    }
  ]
}
```

### Error Response
```json
{
  "error": "Unauthorized",
  "message": "Invalid API key",
  "statusCode": 401
}
```

---

## ✅ Configuration Checklist

- [x] API endpoints configured (multiple fallback patterns)
- [x] Unix timestamp conversion
- [x] Wh → kWh conversion
- [x] Channel-based data structure support
- [x] Authorization headers
- [x] Error handling and retry logic
- [x] Data transformation to VEM format
- [x] React app integration
- [x] Python scripts ready

---

## 🚀 Next Steps

1. **Test with existing data first:**
   ```bash
   python use_existing_wilson_data.py --json ../data/wilson-center-analysis.json
   ```

2. **When ready for live API:**
   - Add API key to `.env`
   - Test with `fetch_bestenergy_data.py`
   - Run full pipeline

3. **For React app:**
   - Add API key to `.env`
   - Start dev server: `npm run dev`
   - Visit `/api-test` page

---

**Documentation:**
- Full guide: `API_CONFIGURATION.md`
- Quick start: `backend/python_reports/QUICK_START.md`
- Portal data: `HOW_TO_ACCESS_PORTAL_DATA.md`

