# Argo Energy Solutions

A React-based dashboard application for connecting to Best.Energy API, performing statistical analysis, creating data visualizations, and providing insights for both internal employees and customers.

## Features

- 📊 **Energy Dashboard** - View energy consumption data with interactive charts
- 👥 **Customer Management** - Browse and view customer information
- 📈 **Data Visualization** - Real-time energy consumption charts using Recharts
- 📊 **Statistical Analysis** - Calculate energy statistics and insights
- 🔄 **API Integration** - Connect to Best.Energy API for real-time data

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **React Router** - Navigation
- **React Query** - Data fetching and caching
- **Axios** - HTTP client
- **Recharts** - Data visualization
- **date-fns** - Date utilities

## Getting Started

### Prerequisites

- Node.js 18+ and npm

### Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   npm install
   ```

3. Create a `.env` file in the root directory:
   ```env
   VITE_BEST_ENERGY_API_URL=https://api.best.energy
   VITE_BEST_ENERGY_API_KEY=your_api_key_here
   VITE_API_TIMEOUT=30000
   ```

4. Start the development server:
   ```bash
   npm run dev
   ```

5. Open your browser to `http://localhost:5173`

## Project Structure

```
src/
├── components/       # Reusable components
│   ├── charts/      # Chart components
│   ├── common/      # Common UI components
│   └── layout/      # Layout components
├── hooks/           # Custom React hooks
├── pages/           # Page components
├── services/        # API and business logic
│   ├── api/         # API client and services
│   └── analytics/   # Statistical analysis
├── types/           # TypeScript type definitions
└── utils/           # Utility functions
```

## API Integration

The application is configured to connect to the Best.Energy API. Review the `Core API v1.pdf` documentation for API endpoint specifications.

### Current API Endpoints (Placeholders)

- `GET /customers` - Get all customers
- `GET /customers/:id` - Get customer by ID
- `GET /customers/:id/consumption` - Get customer energy consumption
- `GET /customers/:id/consumption/grouped` - Get grouped consumption data
- `GET /sites/:id` - Get site information
- `GET /sites/:id/consumption` - Get site energy consumption

**Note:** These endpoints are placeholders. Update them in `src/services/api/bestEnergyApi.ts` based on the actual Best.Energy API documentation.

## Features in Development

- ✅ Project structure and API service layer
- ✅ React Router setup
- ✅ React Query integration
- ✅ Basic dashboard with charts
- ✅ Customer management pages
- 🔄 Statistical analysis utilities
- 🔄 Report generation
- 🔄 Insight generation
- 🔄 Scheduled reporting

## Building for Production

```bash
npm run build
```

The built files will be in the `dist` directory.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_BEST_ENERGY_API_URL` | Best.Energy API base URL | `https://api.best.energy` |
| `VITE_BEST_ENERGY_API_KEY` | API authentication key | - |
| `VITE_API_TIMEOUT` | API request timeout (ms) | `30000` |

## Contributing

1. Review the `NEXT_STEPS.md` file for planned features
2. Follow TypeScript best practices
3. Ensure all components are typed
4. Test API integration with mock data if needed

## License

Copyright © 2024 Argo Energy Solutions. All rights reserved.

