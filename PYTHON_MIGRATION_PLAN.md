# Python Migration Plan for Argo Energy Solutions

## Overview

This document outlines the strategy for converting the project to primarily use Python for backend operations, data engineering, and analytics while keeping Node.js for the React frontend build system.

---

## ✅ Completed

### 1. Data Ingestion (Python)
**Status:** ✅ **DONE**

**File:** `backend/python_scripts/ingest_to_postgres.py`

**Benefits:**
- Cleaner, more readable code (~250 lines vs 400+ lines JS)
- Better error handling with try/except
- Native datetime support
- psycopg2 for efficient database operations
- Easier to extend with pandas for data transformation

**Usage:**
```bash
# Install dependencies
pip install -r backend/python_scripts/requirements.txt

# Run ingestion
python backend/python_scripts/ingest_to_postgres.py --site 23271 --days 90
```

---

## 📋 Scripts to Convert (Priority Order)

### **HIGH PRIORITY** - Convert Immediately

#### 1. Weekly Reports & Analytics ⭐ **MOST IMPORTANT**

**Current (JavaScript):**
- `backend/scripts/reports/weekly-exceptions-brief.js`
- `backend/scripts/reports/analytics/*.js` (5 files)
- `backend/scripts/reports/lib/stats-utils.js`
- `backend/scripts/reports/lib/date-utils.js`

**Why Convert:**
- ✅ **Analytics are Python's strength** - numpy, scipy, pandas
- ✅ **Better statistical functions** - scipy.stats vs manual JS
- ✅ **Cleaner data manipulation** - pandas DataFrames
- ✅ **Easier testing** - pytest vs custom JS tests
- ✅ **Integration with ML** - scikit-learn for anomaly detection

**Recommendation:**
```python
# New structure:
backend/python_scripts/
├── reports/
│   ├── weekly_exceptions_brief.py  # Main report generator
│   ├── analytics/
│   │   ├── sensor_health.py
│   │   ├── anomaly_detection.py
│   │   ├── spike_detection.py
│   │   ├── after_hours_waste.py
│   │   └── quick_wins.py
│   ├── lib/
│   │   ├── stats_utils.py
│   │   ├── date_utils.py
│   │   └── data_fetcher.py  # Query PostgreSQL
│   └── config/
│       └── report_config.py
```

**Benefits:**
```python
# Instead of manual statistics:
import numpy as np
import pandas as pd
from scipy import stats

# Anomaly detection becomes:
df = pd.DataFrame(readings)
df['z_score'] = stats.zscore(df['power_kw'])
anomalies = df[df['z_score'].abs() > 3]

# After-hours analysis:
df['is_business_hours'] = df['timestamp'].apply(is_business_hours)
after_hours = df[~df['is_business_hours']].groupby('channel_name')['energy_kwh'].sum()
```

---

#### 2. Data Analysis Scripts

**Convert:**
- `backend/scripts/analysis/wilson-center-analysis.js`
- `backend/scripts/analysis/analyze-energy-data.js`

**Why:**
- These are pure data analysis
- Perfect for pandas/matplotlib
- Can create better visualizations

**New:**
```python
backend/python_scripts/analysis/
├── wilson_center_analysis.py
└── analyze_energy_data.py
```

---

#### 3. Data Export & Collection

**Convert:**
- `backend/scripts/data-collection/export-wilson-raw-monthly.js`
- `backend/scripts/data-collection/explore-channels.js`
- `backend/scripts/utilities/export-to-csv.js`

**Why:**
- pandas.to_csv() is superior
- Better handling of large datasets
- Native CSV/Excel support

**New:**
```python
backend/python_scripts/data_collection/
├── export_wilson_raw_monthly.py
├── explore_channels.py
└── export_to_csv.py
```

---

### **MEDIUM PRIORITY** - Convert When Needed

#### 4. Diagnostics

**Convert:**
- `backend/scripts/diagnostics/diagnose-data-access.js`
- `backend/scripts/diagnostics/unit-health-report.js`

**Keep JavaScript (for now):**
- `backend/scripts/utilities/capture-api-calls.js` - Web debugging

---

#### 5. Database Utilities

**Convert to Python:**
- `backend/scripts/database/check-database.js` → `check_database.py`
- `backend/scripts/database/test-neon-connection.js` → `test_neon_connection.py`
- `backend/scripts/database/fix-schema.js` → `fix_schema.py`

**Why:** Better database libraries (SQLAlchemy, psycopg2)

---

### **LOW PRIORITY / KEEP AS-IS**

#### Keep in JavaScript:

1. **Frontend Build System** ✅
   - `package.json` scripts for React
   - Vite configuration
   - Frontend development

2. **API Server** (If you use it)
   - `backend/server/api-server.js`
   - Keep for serving React app in dev

3. **HTML Report Generation** (Maybe)
   - `backend/scripts/reports/generate-html-from-json.js`
   - Consider: Python has great HTML templating (Jinja2)
   - Decision: **Could convert** but not urgent

---

## 🎯 Recommended Migration Order

### Phase 1: Core Analytics (Week 1)
1. ✅ Data ingestion (DONE!)
2. Convert `stats_utils.js` → `stats_utils.py`
3. Convert `date_utils.js` → `date_utils.py`
4. Convert analytics modules (sensor health, anomaly detection, etc.)

### Phase 2: Report Generation (Week 2)
5. Convert `weekly-exceptions-brief.js` → `weekly_exceptions_brief.py`
6. Test end-to-end with PostgreSQL data
7. Compare outputs to ensure accuracy

### Phase 3: Data Operations (Week 3)
8. Convert analysis scripts
9. Convert export utilities
10. Convert database utilities

### Phase 4: Cleanup (Week 4)
11. Update documentation
12. Remove old JavaScript files
13. Update npm scripts to use Python
14. Create unified requirements.txt

---

## 📦 New Project Structure

```
projects/argo-energy-solutions/
├── frontend/  (React - Keep as-is)
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── vite.config.ts
│
├── backend/
│   ├── python_scripts/  ⭐ PRIMARY BACKEND
│   │   ├── requirements.txt
│   │   ├── ingest_to_postgres.py  ✅ DONE
│   │   │
│   │   ├── reports/  📊 Analytics & Reports
│   │   │   ├── weekly_exceptions_brief.py
│   │   │   ├── analytics/
│   │   │   │   ├── sensor_health.py
│   │   │   │   ├── anomaly_detection.py
│   │   │   │   ├── spike_detection.py
│   │   │   │   ├── after_hours_waste.py
│   │   │   │   └── quick_wins.py
│   │   │   ├── lib/
│   │   │   │   ├── stats_utils.py
│   │   │   │   ├── date_utils.py
│   │   │   │   └── db_client.py
│   │   │   └── config/
│   │   │       └── report_config.py
│   │   │
│   │   ├── analysis/  📈 Data Analysis
│   │   │   ├── wilson_center_analysis.py
│   │   │   └── analyze_energy_data.py
│   │   │
│   │   ├── data_collection/  💾 Data Ops
│   │   │   ├── export_wilson_raw_monthly.py
│   │   │   ├── explore_channels.py
│   │   │   └── export_to_csv.py
│   │   │
│   │   ├── database/  🗄️ DB Utilities
│   │   │   ├── check_database.py
│   │   │   ├── test_connection.py
│   │   │   └── fix_schema.py
│   │   │
│   │   └── utilities/  🛠️ Helpers
│   │       └── common.py
│   │
│   ├── python_reports/  (Keep - PDF generation)
│   │   └── ...
│   │
│   └── scripts/  (Legacy - Will be removed)
│       └── [Old JavaScript files]
│
└── docs/
    └── PYTHON_MIGRATION_PLAN.md  (This file)
```

---

## 🔧 Setup Instructions

### 1. Install Python Dependencies

```bash
# Navigate to project
cd /Users/sargo/cursor-repo/projects/argo-energy-solutions

# Install dependencies
pip install -r backend/python_scripts/requirements.txt

# Or use virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r backend/python_scripts/requirements.txt
```

### 2. Update Environment Variables

Your `.env` already has what we need! Python will use:
- `DATABASE_URL` - PostgreSQL connection
- `VITE_ENISCOPE_API_*` - API credentials

### 3. Test Python Ingestion

```bash
# Run the new Python ingestion
python backend/python_scripts/ingest_to_postgres.py --site 23271 --days 1

# Should be faster and cleaner than JavaScript version!
```

---

## 💡 Benefits of Python Stack

### 1. **Better Data Science Ecosystem**
```python
import pandas as pd
import numpy as np
from scipy import stats

# Load all readings into DataFrame
df = pd.read_sql("SELECT * FROM readings WHERE channel_id = 162119", conn)

# Powerful operations in one line
daily_totals = df.groupby(df['timestamp'].dt.date).agg({
    'energy_kwh': 'sum',
    'power_kw': ['mean', 'max', 'std']
})

# Statistical analysis
anomalies = df[stats.zscore(df['power_kw']) > 3]
```

### 2. **Cleaner Code**
```python
# JavaScript (verbose)
const mean = values.reduce((a, b) => a + b, 0) / values.length;
const variance = values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / values.length;
const std = Math.sqrt(variance);

# Python (one line)
std = np.std(values)
```

### 3. **Better Testing**
```python
# pytest is superior to custom JavaScript tests
def test_anomaly_detection():
    readings = generate_test_data()
    anomalies = detect_anomalies(readings)
    assert len(anomalies) == 5
    assert anomalies[0]['severity'] == 'high'
```

### 4. **Machine Learning Ready**
```python
from sklearn.ensemble import IsolationForest

# Easy ML-based anomaly detection
model = IsolationForest()
model.fit(df[['power_kw', 'energy_kwh']])
df['is_anomaly'] = model.predict(df[['power_kw', 'energy_kwh']])
```

### 5. **Better Database Integration**
```python
import pandas as pd
from sqlalchemy import create_engine

# Read directly into DataFrame
engine = create_engine(os.getenv('DATABASE_URL'))
df = pd.read_sql_query("SELECT * FROM readings WHERE ...", engine)

# Write back easily
df.to_sql('processed_readings', engine, if_exists='append')
```

---

## 🚀 Quick Wins

### 1. **Immediate Performance Improvement**
Python's psycopg2 + pandas is optimized for bulk operations:
- Batch inserts: ~10,000 rows/second
- Data transformations: vectorized operations (numpy)
- Analytics: Pre-optimized functions (scipy)

### 2. **Reduced Code Complexity**
- Stats utils: 200 lines JS → 50 lines Python
- Anomaly detection: 150 lines JS → 30 lines Python
- Data exports: Built-in pandas.to_csv/to_excel

### 3. **Better Maintenance**
- Type hints for better IDE support
- pytest for comprehensive testing
- Standard scientific Python libraries (stable APIs)

---

## 📝 Migration Checklist

### Immediate (This Week)
- [x] ✅ Create Python ingestion script
- [x] ✅ Create requirements.txt
- [ ] Convert `stats_utils.js` → `stats_utils.py`
- [ ] Convert `date_utils.js` → `date_utils.py`
- [ ] Test Python ingestion thoroughly

### Next Week
- [ ] Convert analytics modules
- [ ] Convert weekly report generator
- [ ] Create pytest test suite
- [ ] Update documentation

### Following Weeks
- [ ] Convert remaining data scripts
- [ ] Convert database utilities
- [ ] Remove old JavaScript files
- [ ] Update CI/CD (if applicable)

---

## 🎓 Learning Resources

If you or your team need to get up to speed on Python for data engineering:

1. **Pandas** - https://pandas.pydata.org/docs/getting_started/intro_tutorials/
2. **NumPy** - https://numpy.org/doc/stable/user/quickstart.html
3. **SQLAlchemy** - https://docs.sqlalchemy.org/en/20/tutorial/
4. **pytest** - https://docs.pytest.org/en/stable/getting-started.html

---

## ❓ Questions to Consider

### Should you keep ANY JavaScript?

**YES - Keep for:**
- ✅ React frontend build system (Vite, npm)
- ✅ Frontend development server
- ✅ Any real-time WebSocket needs

**NO - Convert to Python:**
- ❌ Backend data processing
- ❌ Analytics and reports
- ❌ Database operations
- ❌ Data exports

### What about the API server?

**Option 1:** Convert to Python (FastAPI/Flask)
```python
from fastapi import FastAPI
app = FastAPI()

@app.get("/api/readings/{channel_id}")
async def get_readings(channel_id: int):
    # Return data from PostgreSQL
    pass
```

**Option 2:** Keep Node.js Express (if it's simple)

**Recommendation:** If you're building a customer portal, use **FastAPI** (Python). It's perfect for data APIs.

---

## 🎯 Summary

**Goal:** Transition to Python-first backend while keeping React frontend

**Timeline:** 3-4 weeks for complete migration

**Immediate Action:** Start using the Python ingestion script today!

**Next Steps:**
1. Test Python ingestion
2. I'll convert the analytics modules next
3. Then the weekly report generator
4. Finally, clean up JavaScript files

**Result:** Cleaner codebase, better performance, easier to maintain, ready for ML/AI features

---

## 🚀 Want to Start Now?

Let me know and I'll begin converting the analytics modules!

Priority conversion order:
1. **stats_utils.py** (foundation for everything)
2. **date_utils.py** (used by analytics)
3. **analytics modules** (the core logic)
4. **weekly_exceptions_brief.py** (ties it all together)

Say the word and I'll start! 💪
