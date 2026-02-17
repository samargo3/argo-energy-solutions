# Tableau Quick Start - Neon Database

## ⚡ Connect in 5 Minutes

Your energy data is already in Neon PostgreSQL. Connecting Tableau is simple:

### Step 1: Get Connection Info from `.env`

```env
DATABASE_URL=postgresql://user:password@ep-xxx-xxx.us-east-2.aws.neon.tech:5432/neondb?sslmode=require
```

Break it down:
- **Host:** `ep-xxx-xxx.us-east-2.aws.neon.tech`
- **Port:** `5432`
- **Database:** `neondb`
- **User:** `your_username`
- **Password:** `your_password`

### Step 2: Connect Tableau

1. Open **Tableau Desktop**
2. Click **More...** → **PostgreSQL**
3. Enter connection details:
   ```
   Server: [your-host].neon.tech
   Port: 5432
   Database: neondb
   Username: [your-username]
   Password: [your-password]
   ☑️ Require SSL
   ```
4. Click **Sign In**

### Step 3: Add Tables

Drag these to canvas (Tableau will auto-join them):
- `readings` (151,742+ energy readings)
- `channels` (17 active channels)
- `organizations` (site info)

### Step 4: Create Your First Viz

**Power Timeline:**
- Drag `Timestamp` to Columns
- Drag `Power Kw` to Rows
- Drag `Channel Name` to Color
- Done! You have a real-time energy chart

---

## 🎯 What You Can Do

### Real-Time Dashboards
- Live connection to Neon
- Always shows latest data
- No manual refresh needed

### Historical Analysis
- Extract mode for fast performance
- Scheduled daily refresh (3 AM recommended)
- Works offline

### Pre-Built Calculations

```
// Daily Energy
{ FIXED [Channel Name], DATETRUNC('day', [Timestamp]) : SUM([Energy Kwh]) }

// Estimated Cost ($0.12/kWh)
SUM([Energy Kwh]) * 0.12

// After-Hours Usage
[Power Kw] > 1 AND DATEPART('hour', [Timestamp]) > 18

// Power Factor Status
IF [Power Factor] >= 0.95 THEN "Excellent" ELSE "Poor" END
```

---

## 📊 5 Dashboard Templates

1. **Real-Time Monitoring** - Current power by channel
2. **Daily Energy Report** - Consumption and costs
3. **HVAC Performance** - RTU/AHU specific metrics
4. **Cost Analysis** - Budget tracking and trends
5. **Power Quality** - Voltage and power factor

---

## 🔧 Quick Tips

### For Best Performance
- Use **Live Connection** for dashboards (real-time)
- Use **Extract** for analysis (faster, offline)
- Filter to last 30-90 days for speed
- Schedule extract refresh daily at 3 AM

### Security
- Create read-only Tableau user in Neon
- Never share database admin credentials
- Embed credentials when publishing to server

### Common Issues

**"Can't connect"**
→ Check Neon project is active, SSL is enabled

**"Slow queries"**
→ Use extracts, add date filters, last 30 days

**"Data not updating"**
→ Check GitHub Actions daily sync is running

---

## 📚 Full Documentation

**Complete Guide:** [`docs/guides/integrations/NEON_TABLEAU_DIRECT_CONNECT.md`](docs/guides/integrations/NEON_TABLEAU_DIRECT_CONNECT.md)

Includes:
- Detailed setup instructions
- 5 complete dashboard designs
- Performance optimization
- Security best practices
- Troubleshooting guide
- 20+ calculated field formulas

---

## ✅ Why Direct Connection is Best

| Feature | Neon Direct | CSV Export |
|---------|-------------|------------|
| Setup Time | 5 min | 2 min |
| Real-Time Data | ✅ Yes | ❌ No |
| Maintenance | ✅ None | ❌ Manual |
| Multiple Users | ✅ Yes | ⚠️ Limited |
| Data Volume | ✅ Unlimited | ⚠️ Limited |
| Automated Refresh | ✅ Yes | ❌ No |

**Verdict:** Neon direct connection is the clear winner! 🏆

---

## 🎉 Your Data is Ready

- ✅ 151,742 readings in database
- ✅ 17 active channels
- ✅ Complete history since Nov 5, 2025
- ✅ Daily updates via GitHub Actions
- ✅ Production-ready schema

**Start visualizing now!**

---

**Questions?** See full guide or run `npm run py:validate` to check database status.
