# Using Reports with Gemini AI

## Overview

The unit health report script now generates **three formats** optimized for different use cases, including AI analysis with Gemini.

## Generated File Formats

### 1. **JSON Report** (Recommended for Gemini) ⭐
- **File:** `unit-health-<channelId>-<timestamp>.json`
- **Best for:** AI analysis, programmatic processing, structured data queries
- **Why Gemini loves it:** Structured, easy to parse, contains all data in a consistent format

### 2. **Markdown Report**
- **File:** `unit-health-<channelId>-<timestamp>.md`
- **Best for:** Human reading, documentation, version control
- **Why Gemini loves it:** Natural language format, easy to understand context

### 3. **HTML Report**
- **File:** `unit-health-<channelId>-<timestamp>.html`
- **Best for:** Visual presentation, sharing with stakeholders, printing
- **Contains:** Interactive charts and visualizations

## Using with Gemini

### Option 1: Upload JSON File (Recommended)

1. **Generate the report:**
   ```bash
   npm run unit:health 162119 "2025-12-15" "2026-01-20"
   ```

2. **Upload to Gemini:**
   - Go to [Gemini](https://gemini.google.com)
   - Click the upload button
   - Select the `.json` file from the `data/` directory
   - Ask questions like:
     - "What are the main equipment health issues?"
     - "Summarize the anomalies detected"
     - "What recommendations would you make?"
     - "Compare this unit's performance to industry standards"

### Option 2: Upload Markdown File

1. **Generate the report** (same as above)

2. **Upload the `.md` file** to Gemini

3. **Ask questions:**
   - "What does this report tell me about equipment health?"
   - "What are the critical issues I should address first?"
   - "Explain the power factor issues in simple terms"

### Option 3: Copy-Paste JSON Content

1. Open the JSON file
2. Copy the entire contents
3. Paste into Gemini with a prompt like:
   ```
   Analyze this equipment health report and provide:
   1. Executive summary
   2. Top 3 priority actions
   3. Estimated impact of addressing the issues
   ```

## JSON Report Structure

The JSON report is organized for easy AI analysis:

```json
{
  "metadata": {
    "generatedAt": "...",
    "unit": { "channelId": "...", "channelName": "..." },
    "analysisPeriod": { "start": "...", "end": "..." }
  },
  "equipmentHealth": {
    "status": "critical|poor|fair|good|excellent",
    "severity": 1-5
  },
  "summary": {
    "totalEnergyConsumption": 342.37,
    "averagePower": 0.40,
    "peakPower": 3.20,
    ...
  },
  "anomalySummary": {
    "total": 355,
    "bySeverity": { "critical": 2, "high": 5, ... }
  },
  "anomalies": [...],
  "statistics": {...},
  "recommendations": {
    "immediateActions": [...],
    "maintenanceItems": [...],
    "optimizationOpportunities": [...]
  },
  "topAnomalies": [...]
}
```

## Example Gemini Prompts

### For Executive Summary
```
Analyze this equipment health report and provide a 3-paragraph executive summary 
highlighting the key findings, most critical issues, and recommended actions.
```

### For Detailed Analysis
```
Review this equipment health report and:
1. Identify all critical and high-priority anomalies
2. Explain what each anomaly type means in practical terms
3. Prioritize the recommendations by impact and urgency
4. Estimate potential cost savings from addressing power factor issues
```

### For Comparison
```
Compare this unit's performance metrics to typical HVAC equipment standards:
- Power factor (target: >0.85)
- Voltage stability (target: <3V range)
- Operating patterns
Provide specific recommendations for improvement.
```

### For Root Cause Analysis
```
Analyze the anomalies in this report and suggest potential root causes for:
- The power spikes detected
- The low power factor readings
- The voltage fluctuations
What equipment issues could cause these problems?
```

## Benefits of JSON Format for AI

1. **Structured Data** - Easy for AI to parse and understand relationships
2. **Complete Information** - All data in one place, no missing context
3. **Queryable** - AI can answer specific questions about any metric
4. **Consistent Format** - Same structure every time, easier for AI to learn patterns
5. **Rich Metadata** - Includes timestamps, units, and context

## Tips for Best Results

1. **Be Specific** - Ask targeted questions rather than "analyze this"
2. **Reference Data** - Point to specific sections: "Look at the power factor statistics..."
3. **Ask for Comparisons** - "How does this compare to normal operation?"
4. **Request Action Items** - "What should I do first, second, third?"
5. **Ask for Explanations** - "Explain why power factor below 0.85 is a problem"

## Example Workflow

```bash
# 1. Generate report
npm run unit:health 162119 "last 7 days" today

# 2. Open JSON file
open data/unit-health-162119-*.json

# 3. Upload to Gemini or copy-paste

# 4. Ask questions:
# - "What's the equipment health status?"
# - "What are the top 3 issues I should fix?"
# - "Explain the power factor problem"
# - "What would you recommend for maintenance?"
```

## File Locations

All reports are saved in the `data/` directory:
- `data/unit-health-<channelId>-<timestamp>.json` ← **Use this for Gemini**
- `data/unit-health-<channelId>-<timestamp>.md`
- `data/unit-health-<channelId>-<timestamp>.html`

---

**Pro Tip:** The JSON format is specifically designed to be AI-friendly. It includes structured recommendations, severity ratings, and all the context an AI needs to provide meaningful analysis!
