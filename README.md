# Argo Energy Solutions

A React-based dashboard application for connecting to Best.Energy API, performing statistical analysis, creating data visualizations, and providing insights for both internal employees and customers.

## Features

- 📊 **Energy Dashboard** - View energy consumption data with interactive charts
- 👥 **Customer Management** - Browse and view customer information
- 📈 **Data Visualization** - Real-time energy consumption charts using Recharts
- 📊 **Statistical Analysis** - Calculate energy statistics and insights
- 🔄 **API Integration** - Connect to Best.Energy API for real-time data
- 📤 **Data Export** - Export Wilson Center raw data to CSV for Tableau/AI analysis
- ⚡ **Weekly Reports** - Automated weekly energy analytics with anomaly detection and optimization recommendations

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
argo-energy-solutions/
├── docs/                          # 📚 Documentation
│   ├── setup/                     # Setup & configuration guides
│   ├── api/                       # API documentation
│   ├── guides/                    # Feature-specific guides
│   │   ├── data/                  # Data collection & access
│   │   ├── reports/               # Report generation
│   │   └── integrations/          # Third-party integrations
│   ├── troubleshooting/           # Fixes & solutions
│   └── reference/                 # Reference materials (PDFs)
├── backend/                       # 🖥️ Backend services
│   ├── server/                    # Node.js API server
│   ├── scripts/                   # Data & analysis scripts
│   │   ├── analysis/              # Energy data analysis
│   │   ├── data-collection/       # Data fetching & ingestion
│   │   ├── database/              # Database management
│   │   ├── diagnostics/           # Diagnostic tools
│   │   ├── reports/               # Weekly analytics reports (NEW!)
│   │   └── utilities/             # Utility scripts
│   └── python_reports/            # Python analytics
│       ├── scripts/               # Python report scripts
│       ├── reports/               # Generated reports & charts
│       └── data/                  # CSV data files
├── src/                           # ⚛️ Frontend (React/TypeScript)
│   ├── components/                # Reusable components
│   │   ├── charts/                # Chart components
│   │   ├── common/                # Common UI components
│   │   └── layout/                # Layout components
│   ├── hooks/                     # Custom React hooks
│   ├── pages/                     # Page components
│   ├── services/                  # API and business logic
│   │   ├── api/                   # API client and services
│   │   └── analytics/             # Statistical analysis
│   ├── types/                     # TypeScript type definitions
│   └── utils/                     # Utility functions
├── public/                        # 📁 Public assets
├── .env.example                   # Environment variables template
├── package.json                   # Dependencies & scripts
└── README.md                      # This file
```

## Documentation

Comprehensive documentation is available in the `docs/` directory:

- **Setup Guides**: `docs/setup/` - Installation and configuration
- **API Documentation**: `docs/api/` - API endpoints and configuration
- **Data Guides**: `docs/guides/data/` - Data collection and access
- **Report Guides**: `docs/guides/reports/` - Report generation
- **Integration Guides**: `docs/guides/integrations/` - Salesforce, Tableau, etc.
- **Troubleshooting**: `docs/troubleshooting/` - Common issues and fixes

Quick reference documents:
- `docs/CURRENT_STATUS.md` - Current project status
- `docs/NEXT_STEPS.md` - Planned features and roadmap
- `docs/QUICK_REFERENCE.md` - Quick command reference

### Weekly Analytics Reports

Generate automated weekly energy analytics reports with:
- **Sensor health monitoring** - Detect missing data, stale meters, and flatlined sensors
- **After-hours waste analysis** - Identify equipment running unnecessarily outside business hours
- **Anomaly detection** - Statistical outlier identification using IQR method
- **Demand spike detection** - Peak power events and short-cycling identification
- **Quick wins** - Actionable recommendations ranked by impact and cost savings

**Quick Start:**
```bash
# Generate report for last week
npm run report:weekly -- --site YOUR_SITE_ID

# See full documentation
cat backend/scripts/reports/QUICKSTART.md
cat backend/scripts/reports/README.md
```

For complete documentation, see `backend/scripts/reports/README.md`

## API Integration

The application is configured to connect to the Best.Energy API. Review `docs/reference/Core_API_v1.pdf` for complete API specifications.

### Available Scripts

```bash
# Data Collection & Analysis
npm run analyze:energy      # Analyze energy data
npm run explore:channels    # Explore available channels
npm run analyze:wilson      # Wilson Center specific analysis
npm run diagnose:data       # Diagnostic data access tests
npm run export:csv          # Export data to CSV
npm run export:wilson:raw   # Export Wilson Center raw monthly data to CSV

# Data Ingestion
npm run ingest:data         # Ingest Eniscope data
npm run ingest:full         # Full data ingestion
npm run ingest:incremental  # Incremental ingestion

# Database & Health
npm run db:check            # Check database status
npm run unit:health         # Unit health report
npm run check:daily         # Daily data check

# Weekly Analytics Reports (NEW!)
npm run report:weekly       # Generate weekly exceptions & opportunities brief
npm run report:test         # Run analytics unit tests

# Development
npm run dev                 # Start frontend dev server
npm run api:server          # Start backend API server
npm run dev:all             # Start both frontend and backend
npm start                   # Alias for dev:all
```

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

1. Review `docs/NEXT_STEPS.md` for planned features
2. Follow TypeScript best practices
3. Ensure all components are typed
4. Test API integration with mock data if needed
5. Backend scripts go in `backend/scripts/` (categorized by function)
6. Documentation goes in `docs/` (organized by topic)

## License

Copyright © 2024 Argo Energy Solutions. All rights reserved.

