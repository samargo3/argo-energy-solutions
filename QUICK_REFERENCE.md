# Quick Reference Guide - Wilson Center Energy Analysis

## 🚀 Quick Start Commands

### Generate Today's Report
```bash
npm run analyze:wilson today 900
```

### Generate Monthly Report
```bash
npm run analyze:wilson thismonth 3600
```

### Custom Electricity Rate ($0.18/kWh)
```bash
npm run analyze:wilson thismonth 3600 0.18
```

### Full Custom (rate + carbon factor)
```bash
npm run analyze:wilson lastweek 3600 0.15 0.92
```

---

## 📊 Command Parameters

```bash
npm run analyze:wilson [daterange] [resolution] [rate] [carbon]
```

| Parameter | Description | Default | Examples |
|-----------|-------------|---------|----------|
| **daterange** | Time period to analyze | yesterday | today, yesterday, lastweek, thismonth, '2024-12-01,2024-12-31' |
| **resolution** | Data granularity (seconds) | 900 (15 min) | 60 (1 min), 900 (15 min), 3600 (1 hr), 86400 (1 day) |
| **rate** | Electricity cost ($/kWh) | 0.12 | 0.10, 0.15, 0.20 |
| **carbon** | Carbon factor (lbs CO₂/kWh) | 0.92 | 0.85 (clean), 0.92 (US avg), 1.2 (coal-heavy) |

---

## 📋 Report Outputs

All reports saved to `/data/` directory:

| File | Contents |
|------|----------|
| **wilson-center-report.md** | Full formatted report (Markdown) |
| **wilson-center-summary.json** | Executive summary (JSON) |
| **wilson-center-analysis.json** | Complete raw data (JSON) |

---

## 💡 Common Use Cases

### Daily Operations Report
*15-minute resolution, yesterday's data*
```bash
npm run analyze:wilson yesterday 900
```
**Use for:** Daily operations review, quick health check

### Weekly Executive Summary  
*Hourly resolution, last week*
```bash
npm run analyze:wilson lastweek 3600 0.15
```
**Use for:** Weekly stakeholder reports, trend analysis

### Monthly Billing Report
*Hourly resolution, current month, actual utility rate*
```bash
npm run analyze:wilson thismonth 3600 0.18
```
**Use for:** Budget tracking, invoice validation

### Quarterly Analysis
*Daily resolution, custom date range*
```bash
npm run analyze:wilson ['2024-10-01','2024-12-31'] 86400 0.15
```
**Use for:** Long-term planning, efficiency tracking

---

## 📈 What's in the Report

### 1. Maintenance Alerts (if any)
- Offline sensors
- Equipment errors
- Data quality issues

### 2. Executive Summary
**Financial & Environmental Impact Table:**
- Total energy consumption (kWh)
- Estimated cost ($)
- Carbon footprint (tons CO₂)
- Average facility load (kW)
- Peak demand (kW + timestamp)
- Average power factor

**Key Insights:**
- Cost per day
- Home equivalents
- Car emissions comparison
- Power factor warnings
- Potential savings

### 3. Channel Details (by category)
**HVAC Systems:**
- RTUs (Roof Top Units)
- AHUs (Air Handling Units)

**Electrical Panels:**
- Kitchen panels
- Distribution panels

**Sensors:**
- Air quality
- Environmental monitoring

**Each channel shows:**
- Total energy & cost
- Average/peak loads
- Operating hours
- Voltage stability
- Power factor status
- Peak occurrence time

### 4. Recommendations
**Priority 1:** Immediate actions (safety/maintenance)  
**Priority 2:** Efficiency improvements (financial ROI)  
**Priority 3:** Long-term optimization (strategic)

---

## 🎯 Reading the Report

### Status Indicators
- ✅ **Green:** Good/Excellent
- ⚠️ **Yellow:** Acceptable/Monitor
- ❌ **Red:** Poor/Action Required

### Power Factor Guide
- **≥ 0.95:** ✅ Excellent (no action needed)
- **0.85-0.95:** ⚠️ Acceptable (minor improvements)
- **< 0.85:** ❌ Poor (penalties likely, correction recommended)

### Voltage Stability
- **< 3V range:** ✅ Stable
- **3-6V range:** ⚠️ Moderate (monitor)
- **> 6V range:** ❌ Unstable (investigate)

---

## 💰 Understanding Costs

### Monthly Cost Calculation
```
Monthly kWh × Rate = Monthly Cost
7,572 kWh × $0.15/kWh = $1,136
```

### Power Factor Penalty
```
If PF < 0.85:
Penalty ≈ (Target PF - Actual PF) × 20% × Base Cost

Example:
(0.95 - 0.55) × 20% × $1,136 = ~$91/month penalty
Annual savings from correction: ~$1,092
```

### Peak Demand Charges
Some utilities charge for peak demand (kW), not just energy (kWh).

**Example:**
- Peak: 17 kW
- Demand charge: $15/kW
- Monthly demand cost: 17 × $15 = $255

---

## 🌍 Carbon Footprint Context

### US Average: 0.92 lbs CO₂/kWh

**Wilson Center Monthly Example:**
```
7,572 kWh × 0.92 lbs/kWh = 6,966 lbs CO₂
= 3.5 tons CO₂
= 1.6 cars off the road for a year
= 41 trees planted
```

### Regional Variations
- **Clean energy states** (WA, OR): ~0.4 lbs/kWh
- **US Average**: 0.92 lbs/kWh  
- **Coal-heavy states** (WV, WY): ~1.5 lbs/kWh

---

## 🔧 Troubleshooting

### No Data Returned
```
⏳ No data found for date range
```
**Solutions:**
1. Try more recent date range (today/yesterday)
2. Check device connectivity on portal
3. Verify channel is active (status = 1)

### Rate Limit Errors (429)
```
⏳ Rate limited. Retrying in 1s...
```
**Normal behavior** - script automatically retries with exponential backoff.

### Sensor Errors (500)
```
❌ Error: Request failed with status code 500
```
**Action:** Check "Maintenance Alerts" section of report - sensor may be offline.

---

## 📊 Exporting Data

### For Excel/Spreadsheets
```bash
# Open JSON in Excel
open data/wilson-center-analysis.json
```

### For Salesforce
```javascript
// Import summary data
const summary = require('./data/wilson-center-summary.json');
// Push to Salesforce via API
```

### For Custom Dashboards
All data available in structured JSON format with:
- Timestamps
- Channel IDs
- Energy values
- Power readings
- Metadata

---

## 🤝 Sharing Reports

### Email to Client
1. Open `data/wilson-center-report.md`
2. Copy and paste into email (renders nicely)
3. Or export as PDF using Markdown viewer

### Presentation Format
1. Copy key tables from report
2. Paste into PowerPoint/Google Slides
3. Add visualizations from data

### Web Dashboard
1. Parse JSON files
2. Create charts with Chart.js/D3.js
3. Host on internal portal

---

## 📱 Integration Options

### Salesforce
```javascript
// See SALESFORCE_INTEGRATION_GUIDE.md
// Create Energy_Site__c, Energy_Channel__c objects
// Schedule daily sync job
```

### Google Sheets
```javascript
// Export to CSV, import to Sheets
// Use Google Apps Script for automation
```

### Power BI / Tableau
```javascript
// Import JSON files as data source
// Create interactive dashboards
```

---

## 🎓 Best Practices

### Resolution Guidelines
| Time Period | Recommended Resolution |
|-------------|----------------------|
| 1 day | 900s (15 min) |
| 1 week | 3600s (1 hour) |
| 1 month | 3600s (1 hour) |
| 3+ months | 86400s (1 day) |

### Analysis Frequency
- **Daily:** Operations monitoring
- **Weekly:** Management review
- **Monthly:** Executive reporting, billing
- **Quarterly:** Strategic planning

### Data Retention
Keep analysis files organized:
```
/data/
  /2024-12/
    wilson-center-2024-12-01.json
    wilson-center-2024-12-08.json
    wilson-center-2024-12-15.json
```

---

## 🆘 Getting Help

### Documentation
- `WILSON_CENTER_REPORT.md` - Infrastructure guide
- `API_RATE_LIMITS.md` - API usage guidelines
- `SALESFORCE_INTEGRATION_GUIDE.md` - Integration instructions
- `FIXES_APPLIED.md` - Unit conversion fixes
- `REPORT_IMPROVEMENTS.md` - Latest enhancements

### Support
- **API Issues:** Best.Energy support
- **Script Issues:** Check error messages, review documentation
- **Salesforce:** Refer to integration guide

---

## 📝 Quick Checklist

Before sending report to client:

- [ ] Verified electricity rate is accurate
- [ ] Checked maintenance alerts section
- [ ] Reviewed power factor recommendations
- [ ] Confirmed peak demand timing makes sense
- [ ] Validated cost estimate is reasonable
- [ ] Checked for any sensor errors
- [ ] Reviewed priority recommendations

---

**Last Updated:** December 30, 2024  
**Version:** 2.0 (with all improvements)

