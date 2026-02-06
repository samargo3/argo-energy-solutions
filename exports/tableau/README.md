# Tableau Exports

This folder contains Tableau-ready CSV files generated from your Neon PostgreSQL database.

## 📊 Current Files

Run `npm run py:export:tableau` to generate:

1. **tableau_daily_summary.csv** ⭐ Start here
   - Pre-aggregated by day and channel
   - Fastest performance in Tableau
   - Best for trend dashboards

2. **tableau_readings.csv**
   - 15-minute interval data
   - Complete detail for analysis
   - Includes device information (ID, name, type, UUID)
   - Large file (~50MB for 90 days)

3. **tableau_channel_summary.csv**
   - Channel metadata and stats
   - Equipment comparison
   - Includes device information (ID, name, type, UUID)
   - Small file, loads instantly

4. **tableau_hourly_patterns.csv**
   - Average by hour-of-day
   - Perfect for heatmaps
   - Shows typical usage patterns

### 🔧 Device Information

All exports now include detailed device information from the Eniscope API:
- **Device ID**: Unique identifier for the physical device
- **Device Name**: Human-readable device name (e.g., "Dryer", "A/C 3")
- **Device Type**: Type of monitoring device (e.g., "Eniscope 8 Hybrid Metering Point")
- **Device UUID**: Hardware UUID from the Eniscope system (e.g., "80342815FC990001")

---

## 🔄 Refresh Schedule

**Manual (recommended for now):**
```bash
npm run py:export:tableau
```

**Automated (future):**
- GitHub Actions can export weekly
- See GITHUB_GUIDE.md for setup

---

## 📁 Using in Tableau

1. Open Tableau Desktop
2. Connect → Text File
3. Select this folder
4. Choose files to import
5. Build dashboards!

**Full guide:** [TABLEAU_QUICK_START.md](../../TABLEAU_QUICK_START.md)

---

## 🗄️ File Management

**These files are temporary** - regenerate as needed:
- Not committed to git (too large)
- Regenerate weekly or on-demand
- Old custom exports auto-archived monthly

**Location for current exports:**
```
exports/tableau/
```

**Location for old exports:**
```
exports/archive/
```

---

**Last Updated:** February 5, 2026
