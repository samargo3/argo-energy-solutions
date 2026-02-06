# Wilson Center Raw Data Export - Setup Checklist

Before running your first export, verify everything is configured correctly.

## Prerequisites Checklist

### 1. Environment Setup ✓

- [ ] Node.js 18+ installed
  ```bash
  node --version  # Should show v18 or higher
  ```

- [ ] Dependencies installed
  ```bash
  npm install
  ```

- [ ] `.env` file exists in project root
  ```bash
  ls -la .env  # File should exist
  ```

### 2. API Credentials ✓

- [ ] Eniscope API credentials configured in `.env`:
  ```env
  VITE_ENISCOPE_API_URL=https://core.eniscope.com
  VITE_ENISCOPE_API_KEY=your_key_here
  VITE_ENISCOPE_EMAIL=your_email_here
  VITE_ENISCOPE_PASSWORD=your_password_here
  ```

- [ ] Test API authentication:
  ```bash
  npm run explore:channels
  ```
  Should successfully fetch channels without errors.

### 3. Channel Data Available ✓

- [ ] Wilson Center channels data exists:
  ```bash
  ls -la backend/scripts/data/channels-org-23271.json
  ```

- [ ] If not, fetch it:
  ```bash
  npm run explore:channels
  ```

### 4. Export Directory ✓

- [ ] Export directory exists:
  ```bash
  ls -la backend/data/exports/
  ```

- [ ] Directory is writable:
  ```bash
  touch backend/data/exports/test.txt && rm backend/data/exports/test.txt
  ```

## Verification Tests

### Test 1: Basic Export (Small Dataset)

Export a single day with hourly resolution:

```bash
# This should complete in ~30 seconds
npm run export:wilson:raw 2025 12 -- --resolution=86400
```

**Expected Output:**
```
✓ Authentication successful
✓ Found 9 active Wilson Center channels
✓ Data exported: wilson-center-raw-2025-12.csv
✓ Channel metadata: wilson-center-raw-2025-12-channels.csv
✓ Summary: wilson-center-raw-2025-12-summary.json
```

**Verify Files:**
```bash
ls -lh backend/data/exports/wilson-center-raw-2025-12*
```

Should see 3 files (CSV, CSV, JSON).

### Test 2: Open CSV

Verify the CSV can be opened:

```bash
# View first few lines
head -n 5 backend/data/exports/wilson-center-raw-2025-12.csv
```

Should show headers and data rows.

### Test 3: Check Summary

Verify summary JSON:

```bash
cat backend/data/exports/wilson-center-raw-2025-12-summary.json
```

Should show valid JSON with export metadata.

## Common Setup Issues

### Issue: "Missing required environment variables"

**Cause**: `.env` file missing or incomplete

**Fix**:
1. Copy from example: `cp .env.example .env`
2. Fill in actual values
3. Verify no extra spaces or quotes
4. Ensure variables start with `VITE_ENISCOPE_`

### Issue: "Channels data not found"

**Cause**: Channel exploration not run yet

**Fix**:
```bash
npm run explore:channels
```

Wait for completion, then retry export.

### Issue: "Authentication failed"

**Cause**: Invalid API credentials

**Fix**:
1. Verify credentials in Eniscope dashboard
2. Check email/password are correct
3. Ensure API key is valid and not expired
4. Try re-copying credentials (avoid copy/paste errors)

### Issue: "No data available"

**Cause**: Requesting data before Wilson Center went online

**Fix**:
- Wilson Center data starts in **May 2025**
- Try exporting a more recent month:
  ```bash
  npm run export:wilson:raw 2025 12
  ```

### Issue: Export is very slow

**Cause**: Too many data points or network issues

**Fix**:
- Use coarser resolution (3600 instead of 900)
- Check network connection
- Verify no firewall blocking API access

## Post-Setup Verification

Once setup is complete, you should be able to:

- [ ] Run export command without errors
- [ ] See 3 output files created
- [ ] Open CSV in Excel/text editor
- [ ] View summary JSON
- [ ] Import CSV into Tableau (if available)

## First Export Recommendations

### For Your First Export:

1. **Start with last month**:
   ```bash
   npm run export:wilson:raw
   ```

2. **Verify data quality**:
   - Check row count in summary JSON
   - Spot-check a few data points
   - Verify all 9 channels present

3. **Test with your tool**:
   - If using Tableau: Import and create simple chart
   - If using Python: Run example analysis script
   - If using AI: Upload and ask for summary

4. **Document any issues**:
   - Note any missing data
   - Record any errors encountered
   - Keep notes for future reference

## Automation Setup (Optional)

### For Regular Automated Exports:

#### Linux/Mac Cron Job
```bash
# Edit crontab
crontab -e

# Add line to run monthly on the 1st at 2 AM
0 2 1 * * cd /path/to/project && npm run export:wilson:raw >> /path/to/logs/export.log 2>&1
```

#### Windows Task Scheduler
1. Open Task Scheduler
2. Create Basic Task
3. Name: "Wilson Center Monthly Export"
4. Trigger: Monthly, Day 1, 2:00 AM
5. Action: Start a program
   - Program: `C:\Program Files\nodejs\node.exe`
   - Arguments: `backend/scripts/data-collection/export-wilson-raw-monthly.js`
   - Start in: `C:\path\to\project`

#### Verify Automation
```bash
# Test the cron/task runs correctly
cd /path/to/project && npm run export:wilson:raw
```

Check logs to ensure no errors.

## Tableau Integration Setup (Optional)

If using Tableau:

1. **Install Tableau Desktop** (if not already installed)

2. **Test Connection**:
   - Open Tableau
   - Connect → Text File
   - Select exported CSV
   - Verify data loads correctly

3. **Create Data Source**:
   - Save as `.tds` file
   - Configure field types if needed
   - Set up joins with metadata

4. **Create First Dashboard**:
   - Simple line chart of power over time
   - Bar chart of energy by channel
   - Verify visualizations work

## Python/R Setup (Optional)

If using Python:

```bash
# Install required packages
pip install pandas matplotlib seaborn

# Test example script
cd backend/data/exports
python example-python-analysis.py wilson-center-raw-2025-12.csv
```

Should generate charts and report.

If using R:

```r
# Install required packages
install.packages(c("tidyverse", "lubridate"))

# Load and test
library(tidyverse)
df <- read_csv("backend/data/exports/wilson-center-raw-2025-12.csv")
head(df)
```

## Support Checklist

Before requesting help, verify:

- [ ] Checked all documentation
- [ ] Reviewed error messages
- [ ] Tested with simple export first
- [ ] Verified API credentials
- [ ] Checked network connectivity
- [ ] Reviewed relevant guide (Tableau/Python/etc.)

## Success Criteria

✅ Setup is complete when:

1. Export runs without errors
2. Creates 3 expected files
3. CSV contains expected data
4. Summary shows correct metadata
5. Can import into intended tool (Tableau/Python/etc.)
6. Understand how to run future exports
7. Know where to find documentation

## Next Steps

After successful setup:

1. Review **Quick Start Guide**: `docs/guides/WILSON_RAW_EXPORT_QUICKSTART.md`
2. Read **Full User Guide**: `backend/scripts/data-collection/README_EXPORT.md`
3. Check **Integration Guides**: `docs/guides/integrations/`
4. Set up regular export schedule (if needed)
5. Create first dashboard or analysis
6. Share with stakeholders

## Maintenance

Regular checks:

- [ ] **Weekly**: Verify automated exports running
- [ ] **Monthly**: Review data quality and completeness
- [ ] **Quarterly**: Archive old exports
- [ ] **Yearly**: Review and update credentials if changed

## Getting Help

If you encounter issues:

1. **Documentation**:
   - This checklist
   - Quick Start Guide
   - Full User Guide
   - Troubleshooting sections

2. **Examples**:
   - Python analysis script
   - Tableau integration guide

3. **API Documentation**:
   - `docs/api/API_CONNECTION_GUIDE.md`
   - `docs/api/Core_API_v1.txt`

4. **Support**:
   - Check error message carefully
   - Review relevant documentation section
   - Verify setup steps completed
   - Document exact steps to reproduce issue

---

**Created**: February 2026  
**Version**: 1.0

**Quick Start After Setup**:
```bash
# You're ready! Just run:
npm run export:wilson:raw
```
