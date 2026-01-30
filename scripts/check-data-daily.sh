#!/bin/bash
# Daily Data Availability Check
# Run this daily until Wilson Center data appears in the API

echo "🔍 Daily Wilson Center Data Check - $(date)"
echo "================================================"
echo ""

cd "$(dirname "$0")/.."

# Run diagnostic
echo "Running diagnostic tests..."
npm run diagnose:data

# Check if data was found
if grep -q '"dataPoints": [1-9]' data/diagnostic-results.json 2>/dev/null; then
    echo ""
    echo "✅ SUCCESS! Data is now available!"
    echo "================================================"
    echo ""
    echo "Next steps:"
    echo "1. Run full Wilson Center analysis:"
    echo "   npm run analyze:wilson yesterday 900"
    echo ""
    echo "2. Review the generated report:"
    echo "   cat data/wilson-center-report.md"
    echo ""
    echo "3. Begin Salesforce integration (see SALESFORCE_INTEGRATION_GUIDE.md)"
    echo ""
else
    echo ""
    echo "⏳ No data yet. This is normal for newly deployed devices."
    echo ""
    echo "Typical timeline:"
    echo "- Portal data: Immediate (✅ you have this)"
    echo "- API data: 24-72 hours after deployment"
    echo ""
    echo "💡 Tip: Check Best.Energy portal to confirm data is visible there"
    echo "📞 If no API data after 72 hours, contact Best.Energy support"
    echo ""
fi

echo "================================================"
echo "Check completed: $(date)"

