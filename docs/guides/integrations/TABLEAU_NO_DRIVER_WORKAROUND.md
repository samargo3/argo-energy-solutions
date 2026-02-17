# Tableau Without PostgreSQL Driver - Workaround Guide

**Problem:** Company laptop won't allow PostgreSQL driver installation

**Solution:** Multiple workarounds that don't need drivers!

---

## ⚡ Quick Solution: Export to CSV

### Step 1: Export Data

```bash
# Export last 90 days
npm run py:export:tableau

# Or custom date range
npm run py:export:tableau:custom -- 2025-11-01 2026-02-04
```

**Output files** (in `reports/` folder):
- `tableau_readings.csv` - All readings (detailed)
- `tableau_channel_summary.csv` - Channel statistics
- `tableau_daily_summary.csv` - Daily aggregates ⭐ Fastest
- `tableau_hourly_patterns.csv` - Hour-of-day analysis

### Step 2: Import to Tableau

1. **Open Tableau Desktop**
2. **Connect → Text File**
3. **Select all 4 CSV files**
4. Tableau shows "Multiple Files" dialog
5. Click **Union** or **Join** as needed
6. **Done!** Start building dashboards

### Step 3: Refresh Process

**Weekly refresh:**
```bash
# Export fresh data
npm run py:export:tableau

# In Tableau: Data → Refresh
# Or: Data → Replace Data Source
```

**Advantages:**
- ✅ No driver needed
- ✅ Works on restricted laptops
- ✅ Fast in Tableau (local files)
- ✅ Can work offline

**Disadvantages:**
- ⚠️ Manual refresh required
- ⚠️ Not real-time

---

## 🌐 Cloud BI Alternatives (No Install)

### Option A: Google Looker Studio (Recommended)

**Why it's great:**
- 100% browser-based
- Connects directly to Neon PostgreSQL
- No driver or install needed
- Free forever
- Professional dashboards

**Setup (5 minutes):**

1. **Go to:** https://lookerstudio.google.com/

2. **Create → Data Source → PostgreSQL**

3. **Enter Neon details** (from your `.env`):
   ```
   Host: ep-xxx-xxx.neon.tech
   Port: 5432
   Database: neondb
   User: your_username
   Password: your_password
   ☑️ Enable SSL
   ```

4. **Test Connection** → **Connect**

5. **Create Report** → Drag fields to canvas

**Features:**
- Real-time data (always current)
- Share with anyone (link or embed)
- Mobile-friendly
- Scheduled email reports
- Export to PDF

**Sample Dashboards:**
- Power consumption timeline
- Cost tracking
- Equipment performance
- Power quality monitoring

---

### Option B: Metabase (Self-Service BI)

**Why it's great:**
- Ask questions in plain English
- Auto-generates SQL
- Great for non-technical users
- Free cloud hosting

**Setup (5 minutes):**

1. **Sign up:** https://www.metabase.com/start/

2. **Add Database → PostgreSQL**

3. **Enter Neon connection:**
   ```
   Name: Argo Energy
   Host: [your-neon-host].neon.tech
   Port: 5432
   Database: neondb
   Username: your_username
   Password: your_password
   Use SSL: Yes
   ```

4. **Save** → Start asking questions!

**Example Questions:**
- "Show me power consumption by channel last week"
- "Which equipment uses most energy?"
- "What's the trend in energy costs?"

Metabase auto-generates charts!

---

### Option C: Retool (For Custom Dashboards)

**Why it's great:**
- Build custom apps
- Direct PostgreSQL connection
- Free for personal use
- No coding required (drag-and-drop)

**Setup:**
1. Sign up at https://retool.com/
2. Add PostgreSQL resource (Neon)
3. Build custom dashboard with widgets
4. Share with team

---

## 📊 Excel Power Query (Built-in to Office)

If you have Excel on your work laptop, it has a built-in PostgreSQL connector!

**Setup:**

1. **Open Excel**

2. **Data → Get Data → From Database → From PostgreSQL Database**

3. **Enter Neon details:**
   ```
   Server: ep-xxx-xxx.neon.tech:5432
   Database: neondb
   ```

4. **Choose: Database** (not Windows auth)

5. **Enter credentials**

6. **Select tables** → Load

7. **Create Pivot Tables** for analysis

**Advantages:**
- ✅ Already installed
- ✅ Familiar interface
- ✅ Good for financial analysis
- ✅ Can refresh data

**Note:** Excel's PostgreSQL connector might also require a driver, but it's worth trying - sometimes it works when Tableau doesn't!

---

## 🔄 Automated Export (Schedule It)

If you choose the CSV export method, automate it:

### Option 1: GitHub Actions (Cloud)

Add to `.github/workflows/daily-sync.yml`:

```yaml
- name: Export for Tableau
  run: |
    python backend/python_scripts/export_for_tableau.py
    
- name: Upload Tableau files
  uses: actions/upload-artifact@v4
  with:
    name: tableau-data
    path: reports/tableau_*.csv
    retention-days: 30
```

**Then:** Download from GitHub Actions artifacts weekly

### Option 2: Cron Job (Local)

Add to your crontab:

```bash
# Every Monday at 6 AM
0 6 * * 1 cd /path/to/project && npm run py:export:tableau
```

**Then:** Refresh in Tableau weekly

---

## 📋 Which Solution to Choose?

### For Quick Start (Today)
**→ CSV Export** (`npm run py:export:tableau`)
- 5 minutes to set up
- Works immediately
- No approvals needed

### For Best Experience (This Week)
**→ Google Looker Studio**
- Real-time dashboards
- No installations
- Professional results
- Free forever

### For SQL Power Users
**→ Metabase**
- Natural language queries
- Auto-generated dashboards
- Great for exploration

### For Corporate Environment
**→ Excel Power Query**
- Already approved software
- Familiar to everyone
- Good for financial reporting

---

## 🎯 Recommended Approach

**Phase 1 (Today):**
1. Export to CSV: `npm run py:export:tableau`
2. Import to Tableau
3. Build initial dashboards
4. Show stakeholders

**Phase 2 (This Week):**
1. Set up Google Looker Studio
2. Connect directly to Neon
3. Build real-time dashboards
4. Compare with Tableau

**Phase 3 (Ongoing):**
1. Pick winner (Looker Studio or Tableau + CSV)
2. Automate exports if using CSV
3. Schedule regular updates
4. Share with team

---

## 💡 Pro Tips

### CSV Export Tips

**For Best Performance:**
```bash
# Export only recent data
npm run py:export:tableau:custom -- 2025-12-01 2026-02-04

# Smaller files = faster Tableau
```

**For Multiple Sites:**
```python
# Modify export_for_tableau.py
# Add WHERE clause:
WHERE c.organization_id = 23271
```

### Looker Studio Tips

**For Faster Dashboards:**
1. Use "Extract Data" for large datasets
2. Enable caching (Settings → Cache)
3. Add date filters

**For Better Charts:**
1. Use "Scorecards" for big numbers
2. Use "Time Series" for trends
3. Use "Pivot Tables" for analysis

---

## 🆘 Troubleshooting

### "CSV files are too large"

**Solution:** Export smaller date ranges
```bash
npm run py:export:tableau:custom -- 2026-01-01 2026-02-04
```

Or use daily_summary.csv (pre-aggregated)

### "Looker Studio connection fails"

**Check:**
1. Neon project is active (not paused)
2. SSL is enabled in connection
3. Password is correct
4. Try from different network (not VPN)

### "Excel won't connect"

**Try:**
1. Update Office to latest version
2. Check IT policies for database connections
3. Use CSV export as fallback

---

## ✅ Success Checklist

- [ ] Exported CSV files successfully
- [ ] Imported to Tableau (or tried alternative)
- [ ] Created first visualization
- [ ] Decided on long-term solution
- [ ] Set up automation (if needed)
- [ ] Shared with stakeholders

---

## 📞 Need Help?

**CSV Export Issues:**
- Run `npm run py:validate` to check database
- Check `reports/` folder for files
- Verify Neon connection in `.env`

**Alternative Tools:**
- Google Looker Studio: https://support.google.com/looker-studio
- Metabase: https://www.metabase.com/docs
- Excel Power Query: https://support.microsoft.com/en-us/office/power-query

---

**Bottom Line:**
Don't let driver restrictions stop you! CSV export + Tableau works great, and cloud BI tools often work even better.

**Start here:** `npm run py:export:tableau` 🚀
