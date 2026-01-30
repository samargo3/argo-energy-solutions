# Quick Start: Accessing Energy Data - Step by Step

## 🚀 Quick Checklist

Follow these steps in order to access your energy data:

### ✅ Step 1: Create .env File
```bash
# In the root directory, create .env file
VITE_BEST_ENERGY_API_URL=https://api.best.energy
VITE_BEST_ENERGY_API_KEY=your_api_key_here
VITE_API_TIMEOUT=30000
```

### ✅ Step 2: Update API Endpoints
1. Open `src/services/api/bestEnergyApi.ts`
2. Review your `Core API v1.pdf` documentation
3. Update endpoint paths to match your actual API
4. Example: Change `/customers` to `/v1/customers` if needed

### ✅ Step 3: Test API Connection
- Use the test component below OR
- Navigate to `/dashboard` in your app
- Check browser console for errors

### ✅ Step 4: Adjust Data Types (If Needed)
1. Check the actual API response structure
2. Update types in `src/types/energy.ts` if fields differ
3. Update components to use correct field names

## 📋 Testing Your API Connection

### Option 1: Use the Dashboard Page

1. Start your dev server: `npm run dev`
2. Navigate to `http://localhost:5173/dashboard`
3. Check browser console (F12) for:
   - API requests in Network tab
   - Any errors in Console tab
   - Data loading states

### Option 2: Create a Test Component

Add this to test your API connection (see example below)

## 🔍 How to Access Data in Your Code

### Method 1: Using Pre-built Hooks (Easiest)

```typescript
import { useCustomers } from '../hooks/useCustomerData';
import { useCustomerEnergyData } from '../hooks/useEnergyData';

function MyComponent() {
  // Fetch customers
  const { data: customers, isLoading, error } = useCustomers();
  
  // Fetch energy data for a customer
  const { data: energyData } = useCustomerEnergyData('customer-id-123');
  
  // Use the data
  return (
    <div>
      {isLoading && <p>Loading...</p>}
      {error && <p>Error: {error.message}</p>}
      {customers && <p>Found {customers.items.length} customers</p>}
      {energyData && <p>Found {energyData.items.length} energy records</p>}
    </div>
  );
}
```

### Method 2: Direct API Call

```typescript
import { bestEnergyApi } from '../services/api/bestEnergyApi';

async function getData() {
  const customers = await bestEnergyApi.getCustomers();
  console.log('Customers:', customers);
}
```

## 🐛 Troubleshooting

| Error | Likely Cause | Solution |
|-------|-------------|----------|
| 401 Unauthorized | Wrong API key | Check `.env` file |
| 404 Not Found | Wrong endpoint | Update `bestEnergyApi.ts` |
| CORS Error | API not allowing requests | Configure CORS or use proxy |
| Data not showing | Wrong data structure | Update types in `src/types/` |

## 📝 Common API Endpoint Patterns

Based on common API designs, here are patterns you might need:

### Pattern 1: REST API
```
GET /customers
GET /customers/{id}
GET /customers/{id}/consumption
```

### Pattern 2: Versioned API
```
GET /v1/customers
GET /v1/customers/{id}/energy
```

### Pattern 3: Query Parameters
```
GET /energy?customer_id={id}&start_date={date}&end_date={date}
```

Update `bestEnergyApi.ts` accordingly!



