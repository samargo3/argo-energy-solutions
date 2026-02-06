#!/bin/bash
# Automated Report Delivery Script
# 
# Usage: ./send-report.sh <site-id> <recipient-email>
# Example: ./send-report.sh 23271 customer@wilsoncenter.com

SITE_ID=$1
RECIPIENT=$2

if [ -z "$SITE_ID" ] || [ -z "$RECIPIENT" ]; then
  echo "Usage: ./send-report.sh <site-id> <recipient-email>"
  exit 1
fi

# Generate report
echo "📊 Generating weekly report for site $SITE_ID..."
npm run report:weekly -- --site $SITE_ID

# Find the most recent HTML report
REPORT=$(ls -t data/weekly-brief-$SITE_ID-*.html | head -1)

if [ ! -f "$REPORT" ]; then
  echo "❌ Report not found!"
  exit 1
fi

echo "✅ Report generated: $REPORT"
echo "📧 Sending to $RECIPIENT..."

# Option 1: Using macOS mail command
# mail -s "Weekly Energy Report - $(date +%Y-%m-%d)" -a "$REPORT" "$RECIPIENT" <<EOF
# Please find attached your weekly energy analytics report.
# EOF

# Option 2: Using mutt (install with: brew install mutt)
# mutt -s "Weekly Energy Report" -a "$REPORT" -- "$RECIPIENT" <<EOF
# Please find attached your weekly energy analytics report.
# EOF

# Option 3: Manual (open in default email client)
echo ""
echo "📎 Report ready to send:"
echo "   File: $REPORT"
echo "   To: $RECIPIENT"
echo ""
echo "Option 1: Email manually"
echo "Option 2: Use cloud storage and share link"
echo "Option 3: Convert to PDF first (recommended)"
echo ""
echo "To convert to PDF:"
echo "  1. open $REPORT"
echo "  2. Press Cmd+P"
echo "  3. Save as PDF"
echo "  4. Email the PDF"

# Automatically open the report
open "$REPORT"
