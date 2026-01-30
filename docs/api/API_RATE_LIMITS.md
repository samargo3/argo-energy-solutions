# Eniscope Core API - Rate Limits & Restrictions

## Overview

This document outlines all rate limits, restrictions, and best practices when using the Eniscope Core API for data analysis.

---

## 1. Data Ingress Limits (Writing Data)

### POST `/dataingress/generic`
- **Maximum rows per request:** 1,000 rows
- **Purpose:** Insert new data

### PUT `/dataingress/generic`
- **Maximum rows per request:** 100 rows  
- **Purpose:** Update existing data (indexed by timestamp + UUID)
- **Note:** PUT will NOT insert new rows, only update existing ones

### Rate Limiting
- **HTTP 429 Response:** "Too Many Requests"
- **Trigger:** Rate limited based on messages in the Rabbit Message Queue (RMQ)
- **Production Limit:** 10,000 messages in queue (as of Feb 2023)
- **Purpose:** Prevent RMQ from crashing due to large unprocessed messages

**Best Practice:**
- If you receive a 429 error, implement exponential backoff and retry logic
- Split large datasets into smaller batches (≤1000 rows for POST, ≤100 for PUT)

---

## 2. Data Retrieval Limits (Reading Data)

### Pagination for Resource Lists

**Endpoints affected:**
- GET `/organizations`
- GET `/devices`
- GET `/channels`
- GET `/customparameters`
- All other collection endpoints

**Limits:**
- **Default records per page:** 20
- **Maximum records per page:** 100
- **Query parameter:** `?limit=100&page=1`

**Example:**
```
GET /devices/?page=6&limit=100
```

### Readings Endpoint

GET `/readings/{channelId}`

**Parameters:**
- `daterange`: Can be pre-defined (e.g., "today", "lastweek") or custom timestamps
- `res`: Resolution (60s, 900s, 1800s, 3600s, 86400s, or "auto")
- `fields`: Array of field codes (e.g., `E`, `V`, `PF`)
- `action`: "summarize", "total", "averageday", "typicalday", "medianday"

**Restrictions on Resolution:**
- Resolution limits vary based on the date range selected
- Using `res=auto` lets the API choose the appropriate resolution
- Longer date ranges may force lower resolutions to prevent timeout

---

## 3. Access Control

- **Hierarchical Access:** Access is restricted based on where your account sits in the organization hierarchy
- **Permissions:** Ensure you have the necessary access rights to perform operations
- **Role-Based:** Some endpoints may be restricted based on user roles

---

## 4. Response Status Codes Related to Limits

| Code | Meaning | Action |
|------|---------|--------|
| 200 | OK | Request successful |
| 401 | Unauthorized | Check authentication credentials |
| 403 | Forbidden | Insufficient permissions for this resource |
| 429 | Too Many Requests | Rate limit hit - implement backoff/retry |
| 500 | Internal Server Error | API issue - contact support if persistent |

---

## 5. Best Practices for Your Analysis Script

### For Reading Data

```javascript
// 1. Use pagination for large datasets
async function getAllDevices() {
  let allDevices = [];
  let page = 1;
  let hasMore = true;
  
  while (hasMore) {
    const response = await api.get(`/devices?page=${page}&limit=100`);
    allDevices = allDevices.concat(response.data.data);
    hasMore = page < response.data.metadata.totalPages;
    page++;
  }
  
  return allDevices;
}

// 2. Request appropriate date ranges
// For large historical analysis, break into chunks
const dateRanges = [
  ['2024-01-01', '2024-03-31'],  // Q1
  ['2024-04-01', '2024-06-30'],  // Q2
  ['2024-07-01', '2024-09-30'],  // Q3
  ['2024-10-01', '2024-12-31']   // Q4
];

for (const [start, end] of dateRanges) {
  const readings = await fetchReadings(channelId, start, end);
  // Process and save
}

// 3. Use appropriate resolution for date range
// Longer ranges = lower resolution
const getAppropriateResolution = (days) => {
  if (days <= 1) return 60;        // 1 minute
  if (days <= 7) return 900;       // 15 minutes
  if (days <= 30) return 3600;     // 1 hour
  return 86400;                     // 1 day
};
```

### For Writing Data (if applicable)

```javascript
// Batch writes to respect limits
async function batchInsertData(records) {
  const BATCH_SIZE = 1000;
  
  for (let i = 0; i < records.length; i += BATCH_SIZE) {
    const batch = records.slice(i, i + BATCH_SIZE);
    
    try {
      await api.post('/dataingress/generic', batch);
      console.log(`Inserted batch ${i / BATCH_SIZE + 1}`);
      
      // Small delay between batches to avoid rate limiting
      await new Promise(resolve => setTimeout(resolve, 100));
      
    } catch (error) {
      if (error.response?.status === 429) {
        // Rate limited - exponential backoff
        console.log('Rate limited, waiting...');
        await new Promise(resolve => setTimeout(resolve, 5000));
        i -= BATCH_SIZE; // Retry this batch
      } else {
        throw error;
      }
    }
  }
}
```

### Error Handling

```javascript
async function apiCallWithRetry(fn, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      if (error.response?.status === 429) {
        // Exponential backoff: 1s, 2s, 4s, 8s...
        const delay = Math.pow(2, i) * 1000;
        console.log(`Rate limited. Retrying in ${delay}ms...`);
        await new Promise(resolve => setTimeout(resolve, delay));
      } else {
        throw error; // Not a rate limit error
      }
    }
  }
  throw new Error('Max retries exceeded');
}
```

---

## 6. Recommendations for Your Analysis

Based on these limits, here's what I recommend for your analysis script:

### ✅ Safe Practices

1. **Paginate all list endpoints** - Use `limit=100` and iterate through pages
2. **Break large date ranges** - Query monthly or quarterly instead of years at a time
3. **Use appropriate resolutions** - Don't request 1-minute data for a full year
4. **Implement retry logic** - Handle 429 errors with exponential backoff
5. **Save data incrementally** - Don't try to fetch everything in one request
6. **Cache session tokens** - Reuse tokens instead of re-authenticating constantly

### ⚠️ Things to Avoid

1. ❌ Requesting all channels with 1-minute resolution for a full year
2. ❌ Making parallel requests without rate limiting
3. ❌ Ignoring pagination - only fetching first 20 records
4. ❌ Not handling 429 errors
5. ❌ Re-authenticating for every API call

### 📊 Suggested Data Collection Strategy

**For comprehensive analysis:**

```bash
# Day 1: Collect metadata (fast)
- Organizations
- Devices  
- Channels
- Custom parameters

# Day 2+: Collect readings incrementally
- Start with recent data (last month, hourly resolution)
- Gradually expand backwards (quarterly, daily resolution)
- Store results in JSON/CSV for offline analysis
- Resume if interrupted using timestamps
```

---

## Summary

| Operation | Limit | Notes |
|-----------|-------|-------|
| POST ingress | 1,000 rows/request | Insert new data |
| PUT ingress | 100 rows/request | Update existing data |
| List endpoints | 100 records/page | Use pagination |
| Rate limit queue | 10,000 messages | Returns 429 when full |
| Session token | Reusable | Don't re-auth constantly |
| Date range + resolution | Varies | Longer ranges = lower resolution |

**Key Takeaway:** The API is designed for incremental, paginated access. Structure your analysis to work in batches rather than trying to pull everything at once.

