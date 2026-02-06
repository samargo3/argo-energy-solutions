# Report Sharing Guide

## TL;DR - Fastest Methods

### For Quick Sharing
**Print to PDF → Email PDF** (Most reliable, 2 minutes)

### For Professional Delivery
**Email HTML directly** (Works great, 1 minute)

### For Multiple Recipients
**Upload to cloud → Share link** (Best for teams)

---

## Method 1: Email HTML File Directly ⭐ EASIEST

### Why This Works
The HTML file is **completely self-contained**:
- ✅ All CSS is inline (no external stylesheets)
- ✅ No images to load (emoji/icons are unicode)
- ✅ No JavaScript required
- ✅ Works in every browser
- ✅ Only 39 KB (tiny!)

### Steps
1. Open your email client
2. Attach: `data/weekly-brief-23271-corrected.html`
3. Write brief message
4. Send!

### What Recipients Do
1. Download attachment
2. Double-click to open in browser
3. View the professional report
4. (Optional) Print to PDF for their records

### Email Template
```
Subject: Weekly Energy Report - Wilson Center

Hi [Name],

Attached is your Weekly Energy Analytics Report for 
Jan 18-24, 2026.

Key highlights:
• $4,000/year potential savings identified
• 8 prioritized action items
• Detailed analysis included

To view: Download and double-click the attached file.
It will open in your browser.

Questions? Let me know!

[Your signature]
```

**Pros:**
- ✅ Simplest method
- ✅ Works 100% of the time
- ✅ Formatting perfectly preserved
- ✅ Recipients keep a copy
- ✅ No special software needed

**Cons:**
- ⚠️ Requires recipient to download
- ⚠️ Some email clients may block HTML (rare)

---

## Method 2: Convert to PDF First 🏆 MOST PROFESSIONAL

### Why PDF?
- Universal format (everyone has PDF reader)
- Can't be accidentally edited
- Professional appearance
- Consistent across all devices
- Email-friendly

### Steps (Chrome/Edge)
```
1. Open: data/weekly-brief-23271-corrected.html
2. Press: Cmd+P (Mac) or Ctrl+P (Windows)
3. Destination: "Save as PDF"
4. Settings:
   - Paper size: Letter
   - Margins: Default
   - Background graphics: ✓ Checked
5. Click "Save"
6. Save as: wilson-center-weekly-jan-2026.pdf
7. Email the PDF
```

### Steps (Safari)
```
1. Open HTML file
2. File → Export as PDF
3. Save as: wilson-center-weekly-jan-2026.pdf
4. Email the PDF
```

### File Size
- HTML: 39 KB
- PDF: ~150-200 KB (still small!)

**Pros:**
- ✅ Universal format
- ✅ Most professional
- ✅ Print-ready
- ✅ Can't be edited
- ✅ Consistent everywhere

**Cons:**
- ⚠️ Extra step (but worth it!)
- ⚠️ Slightly larger file

---

## Method 3: Cloud Storage Link 🌐 BEST FOR TEAMS

### Platforms
- Google Drive
- Dropbox
- OneDrive
- Box
- iCloud

### Steps (Google Drive example)
```
1. Go to drive.google.com
2. Upload: weekly-brief-23271-corrected.html
3. Right-click → "Get link"
4. Set sharing: "Anyone with link can view"
5. Copy link
6. Share link via email/Slack/Teams
```

### What Recipients See
They click the link and see the report in their browser instantly!

**Pros:**
- ✅ One link → unlimited recipients
- ✅ Update once → everyone sees it
- ✅ No email size limits
- ✅ Track who viewed (some platforms)
- ✅ Can replace/update file

**Cons:**
- ⚠️ Requires internet
- ⚠️ Link management needed
- ⚠️ May preview differently in some cloud viewers

### Tip for Cloud Sharing
If the cloud service shows a "preview" that looks different, recipients can:
1. Click "Download"
2. Open locally in browser
3. See perfect formatting

---

## Method 4: Customer Portal Integration 🏢 ENTERPRISE

### For Your Customer Portal
The HTML can be directly embedded or linked:

```html
<!-- Option 1: Direct embed (iframe) -->
<iframe src="/reports/wilson-center-weekly.html" 
        width="100%" 
        height="800px" 
        frameborder="0">
</iframe>

<!-- Option 2: Link to open in new tab -->
<a href="/reports/wilson-center-weekly.html" 
   target="_blank">
  View Weekly Energy Report
</a>
```

**Pros:**
- ✅ Professional portal integration
- ✅ Customers access anytime
- ✅ Version history possible
- ✅ Automated updates

---

## Method 5: Using the Helper Script 🤖 AUTOMATED

We've created a helper script for you:

```bash
./backend/scripts/reports/send-report.sh 23271 customer@example.com
```

This will:
1. Generate the weekly report
2. Open it in your browser
3. Show instructions for sending

Then you can:
- Print to PDF easily
- Copy/paste email template
- Choose your delivery method

---

## Troubleshooting

### Problem: Email blocks HTML attachments

**Solution 1:** Convert to PDF first
**Solution 2:** Zip the HTML file
```bash
cd data
zip wilson-report.zip weekly-brief-23271-corrected.html
# Email the .zip file
```

**Solution 3:** Use cloud storage link

### Problem: Recipient sees "Download file to view"

**This is normal!** Just tell them:
```
"Please download and double-click the file. 
It will open in your browser with full formatting."
```

### Problem: Formatting looks different on their computer

**This should never happen** because the HTML is self-contained, but if it does:
1. Ask them to open in Chrome, Firefox, or Safari
2. Make sure they downloaded (not viewing in email preview)
3. Send PDF version instead

### Problem: File is too large for email

**Unlikely** (HTML is only 39 KB), but if so:
- Convert to PDF (might be slightly larger but still small)
- Use cloud storage link
- Compress as .zip (usually makes it smaller)

---

## Best Practices

### Naming Convention
Use clear, descriptive names:
```
✅ wilson-center-weekly-report-2026-01-24.pdf
✅ weekly-energy-report-jan-2026.html
❌ report.html
❌ weekly-brief-23271-corrected.html
```

### Email Subject Lines
```
✅ Weekly Energy Report - Wilson Center (Jan 18-24)
✅ Your Energy Analytics Report - Week of Jan 18
✅ Wilson Center: Weekly Performance Summary
❌ Report
❌ Here's your file
```

### Include Context
Always include in email:
- Date range covered
- Key highlights (2-3 bullets)
- Total savings identified
- Next steps/action items

### Follow-Up
Schedule a brief call to:
- Review findings together
- Prioritize recommendations
- Answer questions
- Plan implementation

---

## Comparison Table

| Method | Ease | Professional | Speed | Best For |
|--------|------|-------------|-------|----------|
| Email HTML | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Quick sharing |
| Email PDF | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Customer delivery |
| Cloud Link | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Teams/groups |
| Portal | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | Enterprise |
| Helper Script | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Automation |

---

## Quick Reference

### For Wilson Center Right Now
```bash
# Option 1: Quick email (1 minute)
# Just attach: data/weekly-brief-23271-corrected.html

# Option 2: Professional PDF (2 minutes)
open data/weekly-brief-23271-corrected.html
# Press Cmd+P → Save as PDF → Email PDF

# Option 3: Cloud link (2 minutes)
# Upload to Google Drive → Get link → Share
```

### For Regular Weekly Distribution
```bash
# Set up weekly automation
./backend/scripts/reports/send-report.sh 23271 customer@email.com
```

---

## Recommended Workflow

### For Individual Customers (like Wilson Center)
1. Generate report: `npm run report:weekly -- --site 23271`
2. Open HTML: `open data/weekly-brief-*.html`
3. Print to PDF: `Cmd+P → Save as PDF`
4. Email PDF with brief summary
5. Schedule review call

### For Multiple Customers (Batch)
1. Generate all reports (loop through sites)
2. Upload to cloud storage (organized by customer)
3. Send email with links
4. Track opens/downloads
5. Follow up with those who haven't viewed

### For Enterprise Customers (Portal)
1. Generate report automatically (cron)
2. Upload to customer portal
3. Send notification email
4. Customer logs in to view
5. Track engagement

---

## Summary

**Easiest:** Email HTML file directly (39 KB, works everywhere)

**Most Professional:** Convert to PDF, then email (universal format)

**Best for Teams:** Upload to cloud, share link (one link, many people)

**For Automation:** Use the helper script we created

**My Recommendation for Wilson Center:**
```
1. Open data/weekly-brief-23271-corrected.html
2. Cmd+P → Save as PDF
3. Name it: wilson-center-weekly-jan-2026.pdf
4. Email the PDF with the template above
```

This gives you the most professional delivery with the least hassle! 🎯
