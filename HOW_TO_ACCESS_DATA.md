# How to Access Energy Data - Step by Step Guide

## 🎯 Quick Answer: 5 Steps to Access Your Data

### Step 1: Configure Your API Credentials

Create a `.env` file in the root directory:

```env
VITE_BEST_ENERGY_API_URL=https://api.best.energy
VITE_BEST_ENERGY_API_KEY=your_actual_api_key_here
VITE_API_TIMEOUT=30000
```

**Important:** Replace `your_actual_api_key_here` with your real API key!

### Step 2: Update API Endpoints (If Needed)

1. Open `src/services/api/bestEnergyApi.ts`
2. Check your `Core API v1.pdf` for actual endpoints
3. Update the endpoint paths to match your API

**Example:** If your API uses `/v1/customers` instead of `/customers`, change:
```typescript
// Change this:
const response = await apiClient.get('/customers', { params });

// To this:
const response = await apiClient.get('/v1/customers', { params });
```

### Step 3: Test Your Connection

**Option A: Use the Test Page (Easiest)**
1. Start your dev server: `npm run dev`
2. Navigate to: `http://localhost:5173/api-test`
3. Click "Test Customers API"
4. Check the results and any errors

**Option B: Use the Dashboard**
1. Navigate to: `http://localhost:5173/dashboard`
2. Open browser DevTools (F12)
3. Check Console and Network tabs for API calls

### Step 4: Access Data in Your Components

Use the pre-built hooks in any component:

```typescript
import { useCustomers } from '../hooks/useCustomerData';
import { useCustomerEnergyData } from '../hooks/useEnergyData';

function MyComponent() {
  // Get all customers
  const { data: customers, isLoading, error } = useCustomers();
  
  // Get energy data for a customer
  const { data: energyData } = useCustomerEnergyData('customer-id-123');
  
  // Use the data
  return (
    <div>
      {customers && <p>Found {customers.items.length} customers</p>}
      {energyData && <p>Found {energyData.items.length} energy records</p>}
    </div>
  );
}
```

### Step 5: Adjust Data Types (If Needed)

If your API returns different field names, update `src/types/energy.ts`:

```typescript
// If API returns 'kwh' instead of 'value':
export interface EnergyConsumption {
  // ... other fields
  kwh: number;  // Changed from 'value'
}
```

---

## 📋 Detailed Steps

### Step 1: Environment Setup

1. **Create `.env` file** in the project root
2. **Add your API credentials:**
   ```env
   VITE_BEST_ENERGY_API_URL=https://api.best.energy
   VITE_BEST_ENERGY_API_KEY=your_api_key
   VITE_API_TIMEOUT=30000
   ```
3. **Restart your dev server** after creating/updating `.env`

### Step 2: Review API Documentation

1. Open `Core API v1.pdf`
2. Find the endpoints for:
   - Getting customers
   - Getting energy consumption data
   - Authentication method
3. Note the request/response structure

### Step 3: Update API Service

Edit `src/services/api/bestEnergyApi.ts`:

```typescript
// Example: Update endpoint path
export const getCustomers = async () => {
  const response = await apiClient.get('/v1/customers'); // Updated path
  return response.data;
};

// Example: Update authentication if needed
// In apiClient.ts, you might need to change:
headers: {
  'X-API-Key': API_KEY,  // Instead of Authorization Bearer
}
```

### Step 4: Test Connection

**Method 1: API Test Page**
- Navigate to `/api-test`
- Click test buttons
- Review results

**Method 2: Browser DevTools**
1. Open DevTools (F12)
2. Go to Network tab
3. Navigate to Dashboard or Customers page
4. Look for API requests
5. Check status codes (200 = success, 401 = auth error, 404 = not found)

### Step 5: Use Data in Components

The Dashboard and CustomerPortal pages already use the hooks. Once your API is connected, data will automatically appear!

---

## 🔍 Available Data Access Methods

### 1. React Hooks (Recommended)

```typescript
// Customers
import { useCustomers, useCustomer } from '../hooks/useCustomerData';
const { data: customers } = useCustomers();
const { data: customer } = useCustomer('customer-id');

// Energy Data
import { 
  useCustomerEnergyData, 
  useGroupedEnergyData 
} from '../hooks/useEnergyData';
const { data: energyData } = useCustomerEnergyData('customer-id');
const { data: groupedData } = useGroupedEnergyData('customer-id');
```

### 2. Direct API Calls

```typescript
import { bestEnergyApi } from '../services/api/bestEnergyApi';

const customers = await bestEnergyApi.getCustomers();
const energyData = await bestEnergyApi.getCustomerEnergyConsumption('customer-id');
```

---

## 🐛 Troubleshooting

### Error: 401 Unauthorized
- ✅ Check `.env` file has correct API key
- ✅ Verify API key format (Bearer token vs API key)
- ✅ Ensure API key hasn't expired

### Error: 404 Not Found
- ✅ Verify endpoint paths match your API
- ✅ Check if you need version prefix (`/v1/`)
- ✅ Review `Core API v1.pdf` for correct endpoints

### Error: CORS
- ✅ Check if API supports CORS
- ✅ Configure proxy in `vite.config.ts` if needed
- ✅ Contact API provider about CORS settings

### Data Not Showing
- ✅ Check browser console for errors
- ✅ Verify data structure matches types
- ✅ Update TypeScript types if needed
- ✅ Check Network tab for actual API response

---

## 📚 Files to Review

| File | Purpose |
|------|---------|
| `.env` | API configuration |
| `src/services/api/apiClient.ts` | Axios client setup |
| `src/services/api/bestEnergyApi.ts` | API endpoint functions |
| `src/hooks/useEnergyData.ts` | React hooks for energy data |
| `src/hooks/useCustomerData.ts` | React hooks for customer data |
| `src/types/energy.ts` | TypeScript types |
| `src/pages/ApiTest.tsx` | Test page for API connection |

---

## ✅ Checklist

- [ ] Created `.env` file with API credentials
- [ ] Updated API endpoints in `bestEnergyApi.ts`
- [ ] Tested API connection using `/api-test` page
- [ ] Verified data structure matches TypeScript types
- [ ] Updated types if API structure differs
- [ ] Tested data display in Dashboard
- [ ] Checked browser console for errors
- [ ] Reviewed Network tab for API requests

---

## 🚀 Quick Start

1. **Create `.env`** with your API key
2. **Update endpoints** in `bestEnergyApi.ts` (if needed)
3. **Visit `/api-test`** to test connection
4. **Navigate to `/dashboard`** to see data

That's it! Your data should now be accessible throughout the application.

---

## Need More Help?

- 📖 See `API_ACCESS_GUIDE.md` for detailed documentation
- 🧪 Use `/api-test` page to test your connection
- 🔍 Check browser DevTools for detailed error messages
- 📄 Review `Core API v1.pdf` for API specifics



