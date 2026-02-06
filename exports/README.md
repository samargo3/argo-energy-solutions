# Data Exports Folder

This folder contains data exports optimized for external BI tools.

## 📊 Folder Structure

```
exports/
├── tableau/       # Tableau-ready CSV files
├── excel/         # Excel-specific exports (future)
├── powerbi/       # Power BI exports (future)
└── archive/       # Old exports (moved monthly)
```

---

## 📁 Tableau Exports

**Location:** `exports/tableau/`

**Files (updated weekly):**

### `tableau_daily_summary.csv` ⭐ Recommended
- **Size:** Small (~10KB per month of data)
- **Data:** Daily aggregates by channel
- **Best for:** Overview dashboards, trend analysis
- **Use when:** You want fast performance in Tableau

### `tableau_readings.csv`
- **Size:** Large (~50MB for 90 days)
- **Data:** 15-minute interval data
- **Best for:** Detailed analysis, intraday patterns
- **Use when:** You need minute-by-minute detail

### `tableau_channel_summary.csv`
- **Size:** Tiny (~2KB)
- **Data:** Channel metadata and overall statistics
- **Best for:** Channel comparison, equipment ranking
- **Use when:** You want summary cards/KPIs

### `tableau_hourly_patterns.csv`
- **Size:** Small (~50KB)
- **Data:** Average power by hour-of-day and day-of-week
- **Best for:** Typical usage patterns, scheduling insights
- **Use when:** You want heatmaps or pattern analysis

---

## 🔄 How to Generate

### Default (Last 90 Days)

```bash
npm run py:export:tableau
```

Exports all 4 files to `exports/tableau/`

### Custom Date Range

```bash
# Specific range
npm run py:export:tableau:custom -- 2025-11-01 2026-02-04

# Creates: tableau_custom_2025-11-01_2026-02-04.csv
```

### Automated (GitHub Actions)

Add to `.github/workflows/weekly-report.yml`:

```yaml
- name: Export for Tableau
  run: python backend/python_scripts/export_for_tableau.py
  
- name: Upload Tableau exports
  uses: actions/upload-artifact@v4
  with:
    name: tableau-exports
    path: exports/tableau/*.csv
```

---

## 📋 Using in Tableau

### Quick Start (5 minutes)

1. **Open Tableau Desktop**

2. **Connect → Text File**

3. **Navigate to:** `exports/tableau/`

4. **Select file:**
   - Start with `tableau_daily_summary.csv`
   - Or select all 4 for complete dataset

5. **Create first viz:**
   - Drag "Date" to Columns
   - Drag "Daily Energy (kWh)" to Rows
   - Drag "Channel Name" to Color
   - Done!

### Refresh Process

**Weekly refresh (manual):**
```bash
# Step 1: Generate fresh exports
npm run py:export:tableau

# Step 2: In Tableau
Right-click data source → Refresh
```

**Or use Tableau's "Replace Data Source":**
1. Data → Replace Data Source
2. Select new file
3. Maintains all dashboards and formatting

---

## 🗄️ Archive Management

### Monthly Cleanup

**Move old custom exports:**
```bash
mv exports/tableau/tableau_custom_2025*.csv exports/archive/
```

**Or automated** (add to cron):
```bash
# First Monday of month at 6 AM
0 6 1 * * find /path/to/exports/tableau -name "tableau_custom_*.csv" -mtime +30 -exec mv {} /path/to/exports/archive/ \;
```

### Archive Retention

- **Tableau CSVs:** Keep last 90 days in archive
- **Then:** Delete or move to long-term storage (S3, Google Drive)

---

## 🔒 Security Notes

### These files contain:
- ✅ Energy usage data (not sensitive)
- ✅ Channel names (building info)
- ✅ Timestamps and power readings

### They do NOT contain:
- ❌ Customer financial data
- ❌ Personally identifiable information
- ❌ API keys or credentials

**Safe to share** with:
- Facilities managers
- Energy analysts
- Building operators
- Third-party consultants

**DO NOT share** in:
- Public repositories
- Social media
- Unencrypted email (use encrypted file sharing)

---

## 📊 File Size Reference

**Typical sizes (Wilson Center, 17 channels):**

| Time Range | Daily Summary | Detailed Readings |
|-----------|---------------|-------------------|
| 7 days | 2 KB | 3 MB |
| 30 days | 8 KB | 12 MB |
| 90 days | 24 KB | 36 MB |
| 1 year | 100 KB | 150 MB |

**Recommendation:**
- For Tableau: Use daily summary (fast)
- For deep analysis: Use detailed readings
- For large date ranges: Consider database extract instead

---

## 🚀 Quick Commands

```bash
# Generate all Tableau exports (last 90 days)
npm run py:export:tableau

# Custom date range
npm run py:export:tableau:custom -- 2025-12-01 2026-01-31

# Check what's in the folder
ls -lh exports/tableau/

# Archive old files
mv exports/tableau/tableau_custom_*.csv exports/archive/
```

---

## 📞 Support

**Issues with exports?**
1. Check database has data: `npm run py:validate`
2. Verify connection: Check `.env` file
3. Test with smaller date range

**Need different format?**
- Excel: Modify `export_for_tableau.py` to use `pandas.to_excel()`
- JSON: Already available via reports
- CSV with different structure: Edit export script

---

**Last Updated:** February 4, 2026
