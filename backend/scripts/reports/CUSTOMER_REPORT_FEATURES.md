# Customer-Ready HTML Report - Features Overview

## What You Get

When you run the weekly report, you now get **TWO files**:

1. **JSON File** (`weekly-brief-23271-2026-02-01.json`)
   - Raw data for internal analysis
   - Complete analytics results
   - 100-250 KB

2. **HTML File** (`weekly-brief-23271-2026-02-01.html`) ✨ **NEW!**
   - Professional customer-ready report
   - Beautiful design with Argo Energy Solutions branding
   - Ready to print, email, or share
   - 30-50 KB (lightweight!)

## Professional Report Sections

### 1. Executive Summary
- **Key Findings** - Bullet-point highlights
- **Total Potential Savings** - Large, prominent display
- **Top Risks** - Critical issues requiring attention
- **Top Opportunities** - Optimization potential

### 2. Recommended Actions (Quick Wins)
Each recommendation includes:
- **Priority badge** (High/Medium/Low)
- **Impact estimates** (kWh/week, $/week, annual $)
- **Description** of the issue
- **Specific actions** to take
- **Owner assignment** (Facilities, Energy Manager, etc.)
- **Effort estimate** (Low/Medium/High)
- **Confidence level** (Low/Medium/High)

### 3. After-Hours Energy Waste Analysis
- **Table of top 10 contributors**
- Equipment name, excess kWh, costs
- Weekly and annual savings potential
- Average power during after-hours

### 4. Consumption Anomalies
- **Summary statistics** (events, affected equipment, excess energy)
- **Timeline table** with timestamps
- Context (business hours vs after-hours)
- Peak power and excess kWh

### 5. Demand Spikes
- **Top spike events** by peak power
- Time, duration, and energy impact
- Equipment identification

### 6. Data Quality & Sensor Health
- **Issue summary** by severity
- Detailed table of issues
- Type, severity, description
- Helps identify monitoring problems

## Visual Design Features

### Color Coding
- **Blue**: Headers, Argo branding (#1e3a8a, #3b82f6)
- **Green**: Savings, opportunities (#10b981)
- **Red**: Risks, high priority (#dc3545)
- **Orange**: Medium priority (#fd7e14)
- **Yellow**: Low priority/warnings (#ffc107)

### Typography
- **System fonts** for fast loading
- **Clear hierarchy** with size/weight
- **Readable line spacing** (1.6)
- **Professional appearance**

### Layout
- **Responsive design** - works on desktop, tablet, mobile
- **Print-optimized** - looks great as PDF
- **Clean spacing** - easy to scan
- **Branded header/footer**

## Customer Benefits

### For Your Customers
1. **Easy to understand** - No technical jargon
2. **Action-oriented** - Clear next steps
3. **Cost-focused** - Shows dollar savings
4. **Professional** - Builds trust and credibility
5. **Convenient** - Opens in any browser

### For Your Business
1. **Time savings** - No manual report formatting
2. **Consistency** - Every report looks professional
3. **Branding** - Argo Energy Solutions prominently displayed
4. **Scalability** - Generate hundreds of reports automatically
5. **Customer satisfaction** - Professional deliverables

## Technical Features

### Self-Contained
- **No external dependencies** - All CSS inline
- **No images to load** - Works offline
- **Small file size** - Fast to email and load
- **Browser compatible** - Works everywhere

### Print/PDF Ready
- **Print stylesheets** included
- **Page break optimization**
- **High-quality output**
- **No wasted pages**

### Accessibility
- **Semantic HTML**
- **Color contrast** meets WCAG standards
- **Clear typography**
- **Logical reading order**

## Example Report Structure

```
┌─────────────────────────────────────────────────┐
│  ARGO ENERGY SOLUTIONS                         │
│  Weekly Energy Analytics Report                │
│  Wilson Center                                  │
└─────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────┐
│  Report Period: Jan 18-24, 2026                │
│  Location: High Point, United States           │
│  Data Quality: 99.9% Complete                  │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│  📊 EXECUTIVE SUMMARY                          │
│                                                 │
│  Key Findings:                                  │
│   • 489 kWh after-hours waste detected        │
│   • 4 anomalous consumption events            │
│                                                 │
│  ┌───────────────────────────────────────────┐ │
│  │   Total Potential Savings                 │ │
│  │   $4,000/year                             │ │
│  │   489 kWh/week ($59/week)                 │ │
│  └───────────────────────────────────────────┘ │
│                                                 │
│  Top Opportunities:                             │
│   🔹 After-Hours Optimization: $3,049/year     │
│   🔹 Demand Management: potential savings      │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│  ✅ RECOMMENDED ACTIONS                        │
│                                                 │
│  1. Reduce overnight base load on AHU-2       │
│     [HIGH PRIORITY]                            │
│     Impact: 413 kWh/week ($50) = $2,578/year  │
│     Actions: Check schedules, add sensors...   │
│     Owner: Facilities Manager                  │
│                                                 │
│  2. Investigate recurring spikes on AHU-2     │
│     [HIGH PRIORITY]                            │
│     Impact: 106 kWh/week ($13) = $664/year    │
│     ... (and more)                             │
└─────────────────────────────────────────────────┘

[Additional sections with tables and details...]

┌─────────────────────────────────────────────────┐
│  ARGO ENERGY SOLUTIONS                         │
│  Professional Energy Analytics                  │
│  Report ID: 23271-1738435758283                │
│  Generated: Feb 1, 2026                        │
└─────────────────────────────────────────────────┘
```

## Customization Options

Want to customize the report? Edit `backend/scripts/reports/lib/report-renderer.js`:

### 1. Company Branding
```javascript
// Line ~55: Company name in header
<div class="company-logo">⚡ YOUR COMPANY NAME</div>

// Line ~25-26: Brand colors
background: linear-gradient(135deg, #YOUR_COLOR1 0%, #YOUR_COLOR2 100%);
```

### 2. Report Sections
```javascript
// Comment out sections you don't want
${sections.spikes.summary.totalEvents > 0 ? `
  <!-- Spikes section -->
` : ''}
```

### 3. Color Scheme
```javascript
// Modify CSS variables in <style> section
--primary: #1e3a8a;
--secondary: #3b82f6;
--success: #10b981;
--danger: #dc3545;
```

## Comparison: Before vs After

### Before (JSON Only)
```json
{
  "summary": {
    "totalPotentialSavings": {
      "weeklyKwh": 489,
      "weeklyCost": 58.64,
      "estimatedAnnual": 3049
    }
  }
}
```
❌ Not customer-friendly
❌ Requires technical knowledge
❌ Manual formatting needed

### After (HTML Report)
```
┌──────────────────────────────┐
│  Total Potential Savings     │
│  $3,049/year                 │
│  489 kWh/week ($59/week)     │
└──────────────────────────────┘
```
✅ Beautiful, professional
✅ Easy to understand
✅ Ready to deliver
✅ Builds credibility

## ROI for Your Business

### Time Saved Per Report
- **Before**: 30-60 minutes manual formatting
- **After**: 0 minutes (automatic)
- **Savings**: 30-60 minutes per report

### At Scale
- **10 customers/week**: 5-10 hours saved
- **50 customers/week**: 25-50 hours saved
- **Annual savings**: 1,300-2,600 hours

### Professional Image
- Consistent branding
- Error-free formatting
- Immediate delivery
- Customer satisfaction

## Getting Started

### 1. Generate Your First Report
```bash
npm run report:weekly -- --site 23271
```

### 2. Open the HTML File
```bash
open data/weekly-brief-23271-*.html
```

### 3. Review in Browser
- Check all sections
- Verify data accuracy
- Review recommendations

### 4. Deliver to Customer
- Email as attachment
- Upload to portal
- Print to PDF
- Share via cloud storage

## Need Help?

- **Full documentation**: `CUSTOMER_REPORTS.md`
- **Technical details**: `README.md`
- **Quick start**: `QUICKSTART.md`
- **Customization**: Edit `lib/report-renderer.js`

---

**Ready to impress your customers with professional energy reports!** 🎉
