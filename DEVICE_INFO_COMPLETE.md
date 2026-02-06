# Device Information Integration - Complete ✅

**Date:** February 5, 2026  
**Status:** Completed and Verified

---

## 🎯 Objective

Include device information (ID, name, type, UUID) from the Eniscope API in all Tableau exports and database storage.

---

## ✅ Changes Made

### 1. **Database Schema** 
The existing database schema already had proper support:
- `devices` table with columns: `device_id`, `device_name`, `device_type`, `serial_number` (for UUID)
- `channels` table with `device_id` foreign key

### 2. **Data Ingestion (`ingest_to_postgres.py`)**

**New Method:** `upsert_device()`
```python
def upsert_device(self, device_id: int, device_name: str, device_type: str, 
                 uuid: str, org_id: str) -> bool:
    """Insert or update device."""
    # Stores device information with ON CONFLICT handling
```

**Updated Method:** `upsert_channel()`
- Now accepts `device_id` parameter
- Links channels to their parent devices

**Main Ingestion Loop:**
- Extracts device information from Eniscope API response:
  - `deviceId` → Device ID
  - `deviceName` → Device Name
  - `deviceTypeName` → Device Type
  - `uuId` → Device UUID (stored in `serial_number`)
- Calls `upsert_device()` before `upsert_channel()`
- Links channel to device via foreign key

### 3. **Tableau Exports (`export_for_tableau.py`)**

Updated all export queries to include device information via LEFT JOIN with devices table:

**Files Updated:**
1. `tableau_readings.csv` - Added device columns
2. `tableau_channel_summary.csv` - Added device columns
3. `tableau_custom_[dates].csv` - Added device columns

**New CSV Columns:**
- Device ID
- Device Name
- Device Type
- Device UUID

**Sample SQL:**
```sql
SELECT 
    r.timestamp,
    r.channel_id,
    c.channel_name,
    c.device_id,           -- NEW
    d.device_name,         -- NEW
    d.device_type,         -- NEW
    d.serial_number as device_uuid,  -- NEW
    c.organization_id,
    o.organization_name,
    r.energy_kwh,
    ...
FROM readings r
JOIN channels c ON r.channel_id = c.channel_id
LEFT JOIN devices d ON c.device_id = d.device_id  -- NEW
JOIN organizations o ON c.organization_id = o.organization_id
```

### 4. **Documentation (`exports/tableau/README.md`)**
- Added section explaining device information fields
- Updated file descriptions to mention device info
- Updated last modified date

---

## 📊 Verification Results

### Database Status (Wilson Center - Site 23271)
- ✅ **17 devices** stored in `devices` table
- ✅ **18 channels** linked to devices via `device_id`
- ✅ All devices have:
  - Device ID (e.g., 111936)
  - Device Name (e.g., "Dryer", "A/C 3")
  - Device Type (e.g., "Eniscope 8 Hybrid Metering Point")
  - UUID (e.g., "80342815FC990001")

### Export Verification
- ✅ `tableau_readings.csv` - **278,063 readings** with device info
- ✅ `tableau_channel_summary.csv` - **17 channels** with device info
- ✅ `tableau_custom_2026-02-01_2026-02-02.csv` - **3,706 readings** with device info

**Sample Data Row:**
```csv
Timestamp,Channel ID,Channel Name,Device ID,Device Name,Device Type,Device UUID,Organization ID,Organization,...
2026-02-05 08:56:20+00:00,158694,Dryer,111936,Dryer,Eniscope 8 Hybrid Metering Point,80342815FC990001,23271,Site 23271,...
```

---

## 🔄 How It Works

```
┌─────────────────┐
│  Eniscope API   │
│   (channels)    │
└────────┬────────┘
         │ Returns device info:
         │ - deviceId, uuId
         │ - deviceName, deviceTypeName
         ▼
┌─────────────────┐
│  ingest_to_     │
│  postgres.py    │
├─────────────────┤
│ 1. upsert_device│──────┐
│ 2. upsert_channel│      │
└─────────────────┘      │
                         ▼
                 ┌──────────────┐
                 │  PostgreSQL  │
                 ├──────────────┤
                 │  devices     │
                 │  channels    │
                 │  readings    │
                 └──────┬───────┘
                        │
                        ▼
                ┌───────────────┐
                │  export_for_  │
                │  tableau.py   │
                ├───────────────┤
                │ JOIN devices  │
                │ with channels │
                └───────┬───────┘
                        │
                        ▼
                ┌───────────────┐
                │  Tableau CSV  │
                │  with device  │
                │  information  │
                └───────────────┘
```

---

## 📝 Usage

### Generate Exports with Device Info

**Standard Export (last 90 days):**
```bash
npm run py:export:tableau
```

**Custom Date Range:**
```bash
npm run py:export:tableau:custom -- 2026-02-01 2026-02-05
```

### Access Device Data in Tableau

All CSV files now include device columns that can be used for:
- **Filtering** by device type or name
- **Grouping** reports by physical device
- **Identifying** specific hardware by UUID
- **Tracking** equipment-level performance

---

## 🎓 Next Steps

### For Users:
1. ✅ Device information is automatically captured during daily sync
2. ✅ All new exports include device data
3. ✅ Use device columns in Tableau for equipment-specific analysis

### For Developers:
- The `devices` table can be extended with additional fields:
  - `firmware_version` (available in API)
  - `last_seen` timestamp
  - Installation/decommission dates
- Device information is automatically updated on each ingestion

---

## 🔍 Technical Details

### API Fields Captured
From Eniscope `/channels` endpoint:
- `deviceId` → `devices.device_id`
- `deviceName` → `devices.device_name`
- `deviceTypeName` → `devices.device_type`
- `uuId` → `devices.serial_number`

### Database Relationships
```
devices (1) ──< (M) channels (1) ──< (M) readings
     │                   │
     └───────────────────┘
     Foreign Key: device_id
```

### Idempotency
- All device upserts use `ON CONFLICT DO UPDATE`
- Safe to re-run ingestion multiple times
- Device information automatically stays synchronized

---

**Implementation:** Complete ✅  
**Tested:** Yes ✅  
**Documented:** Yes ✅  
**Ready for Production:** Yes ✅
