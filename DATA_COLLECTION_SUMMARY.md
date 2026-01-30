# Data Collection Summary

## ✅ API Connection Successful!

Your Eniscope Core API connection is working properly. The analysis script has successfully:

### Data Retrieved

1. **Organizations:** 2 organizations found
   - Primary: **Argo Energy Solutions LLC** (ID: 23271)
   - Data saved to: `data/organizations.json`

2. **Devices:** 9 devices found for organization 23271
   - Data saved to: `data/devices-org-23271.json`

3. **Channels:** 20 channels found for organization 23271
   - Data saved to: `data/channels-org-23271.json`
   - Sample channel: "Dryer" (ID: 158694)

4. **Readings:** Tested with channel 158694
   - Date range: Last week
   - Resolution: 1 hour
   - Result: 0 readings (channel may not have data for this period)

---

## 📊 Available Data Files

All data has been saved as JSON files in the `/data` directory:

```
/data/
├── organizations.json          # Organization metadata
├── devices-org-23271.json      # All devices for Argo Energy Solutions
├── channels-org-23271.json     # All 20 channels/metering points
└── readings-channel-158694.json # Sample readings (empty for test period)
```

---

## 🔄 Next Steps for Data Analysis

### 1. Explore Your Channels

You have **20 channels** available! Check `channels-org-23271.json` to see:
- Channel names (e.g., "Dryer", etc.)
- Channel IDs (dataChannelId)
- Device types and configurations
- What each channel monitors

### 2. Get Readings for Different Channels

The sample channel had no data. Try other channels:

```bash
# Edit the script or create a new one to fetch specific channels
node scripts/analyze-energy-data.js
```

Or create a custom script to loop through all channels:

```javascript
// Example: Fetch readings for all channels
for (const channel of channelList) {
  const readings = await client.getReadings(channel.dataChannelId, {
    fields: ['E', 'P', 'V'],  // Energy, Power, Voltage
    daterange: 'today',       // Try different ranges
    res: '900',               // 15-minute resolution
    action: 'summarize'
  });
  // Process readings...
}
```

### 3. Try Different Date Ranges

Available pre-defined ranges:
- `today` - Today's data
- `yesterday` - Yesterday
- `thisweek` - Current week
- `lastweek` - Previous week
- `thismonth` - Current month
- `lastmonth` - Previous month
- `7days` - Last 7 days
- `30days` - Last 30 days

Custom ranges:
```javascript
daterange: ['2024-12-01', '2024-12-31']  // December 2024
```

### 4. Adjust Resolution Based on Date Range

- **1 minute (60):** For hourly or daily analysis
- **15 minutes (900):** For weekly analysis
- **1 hour (3600):** For monthly analysis (what we used)
- **1 day (86400):** For yearly analysis

---

## 📈 Data Analysis Ideas

With your data, you can analyze:

1. **Energy Consumption Patterns**
   - Peak usage times
   - Daily/weekly/monthly trends
   - Compare usage across different channels

2. **Cost Analysis**
   - Energy costs per device/channel
   - Identify high-consumption equipment
   - Time-of-use rate optimization

3. **Efficiency Metrics**
   - Power factor analysis
   - Voltage stability
   - Load distribution

4. **Reporting for Salesforce**
   - Aggregate data for customer dashboards
   - Alert thresholds for anomalies
   - Monthly/quarterly summaries

---

## 🛠️ Modifying the Script

The analysis script is located at: `scripts/analyze-energy-data.js`

Key methods you can use:

```javascript
// Get all organizations
const orgs = await client.getOrganizations();

// Get devices for an organization
const devices = await client.getDevices(organizationId);

// Get channels (metering points)
const channels = await client.getChannels(organizationId);

// Get readings for a channel
const readings = await client.getReadings(channelId, {
  fields: ['E', 'P', 'V', 'I', 'PF'],  // What to measure
  daterange: 'lastweek',                // When
  res: '3600',                          // Resolution (seconds)
  action: 'summarize'                   // Type of aggregation
});
```

---

## 🔍 Inspecting Your Data

To view the data in a readable format:

```bash
# Pretty print any JSON file
cat data/channels-org-23271.json | python3 -m json.tool | less

# Search for specific channels
cat data/channels-org-23271.json | grep -i "channelName"

# Count channels
cat data/channels-org-23271.json | grep -c "dataChannelId"
```

---

## ⚠️ API Limits to Remember

1. **Rate Limiting:** The script handles HTTP 429 errors with automatic retries
2. **Pagination:** Maximum 100 records per page (script handles this)
3. **Resolution Restrictions:** Longer date ranges require lower resolution
4. **Session Tokens:** Reused automatically for efficiency

---

## 📋 Recommended Workflow

1. **Explore metadata** (you've done this! ✓)
   - Organizations, devices, channels

2. **Identify active channels**
   - Check which channels have recent data
   - Look at `registered` and `expires` timestamps

3. **Fetch recent data first**
   - Start with `daterange: 'today'` or `'lastweek'`
   - Use hourly or 15-minute resolution

4. **Build historical dataset**
   - Gradually fetch older data
   - Use daily resolution for long periods
   - Save incrementally to JSON/CSV

5. **Create aggregations**
   - Daily summaries
   - Weekly/monthly totals
   - Peak demand calculations

6. **Prepare for Salesforce integration**
   - Format data for Salesforce objects
   - Create summary records
   - Set up sync schedule

---

## 🔗 Integration with Salesforce

Once you've analyzed the data structure, refer to:
- `SALESFORCE_INTEGRATION_GUIDE.md` - Full integration architecture
- `API_RATE_LIMITS.md` - Best practices and limits

You can now confidently build:
1. Apex callouts to fetch live data
2. Scheduled jobs to sync historical data
3. Custom Lightning components to display energy metrics
4. Reports and dashboards for customers

---

## 💡 Tips

- **Start small:** Test with one channel before fetching all 20
- **Check timestamps:** Some channels may be inactive or expired
- **Use appropriate resolutions:** More data ≠ better (respect rate limits)
- **Save incrementally:** Don't try to fetch years of minute-by-minute data at once
- **Document findings:** Note which channels are most relevant for your use case

---

## 🆘 Troubleshooting

### No readings returned?
- Check if the channel is active (`status: "1"`)
- Check expiration date (`expires` timestamp)
- Try a different date range (maybe `'today'` or `'yesterday'`)
- Verify the channel actually collects the fields you're requesting

### Rate limited (429)?
- The script handles this automatically with retries
- If persistent, add longer delays between requests
- Consider fetching data during off-peak hours

### Need more channels?
- Check if there are other organizations in your account
- Verify your access permissions in the Eniscope platform

---

## 📞 Support

- **API Documentation:** `Core_API_v1.txt`
- **Rate Limits Guide:** `API_RATE_LIMITS.md`
- **Salesforce Integration:** `SALESFORCE_INTEGRATION_GUIDE.md`

Happy analyzing! 🎉

