# Neon → Tableau Direct Connection Guide

**⭐ Recommended Approach** - Now that your data is in Neon PostgreSQL, this is the best way to connect Tableau!

---

## 🎯 Overview

Your energy data is already in Neon PostgreSQL with proper structure:
- ✅ `organizations` table
- ✅ `channels` table (17 active channels)
- ✅ `readings` table (151,742+ readings and growing)
- ✅ `ingestion_logs` table

**No exports needed!** Tableau connects directly to Neon.

---

## 🚀 Quick Start (5 Minutes)

### Step 1: Get Your Neon Connection Details

Your connection string is in `.env`:
```env
DATABASE_URL=postgresql://user:password@host.neon.tech/dbname?sslmode=require
```

Break it down into parts:
```
Host: ep-xxx-xxx.us-east-2.aws.neon.tech
Port: 5432
Database: neondb (or your database name)
User: your_username
Password: your_password
SSL: Required
```

### Step 2: Connect Tableau Desktop

1. **Open Tableau Desktop**

2. **Connect to Data:**
   - Click "More..." under **To a Server**
   - Select **PostgreSQL**

3. **Enter Connection Details:**
   ```
   Server: ep-xxx-xxx.us-east-2.aws.neon.tech
   Port: 5432
   Database: neondb
   Authentication: Username and Password
   Username: your_username
   Password: your_password
   ☑️ Require SSL
   ```

4. **Click "Sign In"**

5. **Select Tables:**
   - Drag `readings` to canvas
   - Drag `channels` to canvas
   - Drag `organizations` to canvas
   - Tableau auto-creates relationships based on keys

6. **Done!** You now have live access to all your energy data.

---

## 📊 Two Connection Modes

### Live Connection (Recommended for Dashboards)

**Best for:**
- Real-time dashboards
- Data that updates frequently
- When you have good internet connection

**How:**
- Select "Live" when connecting
- Tableau queries Neon directly
- Always shows latest data
- No data size limits

**Pros:**
- ✅ Always current
- ✅ No storage in Tableau
- ✅ Easy to maintain
- ✅ Multiple users see same data

**Cons:**
- ⚠️ Requires internet connection
- ⚠️ Query performance depends on Neon

### Extract (Recommended for Analysis)

**Best for:**
- Complex calculations
- Offline work
- Faster performance
- Historical snapshots

**How:**
- Select "Extract" when connecting
- Creates `.hyper` file on your computer
- Schedule refreshes (daily, weekly, etc.)

**Pros:**
- ✅ Fast performance
- ✅ Works offline
- ✅ Can work with billions of rows

**Cons:**
- ⚠️ Data can be stale
- ⚠️ Takes disk space
- ⚠️ Needs refresh schedule

**Recommended Schedule:**
```
Daily at 3 AM (after GitHub Actions daily sync completes)
```

---

## 🔗 Creating Relationships in Tableau

Tableau should auto-detect these relationships:

### readings ↔ channels
```
readings.channel_id = channels.channel_id
```

### channels ↔ organizations
```
channels.organization_id = organizations.organization_id
```

If not auto-detected, create manually:
1. Click "Data" → "Edit Relationships"
2. Drag to connect tables
3. Select matching fields

---

## 📈 Suggested Tableau Data Source Setup

### Option 1: Single Data Source (Easiest)

Create one data source with all tables joined:

```
Data Source: "Argo Energy - Wilson Center"
├── readings (fact table)
├── channels (dimension)
└── organizations (dimension)
```

**Use for:** General purpose dashboards

### Option 2: Multiple Data Sources (Advanced)

Create separate data sources for different purposes:

**Data Source 1: "Real-Time Monitoring"**
- Live connection
- Last 7 days only (filter)
- For live dashboards

**Data Source 2: "Historical Analysis"**
- Extract connection
- All data
- Daily refresh at 3 AM
- For trend analysis

**Data Source 3: "Weekly Reports"**
- Extract connection
- Pre-aggregated by week
- For executive reports

---

## 🎨 Pre-Built Calculated Fields

Add these calculated fields in Tableau for instant insights:

### Date/Time Fields

```
// Hour of Day
DATEPART('hour', [Timestamp])

// Day of Week
DATENAME('weekday', [Timestamp])

// Is Weekend
DATEPART('weekday', [Timestamp]) IN (1, 7)

// Is Business Hours (8 AM - 6 PM)
DATEPART('hour', [Timestamp]) >= 8 AND 
DATEPART('hour', [Timestamp]) < 18

// Week Number
DATEPART('week', [Timestamp])
```

### Energy Metrics

```
// Daily Energy (kWh)
{ FIXED [Channel Name], DATETRUNC('day', [Timestamp]) : SUM([Energy Kwh]) }

// Peak Power
{ FIXED [Channel Name] : MAX([Power Kw]) }

// Average Power
AVG([Power Kw])

// Load Factor
AVG([Power Kw]) / MAX([Power Kw])

// Operating Hours (count of non-zero readings)
COUNT(IF [Power Kw] > 0.1 THEN 1 END) * 0.25
// Assuming 15-min intervals (900s)
```

### Cost Calculations

```
// Estimated Cost (at $0.12/kWh)
SUM([Energy Kwh]) * 0.12

// Peak Demand Charge ($15/kW)
MAX([Power Kw]) * 15

// Total Monthly Cost
SUM([Energy Kwh]) * 0.12 + MAX([Power Kw]) * 15
```

### Power Quality

```
// Power Factor Category
IF [Power Factor] >= 0.95 THEN "Excellent"
ELSEIF [Power Factor] >= 0.90 THEN "Good"
ELSEIF [Power Factor] >= 0.85 THEN "Fair"
ELSE "Poor"
END

// Voltage Status
IF [Voltage V] > 126 THEN "High"
ELSEIF [Voltage V] < 114 THEN "Low"
ELSE "Normal"
END
```

### Anomaly Detection

```
// Unusual Reading (> 3 standard deviations)
ABS([Power Kw] - WINDOW_AVG(AVG([Power Kw]))) > 
3 * WINDOW_STDEV(AVG([Power Kw]))

// After Hours Usage (power > 1 kW outside business hours)
[Power Kw] > 1 AND 
(DATEPART('hour', [Timestamp]) < 6 OR 
 DATEPART('hour', [Timestamp]) >= 20)
```

---

## 📊 5 Must-Have Dashboards

### Dashboard 1: Real-Time Monitoring

**Purpose:** Live view of current power usage

**Sheets:**
1. **Current Power by Channel** (bar chart)
   - Rows: Channel Name
   - Columns: SUM(Power kW)
   - Filter: Last 15 minutes
   - Sort: Descending

2. **Power Timeline** (line chart)
   - Columns: Timestamp (continuous)
   - Rows: AVG(Power kW)
   - Color: Channel Name
   - Filter: Last 24 hours

3. **Total Current Load** (big number)
   - SUM(Power kW) for latest reading

4. **Status Indicators**
   - Red if any channel > 20 kW
   - Yellow if total load > 100 kW
   - Green otherwise

### Dashboard 2: Daily Energy Report

**Purpose:** Daily consumption and costs

**Sheets:**
1. **Energy by Equipment** (treemap)
   - Size: SUM(Energy kWh)
   - Color: Channel Name
   - Filter: Today

2. **Hourly Profile** (area chart)
   - Columns: Hour of Day
   - Rows: SUM(Energy kWh)
   - Color: Channel Name
   - Stacked

3. **Yesterday vs Today** (dual axis)
   - Columns: Hour of Day
   - Rows: SUM(Energy kWh) for Today
   - Rows: SUM(Energy kWh) for Yesterday
   - Dual axis

4. **Cost Summary** (text table)
   - Today's energy: $XX.XX
   - This week: $XX.XX
   - This month: $XX.XX

### Dashboard 3: HVAC Performance

**Purpose:** Monitor HVAC systems specifically

**Filters:**
- Channel Name contains "RTU" or "AHU"

**Sheets:**
1. **HVAC Load Profile** (line chart)
   - Columns: Timestamp
   - Rows: AVG(Power kW)
   - Color: Channel Name
   - Show weekday pattern

2. **Runtime Hours** (bar chart)
   - Rows: Channel Name
   - Columns: Operating Hours (calculated)
   - Last 7 days

3. **After-Hours Operation** (highlight table)
   - Rows: Channel Name
   - Columns: Day of Week
   - Color: SUM(Energy kWh) during off-hours
   - Red = high after-hours usage

4. **Temperature Correlation** (scatter plot)
   - If you have weather data
   - X: Outdoor Temperature
   - Y: Total HVAC Power

### Dashboard 4: Cost Analysis

**Purpose:** Track and project costs

**Sheets:**
1. **Monthly Cost Trend** (line chart)
   - Columns: Month/Year
   - Rows: Estimated Cost
   - Trend line with forecast

2. **Cost Breakdown** (stacked bar)
   - Columns: Week
   - Rows: Cost
   - Color: Channel Name
   - Show top 10 consumers

3. **Budget vs Actual** (bullet chart)
   - Set budget target
   - Show actual vs target
   - Color code: green/yellow/red

4. **Savings Opportunities** (text table)
   - List channels with:
     - Poor power factor
     - High after-hours use
     - Unusual spikes
   - Estimated savings potential

### Dashboard 5: Power Quality

**Purpose:** Monitor voltage, power factor, reliability

**Sheets:**
1. **Power Factor by Channel** (bar chart)
   - Rows: Channel Name
   - Columns: AVG(Power Factor)
   - Color by category (excellent/good/fair/poor)
   - Reference line at 0.95

2. **Voltage Stability** (control chart)
   - Columns: Timestamp
   - Rows: AVG(Voltage V)
   - Reference lines at 114V and 126V
   - Color red if outside range

3. **Data Quality Check** (KPI)
   - % of readings in last 24h
   - Missing data indicator
   - Last sync time

4. **Improvement Recommendations** (text)
   - Based on power factor
   - "Install capacitor on channel X"
   - "Estimated annual savings: $X"

---

## 🔧 Performance Optimization

### For Large Datasets (1M+ readings)

**1. Use Data Source Filters**
```
Filter: [Timestamp] >= DATEADD('day', -90, TODAY())
```
Only load last 90 days for live dashboards.

**2. Create Extracts with Aggregation**
```
Aggregate by: 15 minutes (already in your data)
Hide unused fields: reactive_power_kvar, temperature_c
```

**3. Use Context Filters**
```
Set "Channel Name" as context filter
Applies before other filters = faster
```

**4. Optimize Calculations**
```
Use table calculations instead of row-level
Use fixed LOD expressions
Avoid WINDOW functions on large datasets
```

**5. Create Custom SQL**
```sql
-- Pre-aggregate in database for speed
SELECT 
    DATE_TRUNC('hour', timestamp) as hour,
    channel_id,
    AVG(power_kw) as avg_power,
    MAX(power_kw) as peak_power,
    SUM(energy_kwh) as total_energy
FROM readings
WHERE timestamp >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY 1, 2
```

---

## 📱 Tableau Public / Tableau Server

### Publishing to Tableau Public (Free)

**Limitations:**
- ❌ Can't use live connections
- ❌ Must use extracts
- ✅ Free hosting
- ✅ Shareable links

**Steps:**
1. Create extract locally
2. File → Save to Tableau Public
3. Sign in (free account)
4. Publish

**Security Note:** Only publish non-sensitive data!

### Publishing to Tableau Server/Online

**Benefits:**
- ✅ Live connections supported
- ✅ Scheduled extract refreshes
- ✅ User permissions
- ✅ Mobile apps

**Steps:**
1. File → Publish Workbook
2. Select Tableau Server
3. Configure:
   - Authentication: Embed password for Neon
   - Refresh schedule: Daily at 3 AM
   - Permissions: Set user access

---

## 🔐 Security Best Practices

### 1. Use Read-Only Database User

Create a dedicated Tableau user in Neon:

```sql
-- In Neon SQL Editor
CREATE ROLE tableau_reader WITH LOGIN PASSWORD 'secure_password_here';
GRANT CONNECT ON DATABASE neondb TO tableau_reader;
GRANT USAGE ON SCHEMA public TO tableau_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO tableau_reader;

-- For future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public 
GRANT SELECT ON TABLES TO tableau_reader;
```

Use this user in Tableau instead of your admin credentials.

### 2. Embed Credentials

When publishing to Tableau Server:
- ☑️ Embed password in connection
- Don't use "Prompt user" for Neon password
- Users shouldn't see database credentials

### 3. Row-Level Security

If you have multiple sites and need to restrict access:

```sql
-- Create view with security
CREATE VIEW readings_filtered AS
SELECT r.*
FROM readings r
JOIN channels c ON r.channel_id = c.channel_id
WHERE c.organization_id = CURRENT_SETTING('app.organization_id')::INTEGER;

-- In Tableau: Use view instead of table
```

---

## 🎓 Learning Resources

### Tableau Training (Free)

1. **Tableau Desktop Basics**
   - https://www.tableau.com/learn/training
   - 2-hour course, covers essentials

2. **Connecting to Databases**
   - https://help.tableau.com/current/pro/desktop/en-us/examples_postgresql.htm
   - PostgreSQL-specific guide

3. **Working with Time Series**
   - Essential for energy data
   - https://www.tableau.com/learn/tutorials/on-demand/dates-and-times

### Sample Workbooks

Download pre-built workbooks for energy monitoring:
- Tableau Public Gallery: Search "energy monitoring"
- Adapt dashboards to your schema

---

## ❓ Troubleshooting

### "Can't connect to server"

**Check:**
1. ✅ Neon project is active (not paused)
2. ✅ SSL is enabled in connection
3. ✅ Firewall allows port 5432
4. ✅ Connection string is correct

**Test connection:**
```bash
npm run py:validate
# If this works, your connection string is correct
```

### "Slow query performance"

**Solutions:**
1. Use extracts instead of live
2. Add date filter: last 30 days
3. Create indexes (already done)
4. Use custom SQL with pre-aggregation

### "Data not updating"

**Check:**
1. GitHub Actions daily sync is running
2. Last reading time in Tableau
3. Refresh extract (if using)
4. Check ingestion logs

```bash
# Check latest data
npm run py:validate
# Look for "Last reading: YYYY-MM-DD"
```

### "Missing data for some channels"

This is normal! Some channels are:
- Test sites (not production)
- Single-phase meters (no voltage data)
- Power-only meters (no energy data)

Check validation warnings for expected NULL values.

---

## 🚀 Quick Start Checklist

- [ ] Get Neon connection details from `.env`
- [ ] Open Tableau Desktop
- [ ] Connect to PostgreSQL server
- [ ] Enter Neon host, database, user, password
- [ ] Enable SSL
- [ ] Drag `readings`, `channels`, `organizations` to canvas
- [ ] Choose Live or Extract
- [ ] Create first viz: Power over Time
- [ ] Add calculated fields (date/time, costs)
- [ ] Build 5 core dashboards
- [ ] Set up extract refresh schedule (if using)
- [ ] Publish to Tableau Server/Public (optional)

---

## 📞 Support

**Having issues?**
1. Run `npm run py:validate` to check database health
2. Check GitHub Actions for sync failures
3. Review Neon console for database status
4. Test connection with `psql` or database tool first

**Want pre-built dashboards?**
Contact for custom Tableau workbook templates designed for your energy data schema.

---

## 🎉 Next Steps

1. **Connect Tableau** (follow Quick Start above)
2. **Create first dashboard** (Real-Time Monitoring recommended)
3. **Set up refresh schedule** (if using extracts)
4. **Share with stakeholders**
5. **Iterate based on feedback**

---

**Comparison to old methods:**

| Method | Setup Time | Maintenance | Real-Time | Best For |
|--------|-----------|-------------|-----------|----------|
| **Neon Direct** | 5 min | None | ✅ Yes | **Everything** ⭐ |
| CSV Export | 2 min | High | ❌ No | Quick tests |
| JSON Export | 5 min | Medium | ❌ No | File-based workflow |
| Web Connector | 30 min | Medium | ✅ Yes | Custom APIs |

**Neon direct connection is the winner!** 🏆

---

**Last Updated:** February 2026
