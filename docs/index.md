# Argo Energy Solutions Documentation

Welcome to the Argo Energy Solutions documentation. This site covers setup, API integration, analytics, reporting, and operations for the energy monitoring platform.

## Quick Links

- **[Quick Start](QUICK_START.md)** - Common commands for daily operations
- **[Current Status](CURRENT_STATUS.md)** - Project status overview
- **[Quick Reference](QUICK_REFERENCE.md)** - Command cheat sheet

## Documentation Sections

| Section | Description |
|---------|-------------|
| [Getting Started](setup/CREATE_ENV_FILE.md) | Environment setup, database config, GitHub workflows |
| [API](api/API_ACCESS_GUIDE.md) | Best.Energy API access, endpoints, rate limits |
| [Guides](guides/QUERY_GUIDE.md) | Analytics, data export, Tableau, Salesforce, reports |
| [Architecture](architecture/PROJECT_ORGANIZATION.md) | Database schema, data foundation, governance |
| [Operations](CURRENT_STATUS.md) | Status, observability, troubleshooting |
| [Reference](PROJECT_CONTEXT.md) | Full project context and AI tool references |

## Project Overview

Argo Energy Solutions is a React + Python platform for connecting to the Best.Energy API, performing statistical analysis, creating data visualizations, and delivering energy insights to customers.

**Tech stack:** React 18, TypeScript, Vite, FastAPI, Python analytics, Neon PostgreSQL

**Key capabilities:**

- Energy dashboard with interactive charts
- Automated weekly analytics reports with anomaly detection
- Data export to Tableau and CSV
- Customer report generation
- Natural language database queries
