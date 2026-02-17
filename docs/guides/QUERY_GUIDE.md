# 🔍 Natural Language Query Guide

**Quick and easy way to query your Neon energy database!**

---

## 🚀 Quick Start

```bash
# Use npm shortcut
npm run py:query "your question here"

# Or directly with Python
source venv/bin/activate
python backend/python_scripts/query_energy_data.py "your question here"
```

---

## 📋 Supported Questions

### Data Overview

```bash
# List all channels
npm run py:query "list all channels"

# Show total energy
npm run py:query "show me total energy this week"
npm run py:query "show me total energy this month"
npm run py:query "show me total energy today"
```

### Channel Search & Info

```bash
# Search for channels
npm run py:query "search for RTU"
npm run py:query "find channel Wilson"

# Get channel statistics
npm run py:query "stats for RTU-1"
npm run py:query "average power for AHU-1A"
npm run py:query "summary for Dryer"
```

### Analysis

```bash
# Top consumers
npm run py:query "top energy consumers"
npm run py:query "top 10 consumers"
npm run py:query "top consumers this month"

# Hourly patterns
npm run py:query "hourly pattern"
npm run py:query "hourly pattern for RTU-1"
npm run py:query "hourly pattern this month"
```

### Recent Data

```bash
# Recent readings
npm run py:query "recent readings"
npm run py:query "latest readings for Dryer"
npm run py:query "last readings for AHU-2"
```

---

## 🎯 Example Queries & Results

### Example 1: List All Channels

**Query:**
```bash
npm run py:query "list all channels"
```

**Result:**
```
channel_id | channel_name                    | channel_type | organization_id
--------------------------------------------------------------------------------
158697     | A/C 0                           | energy       | 23271
162122     | AHU-1A_WCDS_Wilson Ctr          | energy       | 23271
162320     | RTU-1_WCDS_Wilson Ctr           | energy       | 23271
...
```

### Example 2: Total Energy This Week

**Query:**
```bash
npm run py:query "show me total energy this week"
```

**Result:**
```
📊 Energy Summary (Last 7 days)
==================================================
Channels:        17
Total Readings:  14,654
Total Energy:    2,437.82 kWh
Average Power:   1.41 kW
Period:          2026-01-27 to 2026-02-03
```

### Example 3: Top Energy Consumers

**Query:**
```bash
npm run py:query "top energy consumers"
```

**Result:**
```
channel_name          | total_kwh | avg_kw | peak_kw
----------------------------------------------------
AHU-2_WCDS_Wilson Ctr | 1236.48   | 5.74   | 6.49
RTU-1_WCDS_Wilson Ctr | 892.15    | 4.21   | 5.88
RTU-2_WCDS_Wilson Ctr | 756.32    | 3.55   | 4.92
...
```

### Example 4: Stats for Specific Channel

**Query:**
```bash
npm run py:query "stats for RTU-1"
```

**Result:**
```
channel_name          | reading_count | avg_power_kw | max_power_kw | total_energy_kwh
--------------------------------------------------------------------------------------
RTU-1_WCDS_Wilson Ctr | 737          | 4.21         | 5.88         | 892.15
```

### Example 5: Hourly Pattern

**Query:**
```bash
npm run py:query "hourly pattern"
```

**Result:**
```
hour | avg_power_kw | readings
-------------------------------
0    | 0.98         | 612
1    | 0.95         | 612
2    | 0.92         | 612
...
12   | 2.15         | 612
13   | 2.28         | 612
...
```

---

## 💡 Tips

### Time Periods

Most queries support time periods:
- **"this week"** - Last 7 days (default)
- **"this month"** - Last 30 days
- **"today"** - Last 24 hours

Examples:
```bash
npm run py:query "show me total energy this month"
npm run py:query "top consumers this month"
npm run py:query "hourly pattern this month"
```

### Channel Names

You can specify partial channel names:
```bash
npm run py:query "stats for RTU"       # Finds RTU-1
npm run py:query "hourly pattern for AHU"  # Finds AHU channels
npm run py:query "recent readings for Wilson"  # Finds Wilson Center channels
```

### Getting Help

If you're not sure what to ask:
```bash
npm run py:query
# Shows all available question types
```

---

## 🔧 Advanced: Direct Python Usage

If you want more control, you can use the Python API directly:

```python
from backend.python_scripts.query_energy_data import EnergyDataQuery

querier = EnergyDataQuery()

# List all channels
print(querier.list_channels())

# Get total energy for last 30 days
print(querier.get_total_energy(days=30))

# Get stats for a specific channel
print(querier.get_channel_stats("RTU-1", days=7))

# Get top 5 consumers
print(querier.get_top_consumers(days=7, limit=5))

# Get hourly pattern for a channel
print(querier.get_hourly_pattern("AHU-2", days=7))

# Get recent readings
print(querier.get_recent_readings("Dryer", limit=10))
```

---

## 📊 Common Use Cases

### Morning Check

```bash
# Quick morning check of yesterday's energy
npm run py:query "show me total energy today"
npm run py:query "top consumers today"
```

### Weekly Review

```bash
# Weekly energy review
npm run py:query "show me total energy this week"
npm run py:query "top energy consumers"
npm run py:query "hourly pattern"
```

### Equipment Investigation

```bash
# Investigate a specific piece of equipment
npm run py:query "search for RTU"
npm run py:query "stats for RTU-1"
npm run py:query "hourly pattern for RTU-1"
npm run py:query "recent readings for RTU-1"
```

### Data Quality Check

```bash
# Check data availability
npm run py:query "list all channels"
npm run py:query "recent readings"  # See if data is fresh
```

---

## 🎯 What Each Query Type Shows

### `list all channels`
- All available channels
- Channel IDs and types
- Organization/site info

### `show me total energy`
- Number of active channels
- Total readings count
- Total energy consumption (kWh)
- Average power (kW)
- Time period

### `top energy consumers`
- Channels ranked by energy use
- Total kWh per channel
- Average and peak power
- Helps identify biggest users

### `stats for [channel]`
- Reading count
- Average, min, max power
- Total energy
- Time span of data

### `hourly pattern`
- Energy use by hour (0-23)
- Average power per hour
- Reading counts
- Identifies usage patterns

### `recent readings`
- Latest data points
- Timestamp, power, energy
- Useful for real-time checks

---

## 🐛 Troubleshooting

### "No results found"
- Check channel name spelling
- Try partial name: "RTU" instead of "RTU-1_WCDS_Wilson Ctr"
- Verify data exists: `npm run py:query "list all channels"`

### "None" values in results
- Channel may not have data in the specified time period
- Try longer time period: "this month" instead of "this week"
- Check if channel is active

### Connection errors
- Verify DATABASE_URL in `.env`
- Test connection: `npm run db:test-neon`
- Check Neon database is active

---

## 📚 Related Tools

- **Report Generator:** `npm run py:report` - Full weekly analytics
- **Data Ingestion:** `npm run py:ingest` - Update database
- **Database Check:** `npm run db:test-neon` - Test connection

---

## 🚀 Quick Reference

```bash
# Most useful queries
npm run py:query "list all channels"
npm run py:query "show me total energy this week"
npm run py:query "top energy consumers"
npm run py:query "stats for RTU-1"
npm run py:query "hourly pattern"
npm run py:query "recent readings"
```

---

## 💡 Pro Tip: Create Aliases

Add to your `~/.zshrc` or `~/.bashrc`:

```bash
alias eq="cd /Users/sargo/cursor-repo/projects/argo-energy-solutions && npm run py:query"
```

Then use simply:
```bash
eq "show me total energy this week"
eq "top consumers"
eq "stats for RTU-1"
```

---

## 🎉 You're All Set!

Start querying your energy data:

```bash
npm run py:query "show me total energy this week"
```

**Tip:** The more you use it, the more natural it becomes! 🚀
