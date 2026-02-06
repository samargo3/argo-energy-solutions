# Customer-Ready Energy Reports

The weekly report system now automatically generates professional, customer-ready HTML reports alongside the JSON data.

## Quick Start

### Generate a Complete Report

The report generator now creates **both** JSON (for analysis) and HTML (for customers) automatically:

```bash
npm run report:weekly -- --site 23271
```

This creates:
- `data/weekly-brief-23271-YYYY-MM-DD.json` - Raw data
- `data/weekly-brief-23271-YYYY-MM-DD.html` - **Customer-ready report**

### Convert Existing JSON to HTML

If you have existing JSON reports, convert them to HTML:

```bash
npm run report:html data/weekly-brief-23271-corrected.json
```

## What's in the HTML Report?

The professional HTML report includes:

### 📊 **Executive Summary**
- Key findings at a glance
- Total potential savings (annual & weekly)
- Top risks requiring attention
- Top opportunities for optimization

### ✅ **Recommended Actions (Quick Wins)**
- Prioritized list of actionable recommendations
- Impact estimates (kWh & cost savings)
- Specific steps to implement
- Assigned ownership (Facilities/Energy Manager)
- Effort estimates

### 🌙 **After-Hours Energy Waste Analysis**
- Equipment running unnecessarily outside business hours
- Top 10 contributors with costs
- Weekly and annual savings potential

### 📈 **Consumption Anomalies**
- Unusual patterns detected this week
- Comparison to baseline (previous 4 weeks)
- Timeline of anomalous events
- Context (business hours vs after-hours)

### ⚡ **Demand Spikes**
- Peak power events
- Potential equipment issues
- Load management opportunities

### 🔧 **Data Quality & Sensor Health**
- Monitoring system health
- Missing data issues
- Communication problems
- Severity ratings

## Professional Features

### Design
- **Clean, modern layout** with Argo Energy Solutions branding
- **Color-coded priorities** and severity levels
- **Easy-to-read tables** with highlighting
- **Print-optimized** for PDF conversion
- **Mobile-responsive** design

### Branding
- Argo Energy Solutions logo and colors
- Professional header and footer
- Report metadata (ID, generation time, version)
- Confidentiality statement

### Data Visualization
- Summary statistics boxes
- Highlighted savings potential
- Color-coded badges for priorities/severity
- Organized tables with sorting

## Usage Scenarios

### 1. Weekly Customer Reports

Generate and send to customers every week:

```bash
# Generate report
npm run report:weekly -- --site 23271

# Email the HTML file or upload to customer portal
```

### 2. Print to PDF

Open the HTML file in a browser and print:
- Chrome/Edge: Print → Save as PDF
- Safari: File → Export as PDF

### 3. Embed in Portal

The HTML is self-contained (no external dependencies):
- Upload to your customer portal
- Embed in email newsletters
- Share via cloud storage

### 4. Batch Generation

Generate reports for multiple sites:

```bash
#!/bin/bash
for site in 23271 23272 23273; do
  npm run report:weekly -- --site $site
done
```

## Customization

### Company Branding

Edit `backend/scripts/reports/lib/report-renderer.js`:

1. **Logo**: Update line with `ARGO ENERGY SOLUTIONS`
2. **Colors**: Modify CSS variables in `<style>` section
3. **Footer**: Update company information

### Report Sections

To show/hide sections, modify the HTML template in `report-renderer.js`:

- Comment out sections you don't want
- Reorder sections as needed
- Add custom sections

## File Sizes

Typical report sizes:
- **JSON**: 100-250 KB (detailed data)
- **HTML**: 30-50 KB (formatted report)

The HTML is lightweight and loads instantly.

## Delivery Methods

### Email
```bash
# Attach HTML file to email
# Recipients can open directly in any browser
```

### Customer Portal
```bash
# Upload to web portal
# Customers view online or download
```

### Print/PDF
```bash
# Open in browser → Print → Save as PDF
# Professional PDF ready to share
```

### Automated Distribution

Set up automated weekly reports:

```bash
#!/bin/bash
# cron job: every Monday 8am
0 8 * * 1 cd /path/to/project && \
  npm run report:weekly -- --site 23271 && \
  mail -s "Weekly Energy Report" -a data/weekly-brief-*.html customer@example.com
```

## Example Output

### Executive Summary Box
```
┌─────────────────────────────────────────┐
│ 📊 EXECUTIVE SUMMARY                    │
│                                         │
│ Key Findings:                           │
│  • 489 kWh after-hours waste detected  │
│  • 4 anomalous consumption events      │
│                                         │
│ Total Potential Savings: $4,000/year   │
│ (489 kWh/week @ $59/week)              │
└─────────────────────────────────────────┘
```

### Quick Win Example
```
┌─────────────────────────────────────────┐
│ ✅ 1. Reduce overnight base load on     │
│        AHU-2_WCDS_Wilson Ctr            │
│    [HIGH PRIORITY]                      │
│                                         │
│ Weekly Impact: 413 kWh ($50)           │
│ Annual Value: $2,578                    │
│                                         │
│ Recommended Actions:                    │
│  → Verify equipment schedules           │
│  → Check for HVAC systems running       │
│  → Consider occupancy sensors           │
│                                         │
│ Owner: Facilities Manager               │
│ Effort: Low to Medium                   │
│ Confidence: High                        │
└─────────────────────────────────────────┘
```

## Tips for Customer Communication

### 1. **Keep it Simple**
The report is designed to be understood by non-technical customers. Focus on:
- Dollar savings (not just kWh)
- Specific actions they can take
- Quick wins with low effort

### 2. **Follow Up**
After sending the report:
- Schedule a review call
- Prioritize top 3 recommendations
- Track implementation progress

### 3. **Monthly Summary**
Combine 4 weekly reports into a monthly summary:
- Show trends over time
- Highlight completed actions
- Calculate actual savings achieved

### 4. **Success Stories**
When customers implement recommendations:
- Document before/after savings
- Take screenshots for case studies
- Request testimonials

## FAQ

**Q: Can I customize the report for each customer?**  
A: Yes, edit the config file to adjust business hours, thresholds, and priorities for each site.

**Q: How do I add our company logo?**  
A: Edit `report-renderer.js` and replace the text logo with an `<img>` tag pointing to your logo.

**Q: Can customers view this on mobile?**  
A: Yes, the report is fully responsive and works on all devices.

**Q: How do I remove sensitive data?**  
A: The report only shows aggregated data. No raw interval data is included. Specific meter names can be anonymized if needed.

**Q: Can I schedule automated delivery?**  
A: Yes, use cron jobs or scheduling tools to run the report weekly and email automatically.

## Next Steps

1. ✅ Generate your first HTML report
2. ✅ Review it in your browser
3. ✅ Customize branding if needed
4. ✅ Send to a test customer
5. ✅ Set up weekly automation

---

For technical documentation, see `README.md` and `QUICKSTART.md`.

For questions about customization, edit `backend/scripts/reports/lib/report-renderer.js`.
