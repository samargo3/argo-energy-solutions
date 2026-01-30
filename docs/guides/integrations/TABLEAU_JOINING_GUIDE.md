# Tableau CSV Join Guide - Wilson Center Energy Data

## Your CSV Files Overview

You have **4 CSV files**, each serving a different purpose:

### 1. **wilson-center-channels.csv** (8 rows)
**Contains:** Summary statistics per channel
**Key columns:** Channel ID, Channel Name, Total Energy, Average Power, Power Factor
**Use for:** Channel comparison, equipment rankings, summary tables

### 2. **wilson-center-timeseries.csv** (5,952 rows)
**Contains:** Detailed readings over time
**Key columns:** Timestamp, Channel ID, Channel Name, Power, Energy, Voltage
**Use for:** Trend charts, time-series analysis, detailed visualizations

### 3. **wilson-center-summary.csv** (1 row)
**Contains:** Overall facility statistics
**Key columns:** Total Energy, Cost, Carbon Footprint, Peak Power
**Use for:** KPI cards, executive summary, big numbers

### 4. **wilson-center-categories.csv** (4 rows)
**Contains:** Aggregated data by equipment type
**Key columns:** Category, Total Energy, Number of Channels
**Use for:** Pie charts, category breakdowns

---

## Step-by-Step: Connecting Files in Tableau

### Option 1: Simple Single-File Import (Easiest) ⭐

**When to use:** You just want a quick visualization

#### For Time-Series Charts:
1. **Open Tableau Desktop**
2. Click **"Connect"** → **"Text file"**
3. Navigate to: `/Users/sargo/argo-energy-solutions/data/`
4. Select **`wilson-center-timeseries.csv`**
5. Click **"Open"**

**You're done!** This file has everything for most visualizations:
- Timestamp (for trends)
- Channel Name (for filtering/coloring)
- Category (for grouping)
- Power, Energy, Voltage (for measurements)

#### Quick Visualization:
- Drag **"Timestamp"** to **Columns**
- Drag **"Power (kW)"** to **Rows**
- Drag **"Channel Name"** to **Color**
- **Result:** Multi-line energy chart by channel ✅

---

### Option 2: Join Two Files (Recommended) ⭐⭐

**When to use:** You want both detailed readings AND channel summaries

This gives you the best of both worlds:
- Time-series data for trends
- Channel metadata for context

#### Step 1: Import First File
1. **Open Tableau Desktop**
2. Click **"Connect"** → **"Text file"**
3. Select **`wilson-center-timeseries.csv`**
4. You'll see the Data Source page

#### Step 2: Add Second File
1. On the left, under **"Connections"**, click **"Add"** (the plus icon)
2. Select **"Text file"** again
3. Choose **`wilson-center-channels.csv`**

#### Step 3: Create the Join
Tableau will show both files in the top area. Now join them:

1. **Drag** `wilson-center-channels.csv` next to `wilson-center-timeseries.csv`
2. A **Join** dialog appears
3. Tableau will **auto-detect** the join on **"Channel ID"** (because both files have this column)
4. Verify the join:
   - Left table: `wilson-center-timeseries`
   - Join type: **Inner Join** (default is fine)
   - Join clause: `Channel ID = Channel ID`
   - Right table: `wilson-center-channels`

#### Step 4: Verify the Join
Look at the data preview at the bottom - you should see:
- Columns from timeseries (Timestamp, Power, Energy, Voltage)
- PLUS columns from channels (Total Energy, Power Factor, Operating Hours)

Click **"Update Now"** to see a preview.

#### What You Can Now Do:
- **Time-series charts** using Timestamp and Power
- **Filter by Power Factor** (from channels table)
- **Show Operating Hours** alongside current readings
- **Compare actual power vs. average power** (from channels)

---

### Option 3: Join All Four Files (Advanced) ⭐⭐⭐

**When to use:** You want everything - full analysis capabilities

#### The Join Strategy:

```
wilson-center-timeseries (main table - most detail)
    ↓
    JOIN ON "Channel ID"
    ↓
wilson-center-channels (adds channel summaries)
    ↓
    CROSS JOIN (no key needed)
    ↓
wilson-center-summary (adds overall facility stats)
    ↓
    CROSS JOIN (no key needed)
    ↓
wilson-center-categories (adds category aggregations)
```

#### Step-by-Step:

**1. Start with Timeseries**
- Connect to `wilson-center-timeseries.csv`

**2. Add Channels (Inner Join on Channel ID)**
- Add connection → `wilson-center-channels.csv`
- Drag next to timeseries
- Join on: **Channel ID = Channel ID**
- Join type: **Inner**

**3. Add Summary (Cross Join)**
- Add connection → `wilson-center-summary.csv`
- Drag below the joined tables
- A new join line appears
- Click the join icon
- Change join type to: **Cross Join** (last option)
  - Why? Summary has only 1 row with facility totals - we want it on every row

**4. Add Categories (Left Join on Category)**
- Add connection → `wilson-center-categories.csv`
- Drag below
- Join on: **Category = Category**
- Join type: **Left** (keeps all timeseries rows even if category missing)

#### The Result:
Every row now has:
- ✅ Detailed reading data (timestamp, power, voltage)
- ✅ Channel summary (total energy, power factor)
- ✅ Facility totals (overall cost, carbon footprint)
- ✅ Category aggregations (category totals)

---

## Join Types Explained

### Inner Join (Most Common)
```
Timeseries    Channels
-----------   ----------
Channel 1  →  Channel 1  ✓ (matched, included)
Channel 2  →  Channel 2  ✓ (matched, included)
Channel 3  →  [missing]  ✗ (no match, excluded)
```
**Use when:** You only want rows that exist in both tables

### Left Join
```
Timeseries    Channels
-----------   ----------
Channel 1  →  Channel 1  ✓ (matched, included)
Channel 2  →  Channel 2  ✓ (matched, included)
Channel 3  →  [missing]  ✓ (included with nulls)
```
**Use when:** You want ALL timeseries data, even if channel info is missing

### Cross Join
```
Timeseries    Summary
-----------   ----------
Row 1      →  Row 1  ✓ (every row gets summary)
Row 2      →  Row 1  ✓
Row 3      →  Row 1  ✓
```
**Use when:** Joining a single-row summary to all detail rows

---

## Practical Examples

### Example 1: Power Over Time with Channel Details

**Files needed:** timeseries + channels

**Visualization:**
1. **Columns:** Timestamp (continuous)
2. **Rows:** Power (kW)
3. **Color:** Channel Name
4. **Tooltip:** Add "Power Factor" (from channels table)

**Result:** Line chart showing power trends, hover shows if channel has power quality issues

---

### Example 2: Channel Performance vs. Facility Average

**Files needed:** timeseries + channels + summary

**Calculated Field:**
```
Percent of Total = SUM([Power (kW)]) / [Total Energy (kWh) (wilson-center-summary)]
```

**Visualization:**
1. **Rows:** Channel Name
2. **Columns:** Percent of Total
3. **Color:** Category

**Result:** Bar chart showing each channel's contribution to total energy

---

### Example 3: Category Breakdown Dashboard

**Files needed:** categories + summary

**Visualization 1 - Pie Chart:**
1. Drag "Category" to **Color**
2. Drag "Total Energy (kWh)" to **Angle**
3. Mark type: **Pie**

**Visualization 2 - KPI Cards:**
1. Drag "Total Energy (kWh)" from summary to view
2. Mark type: **Text**
3. Format as big number

---

## Common Issues & Solutions

### Issue 1: "No relationships detected"

**Problem:** Tableau can't find matching columns

**Solution:**
1. Click the join icon
2. Manually select columns:
   - Left table: **Channel ID**
   - Right table: **Channel ID**
3. Ensure column names match exactly (they do in our files)

---

### Issue 2: "Duplicate rows after join"

**Problem:** You see way more rows than expected

**Solution:**
- Check join type - you might have used Cross Join accidentally
- Should be **Inner Join** for timeseries ↔ channels
- Only use **Cross Join** for summary (single row)

---

### Issue 3: "Null values appearing"

**Problem:** Some fields show null after join

**Solution:**
- This is normal if using **Left Join**
- Means some timeseries rows don't have matching channel data
- Either:
  - Use **Inner Join** to exclude unmatched rows, or
  - Filter out nulls in Tableau (Filters → exclude null)

---

### Issue 4: "Performance is slow"

**Problem:** Large joined dataset is slow

**Solution:**
1. Click **"Data"** menu → **"Extract Data"**
2. Create a **Tableau Extract (.hyper file)**
3. This pre-joins and optimizes the data
4. Much faster for repeated analysis

---

## My Recommendation for You

### Start Simple (Today):

**Use timeseries.csv only:**
```bash
Connect → wilson-center-timeseries.csv
```

This already has:
- ✅ Timestamp
- ✅ Channel Name
- ✅ Category
- ✅ All measurements (Power, Energy, Voltage)

**Create 3 quick charts:**
1. **Power over time** (line chart)
2. **Energy by channel** (bar chart)
3. **Category breakdown** (pie chart)

### Next Level (This Week):

**Join timeseries + channels:**
```bash
1. Connect to timeseries.csv
2. Add channels.csv
3. Inner join on Channel ID
```

Now you can:
- ✅ Filter by Power Factor
- ✅ Show Operating Hours
- ✅ Compare to channel averages

### Advanced (When Needed):

**Join all four files:**
- When building a comprehensive executive dashboard
- When you need facility totals alongside details
- When creating calculated fields using summary data

---

## Quick Reference: Which File for Which Viz?

| Visualization | File(s) Needed | Join Required? |
|---------------|----------------|----------------|
| Power trend over time | timeseries.csv | No |
| Energy by channel (bar) | timeseries.csv OR channels.csv | No |
| Power quality table | channels.csv | No |
| Total cost KPI card | summary.csv | No |
| Category pie chart | categories.csv | No |
| Trend + power factor | timeseries + channels | Yes (Channel ID) |
| % of facility total | timeseries + summary | Yes (Cross join) |
| Everything dashboard | All 4 files | Yes (multiple joins) |

---

## Test Your Join

After creating joins, verify with this simple check:

### Expected Row Count:
- **Timeseries alone:** 5,952 rows
- **Timeseries + Channels (inner join):** 5,952 rows (should match)
- **Timeseries + Channels + Summary (cross join):** 5,952 rows (should match)
- **If you see 47,616 rows:** You accidentally did a cross join somewhere!

### Check in Tableau:
1. Look at bottom right corner → should say **"5,952 rows"**
2. If different, review your join types

---

## Next Steps

1. ✅ Open Tableau Desktop
2. ✅ Connect to `wilson-center-timeseries.csv` first
3. ✅ Create a simple line chart to verify data
4. ✅ Then add `wilson-center-channels.csv` if you need channel summaries
5. ✅ Create your first dashboard!

Need help with specific visualizations? Let me know what you want to build!

