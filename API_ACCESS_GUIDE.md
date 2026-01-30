# API Access Guide - Accessing Energy Data

This guide walks you through the steps to access energy data from the Best.Energy API.

## Step 1: Configure Environment Variables

Create a `.env` file in the root directory of your project:

```env
VITE_BEST_ENERGY_API_URL=https://api.best.energy
VITE_BEST_ENERGY_API_KEY=your_actual_api_key_here
VITE_API_TIMEOUT=30000
```

**Important:** 
- Replace `your_actual_api_key_here` with your actual Best.Energy API key
- Replace the API URL if your endpoint is different
- Restart your development server after creating/updating `.env`

## Step 2: Update API Endpoints (If Needed)

The current API endpoints in `src/services/api/bestEnergyApi.ts` are placeholders. You need to:

1. **Review the Best.Energy API documentation** (`Core API v1.pdf`)
2. **Identify the actual endpoints** for:
   - Getting customers
   - Getting energy consumption data
   - Getting grouped/aggregated data
3. **Update the endpoints** in `src/services/api/bestEnergyApi.ts`

### Example: Updating an Endpoint

If your API endpoint is `/v1/customers/{id}/energy` instead of `/customers/{id}/consumption`:

```typescript
// In src/services/api/bestEnergyApi.ts
export const getCustomerEnergyConsumption = async (
  customerId: string,
  params: DateRangeParams & PaginationParams
): Promise<PaginatedResponse<EnergyConsumption>> => {
  const response = await apiClient.get(`/v1/customers/${customerId}/energy`, {
    params,
  });
  return response.data;
};
```

## Step 3: Adjust Data Types (If Needed)

If your API returns data in a different structure, update the types in `src/types/energy.ts`:

```typescript
// Example: If API returns 'kwh' instead of 'value'
export interface EnergyConsumption {
  id: string;
  siteId: string;
  customerId: string;
  timestamp: string;
  kwh: number;  // Changed from 'value'
  cost?: number;
  unit?: string;
}
```

If you update types, you'll also need to update:
- `src/services/analytics/statistics.ts` - to use the correct field names
- Components that use the data - to access the correct properties

## Step 4: Update Authentication (If Needed)

The current setup uses Bearer token authentication. If your API uses a different method, update `src/services/api/apiClient.ts`:

### API Key in Header (Alternative)
```typescript
headers: {
  'Content-Type': 'application/json',
  'X-API-Key': API_KEY,  // Instead of Authorization Bearer
}
```

### Basic Auth
```typescript
auth: {
  username: 'your_username',
  password: 'your_password',
}
```

## Step 5: Access Data in Your Components

### Option A: Using React Hooks (Recommended)

The easiest way is to use the pre-built hooks:

```typescript
import { useCustomerEnergyData } from '../hooks/useEnergyData';
import { useCustomers } from '../hooks/useCustomerData';

function MyComponent() {
  // Get all customers
  const { data: customers, isLoading, error } = useCustomers();
  
  // Get energy data for a specific customer
  const customerId = 'customer-123';
  const { data: energyData, isLoading: loadingEnergy } = useCustomerEnergyData(
    customerId,
    {
      startDate: '2024-01-01T00:00:00Z',
      endDate: '2024-01-31T23:59:59Z',
    }
  );

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      <h2>Customers: {customers?.items.length}</h2>
      <h3>Energy Data Points: {energyData?.items.length}</h3>
    </div>
  );
}
```

### Option B: Direct API Calls

You can also call the API functions directly:

```typescript
import { bestEnergyApi } from '../services/api/bestEnergyApi';
import { getDateRange } from '../utils/dateUtils';

async function fetchEnergyData() {
  try {
    const customerId = 'customer-123';
    const dateRange = getDateRange('month');
    
    const data = await bestEnergyApi.getCustomerEnergyConsumption(
      customerId,
      dateRange
    );
    
    console.log('Energy data:', data);
    return data;
  } catch (error) {
    console.error('Error fetching data:', error);
  }
}
```

## Step 6: Test the Connection

### Method 1: Use Browser DevTools

1. Open your application in the browser
2. Open DevTools (F12)
3. Go to the Network tab
4. Navigate to a page that fetches data (e.g., Dashboard or Customers)
5. Look for API requests and check:
   - Request URL (correct endpoint?)
   - Request headers (authentication included?)
   - Response status (200 = success, 401 = auth error, 404 = not found)
   - Response data (correct structure?)

### Method 2: Test in Component

Create a test component to verify the connection:

```typescript
import { useEffect } from 'react';
import { bestEnergyApi } from '../services/api/bestEnergyApi';

function ApiTest() {
  useEffect(() => {
    async function testApi() {
      try {
        console.log('Testing API connection...');
        
        // Test 1: Get customers
        const customers = await bestEnergyApi.getCustomers();
        console.log('Customers:', customers);
        
        // Test 2: Get energy data (if you have a customer ID)
        if (customers.items && customers.items.length > 0) {
          const customerId = customers.items[0].id;
          const dateRange = getDateRange('month');
          const energyData = await bestEnergyApi.getCustomerEnergyConsumption(
            customerId,
            dateRange
          );
          console.log('Energy Data:', energyData);
        }
      } catch (error) {
        console.error('API Test Failed:', error);
      }
    }
    
    testApi();
  }, []);

  return <div>Check console for API test results</div>;
}
```

## Step 7: Handle API Response Structure

Your API might return data in a different format. Common scenarios:

### Scenario 1: Data is Nested

If your API returns:
```json
{
  "success": true,
  "data": {
    "items": [...],
    "total": 100
  }
}
```

Update the API function:
```typescript
export const getCustomerEnergyConsumption = async (
  customerId: string,
  params: DateRangeParams & PaginationParams
): Promise<PaginatedResponse<EnergyConsumption>> => {
  const response = await apiClient.get(`/customers/${customerId}/consumption`, {
    params,
  });
  return response.data.data; // Extract nested data
};
```

### Scenario 2: Different Field Names

If API returns `energy_consumption` instead of `consumption`:
```typescript
// Update the endpoint path
const response = await apiClient.get(`/customers/${customerId}/energy_consumption`, {
  params,
});
```

### Scenario 3: Query Parameters Format

If your API expects different parameter names:
```typescript
const response = await apiClient.get(`/customers/${customerId}/consumption`, {
  params: {
    start: params.startDate,  // API expects 'start' not 'startDate'
    end: params.endDate,       // API expects 'end' not 'endDate'
  },
});
```

## Step 8: Update Components to Use Real Data

The Dashboard and CustomerPortal components are already set up to use the hooks. Once your API is connected, they should automatically display data.

### Example: Dashboard Already Uses Hooks

```typescript
// src/pages/Dashboard.tsx already has:
const { data: customersData } = useCustomers();
const { data: energyData } = useGroupedEnergyData(customerId, dateRange);
```

The components will automatically:
- Show loading states while fetching
- Display data when available
- Handle errors gracefully

## Common Issues & Solutions

### Issue 1: CORS Error
**Problem:** Browser blocks requests due to CORS policy
**Solution:** 
- Check if your API supports CORS
- You may need to configure CORS on the API server
- For development, you might need a proxy (configure in `vite.config.ts`)

### Issue 2: 401 Unauthorized
**Problem:** Authentication failed
**Solution:**
- Verify your API key is correct in `.env`
- Check if the key format is correct (Bearer token vs API key)
- Ensure the API key hasn't expired

### Issue 3: 404 Not Found
**Problem:** Endpoint doesn't exist
**Solution:**
- Verify the endpoint path matches your API documentation
- Check if you need a version prefix (e.g., `/v1/`)
- Confirm the HTTP method (GET, POST, etc.)

### Issue 4: Data Structure Mismatch
**Problem:** TypeScript errors or data not displaying
**Solution:**
- Update TypeScript types to match API response
- Add data transformation functions if needed
- Check console for actual API response structure

## Quick Reference: Where to Access Data

| What You Need | Where to Find It |
|--------------|------------------|
| **API Configuration** | `src/services/api/apiClient.ts` |
| **API Functions** | `src/services/api/bestEnergyApi.ts` |
| **React Hooks** | `src/hooks/useEnergyData.ts`, `src/hooks/useCustomerData.ts` |
| **Type Definitions** | `src/types/energy.ts`, `src/types/api.ts` |
| **Use in Components** | Import hooks from `src/hooks/` |
| **Date Utilities** | `src/utils/dateUtils.ts` |

## Next Steps

Once you can access the data:

1. ✅ Verify data is loading correctly
2. ✅ Check that charts display the data
3. ✅ Test different date ranges
4. ✅ Verify statistics calculations
5. ✅ Test with multiple customers/sites
6. ✅ Add error handling and user feedback
7. ✅ Optimize data fetching (caching, pagination)

## Need Help?

- Check browser console for errors
- Review Network tab in DevTools
- Compare API response with TypeScript types
- Test API endpoints directly (Postman, curl, etc.)
- Review `Core API v1.pdf` for API specifics



