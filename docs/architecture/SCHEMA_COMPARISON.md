# Database Schema Comparison

**Date:** February 5, 2026  
**Comparison:** Current Setup vs. Suggested "Organization Mapping" Approach

---

## 📊 Current Schema (What You Have)

```
organizations (1)
    ↓
    ├──> devices (M) - Hardware layer
    │       ↓
    │       └──> channels (M) - Monitoring points
    │               ↓
    │               └──> readings (M) - Time-series data
    │
    └──> channels (M) - Direct link for channels without device info
            ↓
            └──> readings (M)
```

**Tables:**
- `organizations` (1 record) - Buildings/Sites
- `devices` (17 records) - Physical Eniscope hardware with UUID
- `channels` (20 records) - Metering points (what API calls channels)
- `readings` (298,605 records) - 15-minute interval data

**Key Features:**
- ✅ Explicit device tracking (ID, name, type, UUID)
- ✅ Full audit trail (created_at, updated_at timestamps)
- ✅ Comprehensive readings (energy, power, voltage, current, PF, temp, humidity)
- ✅ Uses Eniscope API terminology (organizations, channels)
- ✅ Supports complex hierarchies (orgs → devices → channels → readings)

---

## 🎯 Suggested Schema (From Prompt)

```
sites (M)
    ↓
    └──> meters (M) - Monitoring points
            ↓
            └──> readings (M) - Time-series data (implied)
```

**Tables:**
- `sites` - Buildings/Organizations
- `meters` - Metering points with `site_id` foreign key
- Helper: `get_site_for_meter(meter_id)` function

**Key Features:**
- ✅ Simpler structure (fewer tables)
- ✅ Business-friendly terminology (sites, meters)
- ✅ Helper function for quick lookups
- ❌ No explicit device layer
- ❌ Doesn't capture hardware details

---

## 🔍 Side-by-Side Comparison

| Aspect | Current Schema | Suggested Schema | Winner |
|--------|---------------|------------------|--------|
| **Terminology** | Technical (organizations, channels) | Business-friendly (sites, meters) | Suggested |
| **Hardware Tracking** | Yes (devices table with UUID) | No | Current |
| **Simplicity** | 4-table hierarchy | 2-table hierarchy | Suggested |
| **Detail Level** | High (device info, full readings) | Moderate (basic tracking) | Current |
| **API Alignment** | Perfect (matches Eniscope naming) | Conceptual (business terms) | Current |
| **Query Complexity** | Requires JOINs through devices | Direct site→meter JOIN | Suggested |
| **Scalability** | Handles complex org structures | Good for simple setups | Current |
| **Already Implemented** | 100% complete | ~70% (missing terminology/helper) | Current |

---

## ✅ What's Already Implemented

Your current schema **already provides** everything the suggestion requires:

### 1. Sites Table ✅
```sql
-- You have: organizations
-- Suggested: sites
-- Mapping: organizations = sites
```
Your `organizations` table **is** the sites table, just with API-aligned naming.

### 2. Meters with Site Foreign Key ✅
```sql
-- You have: channels.organization_id → organizations.organization_id
-- Suggested: meters.site_id → sites.site_id
-- Mapping: channels = meters, organization_id = site_id
```
Your `channels` table **is** the meters table with proper foreign key.

### 3. Readings Connection ✅
```sql
-- You have: readings.channel_id → channels.channel_id
-- Working perfectly with 298,605 readings
```

### 4. Error Handling ✅
Your ingestion script already handles:
- Missing organizations
- Empty channel lists
- API failures
- Rate limiting

---

## ❌ What's Missing

### 1. Helper Function `get_site_for_meter()`
**Current:** You have to manually JOIN
```python
# Current approach
cur.execute("""
    SELECT c.channel_id, c.channel_name, o.organization_name
    FROM channels c
    JOIN organizations o ON c.organization_id = o.organization_id
    WHERE c.channel_id = %s
""", (channel_id,))
```

**Suggested:** A dedicated helper function
```python
# Suggested approach
site_info = get_site_for_meter(meter_id=158694)
# Returns: {"site_id": "23271", "site_name": "Wilson Center", ...}
```

### 2. Business-Friendly Terminology
- Current uses `organizations` and `channels` (API terms)
- Suggested uses `sites` and `meters` (business terms)

---

## 🤔 Should You Refactor?

### ✅ Reasons TO Refactor

1. **Business Clarity**
   - "Sites" and "Meters" are more intuitive for non-technical stakeholders
   - Easier to explain to customers and management
   - Better alignment with energy industry terminology

2. **Simplified Queries**
   - Remove device layer from most queries (if you don't need hardware details)
   - Direct site→meter JOINs are simpler

3. **Helper Function**
   - `get_site_for_meter()` makes common lookups easier
   - Better developer experience

### ❌ Reasons NOT TO Refactor

1. **Everything Works**
   - Current schema is solid and battle-tested
   - 298K+ readings successfully stored
   - All exports working perfectly

2. **You'd Lose Device Tracking**
   - Current schema captures hardware details (UUID, type, name)
   - Useful for troubleshooting and hardware inventory
   - Just implemented this feature (today!)

3. **API Alignment**
   - Current naming matches Eniscope API perfectly
   - Reduces cognitive load when debugging
   - No mental translation needed

4. **Significant Work Required**
   - Rename 4+ tables
   - Update all Python scripts (ingestion, exports, analytics)
   - Rewrite all SQL queries
   - Update documentation
   - Risk of introducing bugs

---

## 💡 Recommended Approach: Hybrid Solution

**Keep current schema, add convenience features:**

### Option 1: Add Helper Function (2 minutes)
Add to your Python scripts without changing schema:

```python
def get_site_for_meter(channel_id: int) -> dict:
    """
    Get site information for a specific meter/channel.
    
    Returns:
        {
            'site_id': '23271',
            'site_name': 'Wilson Center',
            'meter_id': 158694,
            'meter_name': 'Dryer',
            'device_id': 111936,
            'device_name': 'Dryer',
            'device_uuid': '80342815FC990001'
        }
    """
    cur.execute("""
        SELECT 
            c.channel_id as meter_id,
            c.channel_name as meter_name,
            c.organization_id as site_id,
            o.organization_name as site_name,
            c.device_id,
            d.device_name,
            d.serial_number as device_uuid
        FROM channels c
        JOIN organizations o ON c.organization_id = o.organization_id
        LEFT JOIN devices d ON c.device_id = d.device_id
        WHERE c.channel_id = %s
    """, (channel_id,))
    
    row = cur.fetchone()
    if not row:
        return None
    
    return {
        'meter_id': row[0],
        'meter_name': row[1],
        'site_id': row[2],
        'site_name': row[3],
        'device_id': row[4],
        'device_name': row[5],
        'device_uuid': row[6]
    }
```

### Option 2: Create Database Views (5 minutes)
Add business-friendly aliases without changing tables:

```sql
-- Create view: sites (alias for organizations)
CREATE VIEW sites AS
SELECT 
    organization_id as site_id,
    organization_name as site_name,
    address,
    city,
    postcode,
    timezone,
    created_at,
    updated_at
FROM organizations;

-- Create view: meters (alias for channels with device info)
CREATE VIEW meters AS
SELECT 
    c.channel_id as meter_id,
    c.channel_name as meter_name,
    c.organization_id as site_id,
    c.device_id,
    d.device_name,
    d.device_type,
    d.serial_number as device_uuid,
    c.channel_type,
    c.unit,
    c.created_at,
    c.updated_at
FROM channels c
LEFT JOIN devices d ON c.device_id = d.device_id;
```

**Benefits:**
- ✅ Keep all existing code working
- ✅ Get business-friendly names
- ✅ Zero migration risk
- ✅ Can use either terminology
- ✅ Views are just queries - no data duplication

### Option 3: Full Refactor (4-8 hours)
Only if you have strong business requirement for the simpler model.

---

## 📋 My Recommendation

**Keep your current schema and add Option 1 + Option 2:**

1. ✅ Add `get_site_for_meter()` helper function to your Python scripts
2. ✅ Create SQL views for business-friendly aliases
3. ✅ Keep the device layer - it's valuable for troubleshooting
4. ✅ Update documentation to mention both terminologies

**Why:**
- Your current schema is **more powerful** (tracks hardware)
- The suggested schema is **already implemented** (just different names)
- Views give you **best of both worlds** (technical + business terms)
- Helper function provides **convenience** without risk
- **Zero downtime**, no data migration needed

---

## 📊 Current vs. Suggested: Feature Parity

| Feature | Current | Suggested | Comparison |
|---------|---------|-----------|------------|
| Store sites/organizations | ✅ Yes | ✅ Yes | **Equal** |
| Store meters/channels | ✅ Yes | ✅ Yes | **Equal** |
| Site-to-meter relationship | ✅ Yes | ✅ Yes | **Equal** |
| Track hardware devices | ✅ Yes | ❌ No | **Current Better** |
| Business-friendly naming | ⚠️ No | ✅ Yes | **Suggested Better** |
| Helper function | ❌ No | ✅ Yes | **Suggested Better** |
| API alignment | ✅ Perfect | ⚠️ Conceptual | **Current Better** |
| Query simplicity | ⚠️ Moderate | ✅ Simple | **Suggested Better** |
| Implementation status | ✅ 100% | ⚠️ 70% | **Current Better** |

**Overall Winner:** Current schema + Views/Helpers = Best solution

---

## 🎯 Next Steps

Choose your path:

### Path A: Minimal (Recommended) - 5 minutes
1. Create database views (sites, meters)
2. Add `get_site_for_meter()` helper function
3. Update docs to mention aliases

### Path B: Do Nothing - 0 minutes
Your current setup already does everything suggested, just with different naming.

### Path C: Full Refactor - 4-8 hours
Only if business stakeholders strongly prefer simpler terminology and you don't need device tracking.

---

**My Strong Recommendation:** Path A  
You get all benefits of both approaches with minimal effort and zero risk.

Would you like me to implement Path A (views + helper function) for you?
