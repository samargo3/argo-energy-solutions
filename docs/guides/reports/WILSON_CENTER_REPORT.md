# Wilson Center Energy Monitoring - Setup & Analysis Report

**Organization:** Argo Energy Solutions LLC  
**Report Date:** December 29, 2024  
**Status:** Monitoring Infrastructure Deployed

---

## Executive Summary

Argo Energy Solutions has successfully deployed energy monitoring infrastructure at the Wilson Center facility. The system consists of **9 active monitoring channels** across HVAC equipment, electrical panels, and environmental sensors.

### Monitoring Infrastructure

| Category | Channels | Status |
|----------|----------|--------|
| **HVAC - Roof Top Units (RTU)** | 3 | ✅ Deployed |
| **HVAC - Air Handling Units (AHU)** | 3 | ✅ Deployed |
| **Electrical Panels** | 2 | ✅ Deployed |
| **Environmental Sensors** | 1 | ✅ Deployed |
| **Total** | **9** | **Active** |

All monitoring devices were registered between May 1-2, 2025, and licenses are valid through May 2026.

---

## Channel Inventory

### 1. HVAC Systems - Roof Top Units (RTUs)

**RTU-1_WCDS_Wilson Ctr**
- Channel ID: 162320
- Device UUID: 44B7D0E9B3C00003
- Type: Eniscope 8 Hybrid Metering Point
- Registered: May 1, 2025 4:45:18 PM
- Expires: May 1, 2026
- Status: Active ✅
- Data Type: Grid meter
- Phase: System

**RTU-2_WCDS_Wilson Ctr**
- Channel ID: 162119
- Device UUID: 44B7D0E9B3C00004
- Type: Eniscope 8 Hybrid Metering Point
- Registered: May 1, 2025 4:45:55 PM
- Expires: May 1, 2026
- Status: Active ✅

**RTU-3_WCDS_Wilson Ctr**
- Channel ID: 162120
- Device UUID: 44B7D0E9B3C00005
- Type: Eniscope 8 Hybrid Metering Point
- Registered: May 1, 2025 4:46:40 PM
- Expires: May 1, 2026
- Status: Active ✅

### 2. HVAC Systems - Air Handling Units (AHUs)

**AHU-1A_WCDS_Wilson Ctr**
- Channel ID: 162122
- Device UUID: 44B7D0E9B3C00007
- Type: Eniscope 8 Hybrid Metering Point
- Registered: May 1, 2025 4:48:38 PM
- Expires: May 1, 2026
- Status: Active ✅

**AHU-1B_WCDS_Wilson Ctr**
- Channel ID: 162123
- Device UUID: 44B7D0E9B3C00008
- Type: Eniscope 8 Hybrid Metering Point
- Registered: May 1, 2025 4:49:22 PM
- Expires: May 1, 2026
- Status: Active ✅

**AHU-2_WCDS_Wilson Ctr**
- Channel ID: 162121
- Device UUID: 44B7D0E9B3C00006
- Type: Eniscope 8 Hybrid Metering Point
- Registered: May 1, 2025 4:47:44 PM
- Expires: May 1, 2026
- Status: Active ✅

### 3. Electrical Distribution

**CDPK_Kitchen Main Panel(s)_WCDS_Wilson Ctr**
- Channel ID: 162285
- Device UUID: 44B7D0E9B3C00001
- Type: Eniscope 8 Hybrid Metering Point
- Registered: May 1, 2025 4:41:12 PM
- Expires: May 1, 2026
- Status: Active ✅
- Purpose: Main kitchen electrical distribution monitoring

**CDKH_Kitchen Panel(small)_WCDS_Wilson Ctr**
- Channel ID: 162319
- Device UUID: 44B7D0E9B3C00002
- Type: Eniscope 8 Hybrid Metering Point
- Registered: May 1, 2025 4:43:01 PM
- Expires: May 1, 2026
- Status: Active ✅
- Purpose: Secondary kitchen panel monitoring

### 4. Environmental Monitoring

**Air Sense_Main Kitchen_WCDS_Wilson**
- Channel ID: 162277
- Device UUID: 44B7D0E9B3C00501
- Type: Air Sense
- Registered: May 1, 2025 4:56:26 PM
- Expires: May 1, 2026
- Status: Active ✅
- Purpose: Air quality and environmental monitoring in main kitchen

---

## Monitoring Capabilities

Each Eniscope 8 Hybrid channel monitors multiple electrical parameters:

### Energy Metrics
- **E** - Energy consumption (kWh)
- **P** - Real power (kW)
- **kWh** - Cumulative energy
- **kW** - Instantaneous power

### Power Quality
- **V** - Voltage (V)
- **I** - Current (A)
- **PF** - Power Factor
- **Q** - Reactive Power (kVAR)
- **S** - Apparent Power (kVA)

### System Parameters
- **F** - Frequency (Hz)
- Multi-phase monitoring (V1, V2, V3, I1, I2, I3)
- Neutral current monitoring
- THD (Total Harmonic Distortion)

---

## Data Collection Status

### Current Status: ⚠️ Awaiting Data Transmission

The monitoring infrastructure has been successfully deployed and all devices are registered with valid licenses. However, **data transmission has not yet begun** from the Wilson Center site.

**Next Steps:**
1. ✅ Verify network connectivity at Wilson Center
2. ✅ Confirm devices are powered and communicating
3. ✅ Check data gateway/collector status
4. ✅ Run connectivity diagnostics
5. ⏳ Begin data collection

---

## Analysis Capabilities (When Data Available)

Once data transmission begins, the following analyses will be available:

### Real-Time Monitoring
- Live power consumption per equipment
- Voltage and power quality monitoring
- Equipment on/off status detection
- Alert notifications for anomalies

### Energy Consumption Analysis
- **Daily profiles:** Hour-by-hour energy usage patterns
- **Weekly trends:** Day-of-week consumption comparison
- **Monthly reports:** Total consumption and cost analysis
- **Peak demand:** Identify highest load periods

### Equipment-Specific Insights

**HVAC Systems (RTUs & AHUs)**
- Operating hours and runtime analysis
- Seasonal performance tracking
- Load profiles during occupied vs. unoccupied hours
- Efficiency metrics (kW per ton of cooling)
- Comparison between units

**Kitchen Electrical Distribution**
- Main vs. secondary panel load distribution
- Peak kitchen operations periods
- Equipment diversity factors
- Potential for load balancing

**Environmental Correlation**
- Air quality vs. ventilation system operation
- Temperature/humidity correlation with HVAC load
- Occupancy pattern detection

### Cost Analysis
- Energy costs by equipment category
- Time-of-use rate optimization opportunities
- Demand charge analysis
- Projected monthly/annual costs

### Efficiency & Optimization
- Identify equipment operating inefficiently
- Off-hours consumption detection
- Power factor improvement opportunities
- Load shedding opportunities
- Scheduling optimization recommendations

---

## Sample Report Format

When data becomes available, automated reports will include:

```
📊 Wilson Center Energy Summary
Period: [Date Range]

Total Energy: XXX kWh
Total Cost: $XXX
Peak Demand: XX kW at [Time]

By Equipment Category:
├─ HVAC Systems: XXX kWh (XX%)
│  ├─ RTU-1: XX kWh
│  ├─ RTU-2: XX kWh
│  ├─ RTU-3: XX kWh
│  ├─ AHU-1A: XX kWh
│  ├─ AHU-1B: XX kWh
│  └─ AHU-2: XX kWh
│
└─ Kitchen Electrical: XXX kWh (XX%)
   ├─ Main Panels: XX kWh
   └─ Small Panel: XX kWh

Power Quality:
- Average Power Factor: X.XX
- Voltage Stability: Excellent
- Harmonic Distortion: < 5%

🔍 Key Insights:
• [Automatically generated insights]
• [Equipment efficiency observations]
• [Cost saving opportunities]
• [Maintenance recommendations]
```

---

## Integration with Salesforce

### Recommended Data Flow

```
Wilson Center Devices
        ↓
Eniscope Core API
        ↓
Middleware / Integration Layer
        ↓
Salesforce Custom Objects
        ↓
Lightning Dashboards & Reports
```

### Salesforce Data Model

**Custom Objects to Create:**

1. **Energy_Site__c**
   - Site_Name__c: "Wilson Center"
   - Organization__c: Lookup to Account
   - Status__c: "Active"
   - Total_Channels__c: 9

2. **Energy_Channel__c**
   - Channel_Name__c: e.g., "RTU-1_WCDS_Wilson Ctr"
   - Channel_ID__c: External ID (162320)
   - Device_UUID__c: "44B7D0E9B3C00003"
   - Site__c: Lookup to Energy_Site__c
   - Equipment_Type__c: Picklist (RTU, AHU, Panel, Sensor)
   - Status__c: "Active"

3. **Energy_Reading__c**
   - Channel__c: Lookup to Energy_Channel__c
   - Reading_Timestamp__c: DateTime
   - Energy_kWh__c: Number
   - Power_kW__c: Number
   - Voltage__c: Number
   - Current__c: Number
   - Power_Factor__c: Number

4. **Energy_Summary__c** (Daily/Weekly/Monthly aggregations)
   - Site__c: Lookup to Energy_Site__c
   - Period_Start__c: Date
   - Period_End__c: Date
   - Period_Type__c: Picklist (Daily, Weekly, Monthly)
   - Total_Energy_kWh__c: Number
   - Total_Cost__c: Currency
   - Peak_Demand_kW__c: Number
   - Average_Power_Factor__c: Number

### Salesforce Dashboards

**Wilson Center Overview Dashboard**
- Total energy consumption gauge
- Cost trend chart (month-over-month)
- Equipment breakdown pie chart
- Peak demand timeline
- Power quality indicators

**Equipment Performance Dashboard**
- Individual HVAC unit comparisons
- Runtime hours bar chart
- Efficiency metrics
- Maintenance alerts

**Cost Analysis Dashboard**
- Cost breakdown by equipment
- Budget vs. actual
- Savings opportunities
- ROI calculations

---

## Automated Scripts

### Available Analysis Commands

```bash
# Fetch and analyze Wilson Center data
npm run analyze:wilson [daterange] [resolution]

# Examples:
npm run analyze:wilson today 900        # Today's data, 15-min intervals
npm run analyze:wilson yesterday 3600   # Yesterday, hourly
npm run analyze:wilson lastweek 3600    # Last week, hourly
npm run analyze:wilson thismonth 86400  # This month, daily

# Explore all channels
npm run explore:channels

# General energy data fetch
npm run analyze:energy
```

### Output Files

Analysis scripts generate:
- `data/wilson-center-analysis.json` - Complete raw data
- `data/wilson-center-summary.json` - Statistical summary
- `data/wilson-center-report.md` - Formatted report

---

## Troubleshooting Data Collection

### If No Data Appears:

1. **Check Device Connectivity**
   - Verify devices have power
   - Check network/gateway connectivity
   - Review device logs in Eniscope portal

2. **Verify API Access**
   - Confirm API credentials are valid
   - Check organization permissions
   - Review channel status in Eniscope portal

3. **Date Range Issues**
   - Devices only collect data after registration (May 2025)
   - Try recent date ranges (today, yesterday)
   - Verify device installation dates

4. **Contact Support**
   - Eniscope support for device issues
   - Check `in_tsdb` flag (should be 'Y')
   - Review device registration status

---

## Next Steps & Recommendations

### Immediate Actions
1. ✅ **Verify Connectivity**: Ensure all 9 channels are transmitting data
2. ✅ **Test Data Collection**: Run analysis script to confirm data availability
3. ✅ **Establish Baseline**: Collect 1-2 weeks of data for baseline analysis
4. ✅ **Configure Alerts**: Set up anomaly detection and alerts

### Short-Term (1-3 Months)
- Analyze usage patterns and establish operational baselines
- Identify energy efficiency opportunities
- Calculate ROI on monitoring investment
- Fine-tune alert thresholds
- Create monthly reporting schedule

### Long-Term (3-12 Months)
- Implement recommended efficiency improvements
- Track savings vs. baseline
- Expand monitoring to additional facilities
- Integrate with predictive maintenance systems
- Build Salesforce customer portal for energy insights

---

## Contact & Support

**Analysis Scripts:** `/backend/scripts/analysis/wilson-center-analysis.js`  
**Documentation:** `DATA_COLLECTION_SUMMARY.md`, `API_RATE_LIMITS.md`  
**API Documentation:** `Core_API_v1.txt`  

For questions about this analysis or to request custom reports, contact your energy solutions team.

---

*This report will be automatically updated once data collection begins from the Wilson Center facility.*

