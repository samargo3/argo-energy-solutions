# API Connection Guide - Extracting Info from Core API v1.pdf

This guide will help you extract the necessary information from the Best.Energy API documentation to configure your connection.

## 📋 Information to Extract from the PDF

Open `Core API v1.pdf` and look for the following sections. Write down what you find:

### 1. Base URL / API Endpoint
Look for sections like:
- "Base URL"
- "API Endpoint" 
- "Server URL"
- "Host"
- "API Gateway"

**What to look for:**
```
Base URL: https://api.best.energy/v1
OR
Endpoint: https://api.bestenergy.com
```

**Update in `.env`:**
```env
VITE_BEST_ENERGY_API_URL=<the base URL you found>
```

---

### 2. Authentication Method
Look for sections about:
- "Authentication"
- "Authorization"
- "API Keys"
- "Bearer Token"
- "OAuth"

**Common formats:**
- **Bearer Token:** `Authorization: Bearer <token>`
- **API Key in Header:** `X-API-Key: <key>` or `API-Key: <key>`
- **API Key in Query:** `?api_key=<key>`

**What to note:**
- Where to get the API key/token
- How to format it in the request
- Any expiration or refresh requirements

---

### 3. API Endpoints for Energy Data

Look for sections like:
- "Endpoints"
- "Resources"
- "API Reference"
- "Getting Started"

**Key endpoints to find:**

#### a) Get Customers
```
GET /customers
GET /api/v1/customers
GET /v1/customers
```

#### b) Get Customer Energy Consumption
```
GET /customers/{id}/consumption
GET /customers/{id}/energy
GET /api/v1/customers/{id}/consumption
GET /v1/energy/customer/{id}
```

#### c) Get Grouped/Aggregated Data
```
GET /customers/{id}/consumption/grouped
GET /customers/{id}/energy/aggregated
GET /v1/energy/{id}/daily
```

#### d) Get Sites
```
GET /customers/{id}/sites
GET /sites?customer_id={id}
GET /v1/sites
```

**What to note:**
- Exact endpoint paths
- Required path parameters (like `{id}`)
- Query parameters (like `startDate`, `endDate`, `page`, `pageSize`)

---

### 4. Request Parameters

Look for parameter documentation:
- Query parameters
- Path parameters
- Request body structure

**Common parameters:**
- Date ranges: `startDate`, `endDate`, `from`, `to`
- Pagination: `page`, `pageSize`, `limit`, `offset`
- Filtering: `siteId`, `customerId`, `groupBy`

**Date format to note:**
- ISO 8601: `2024-01-01T00:00:00Z`
- Unix timestamp: `1704067200`
- Simple date: `2024-01-01`

---

### 5. Response Structure

Look for response examples:
- JSON structure
- Field names
- Data types

**What to check:**
- How is data wrapped? (e.g., `{ data: [...] }` or just `[...]`)
- Field names (e.g., `value`, `kwh`, `consumption`)
- Pagination structure (e.g., `{ items: [], total: 100 }`)

---

## 🔧 Steps to Update Your Configuration

Once you've extracted the information:

### Step 1: Update `.env` file

```env
VITE_BEST_ENERGY_API_URL=<base URL from PDF>
VITE_BEST_ENERGY_API_KEY=<your API key>
VITE_API_TIMEOUT=30000
```

### Step 2: Update Authentication in `src/services/api/apiClient.ts`

Based on the authentication method you found:

**Bearer Token (most common):**
```typescript
headers: {
  'Content-Type': 'application/json',
  'Authorization': `Bearer ${API_KEY}`,
}
```

**API Key in Header:**
```typescript
headers: {
  'Content-Type': 'application/json',
  'X-API-Key': API_KEY,  // or whatever header name the PDF specifies
}
```

**API Key in Query (less common):**
```typescript
// Add to each request
params: {
  api_key: API_KEY,
}
```

### Step 3: Update Endpoints in `src/services/api/bestEnergyApi.ts`

Update each function with the correct endpoint paths from the PDF:

```typescript
// Example: If PDF says the endpoint is /v1/customers
export const getCustomers = async () => {
  const response = await apiClient.get('/v1/customers');  // Updated
  return response.data;
};

// Example: If PDF says /api/v1/energy/{customerId}
export const getCustomerEnergyConsumption = async (customerId: string, params) => {
  const response = await apiClient.get(`/api/v1/energy/${customerId}`, {  // Updated
    params,
  });
  return response.data;
};
```

### Step 4: Update Query Parameters

If the PDF uses different parameter names:

```typescript
// Example: If PDF uses 'from' and 'to' instead of 'startDate' and 'endDate'
const response = await apiClient.get(`/customers/${customerId}/consumption`, {
  params: {
    from: params.startDate,    // Map to API's expected name
    to: params.endDate,
  },
});
```

### Step 5: Update TypeScript Types

If the response structure is different, update `src/types/energy.ts`:

```typescript
// Example: If API returns 'kwh' instead of 'value'
export interface EnergyConsumption {
  id: string;
  siteId: string;
  customerId: string;
  timestamp: string;
  kwh: number;  // Changed from 'value' based on PDF
  cost?: number;
}
```

---

## 📝 Quick Checklist

Use this checklist as you read through the PDF:

- [ ] Found base URL: `_______________`
- [ ] Found authentication method: `_______________`
- [ ] Found API key location/format: `_______________`
- [ ] Found customers endpoint: `_______________`
- [ ] Found energy consumption endpoint: `_______________`
- [ ] Found grouped data endpoint: `_______________`
- [ ] Found sites endpoint: `_______________`
- [ ] Found date parameter names: `_______________`
- [ ] Found date format: `_______________`
- [ ] Found response structure: `_______________`

---

## 🆘 What to Do After Reading the PDF

1. **Fill out the checklist above** with information from the PDF
2. **Update the `.env` file** with the base URL and your API key
3. **Update `src/services/api/apiClient.ts`** with the correct authentication method
4. **Update `src/services/api/bestEnergyApi.ts`** with the correct endpoint paths
5. **Test the connection** using the `/api-test` page

---

## 💡 Common PDF Sections to Search For

Use Ctrl+F (Cmd+F on Mac) to search the PDF for:
- "authentication"
- "authorization"
- "base url"
- "endpoint"
- "getting started"
- "quick start"
- "api key"
- "bearer"
- "customers"
- "consumption"
- "energy"

---

## 📞 Need Help?

If you find the information in the PDF but aren't sure how to apply it:
1. Share the relevant sections from the PDF
2. I can help update the code based on what you found
3. Or describe what you found and I'll guide you through the updates



