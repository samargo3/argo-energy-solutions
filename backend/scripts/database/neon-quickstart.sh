#!/bin/bash

# Neon PostgreSQL Quick Start for Argo Energy Solutions
# This script walks you through the setup process

set -e  # Exit on error

echo "🚀 Neon PostgreSQL Quick Start for Argo Energy Solutions"
echo "========================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Check if pg is installed
echo -e "${BLUE}Step 1: Installing dependencies...${NC}"
if npm list pg > /dev/null 2>&1; then
  echo "✅ pg package already installed"
else
  echo "📦 Installing pg (PostgreSQL client)..."
  npm install pg
  echo "✅ pg installed"
fi
echo ""

# Step 2: Check .env file
echo -e "${BLUE}Step 2: Checking .env configuration...${NC}"
if [ ! -f .env ]; then
  echo -e "${RED}❌ .env file not found${NC}"
  echo "Please create a .env file in the project root"
  exit 1
fi

if grep -q "DATABASE_URL" .env; then
  echo "✅ DATABASE_URL found in .env"
else
  echo -e "${YELLOW}⚠️  DATABASE_URL not found in .env${NC}"
  echo ""
  echo "You need to add your Neon connection string to .env:"
  echo ""
  echo "1. Go to https://neon.tech"
  echo "2. Sign in (or create account with GitHub)"
  echo "3. Create a project: 'argo-energy-production'"
  echo "4. Copy the connection string"
  echo "5. Add to .env:"
  echo ""
  echo "   DATABASE_URL=postgresql://user:pass@host/db"
  echo ""
  read -p "Press Enter when you've added DATABASE_URL to .env..."
  
  # Check again
  if ! grep -q "DATABASE_URL" .env; then
    echo -e "${RED}❌ DATABASE_URL still not found in .env${NC}"
    exit 1
  fi
  echo "✅ DATABASE_URL added"
fi
echo ""

# Step 3: Test connection
echo -e "${BLUE}Step 3: Testing Neon connection...${NC}"
if npm run db:test-neon; then
  echo "✅ Connection successful"
else
  echo -e "${RED}❌ Connection failed${NC}"
  echo "Please check your DATABASE_URL in .env"
  exit 1
fi
echo ""

# Step 4: Setup schema
echo -e "${BLUE}Step 4: Setting up database schema...${NC}"
read -p "Create tables in Neon? (yes/no): " create_tables
if [ "$create_tables" = "yes" ]; then
  npm run db:setup
  echo "✅ Schema created"
else
  echo "⏭️  Skipped schema creation"
fi
echo ""

# Step 5: Choose data source
echo -e "${BLUE}Step 5: Load data...${NC}"
echo "Choose how to populate your database:"
echo ""
echo "A) Migrate existing SQLite data (if you have it)"
echo "B) Pull fresh data from Eniscope API"
echo "C) Skip for now"
echo ""
read -p "Choose option (A/B/C): " data_option

case $data_option in
  [Aa])
    echo ""
    echo "📦 Migrating data from SQLite to PostgreSQL..."
    if [ -f "backend/data/eniscope.db" ]; then
      npm run db:migrate:sqlite-to-postgres
      echo "✅ Migration complete"
    else
      echo -e "${YELLOW}⚠️  SQLite database not found at backend/data/eniscope.db${NC}"
      echo "Run option B instead to pull fresh data"
    fi
    ;;
  [Bb])
    echo ""
    echo "🌐 Pulling data from Eniscope API..."
    echo ""
    read -p "Enter site ID (e.g., 23271 for Wilson Center): " site_id
    read -p "Enter number of days to pull (e.g., 90): " days
    
    echo ""
    echo "Pulling last $days days for site $site_id..."
    npm run ingest:full -- --db postgres --site $site_id --days $days
    echo "✅ Data ingestion complete"
    ;;
  [Cc])
    echo "⏭️  Skipped data loading"
    ;;
  *)
    echo "Invalid option, skipping data loading"
    ;;
esac
echo ""

# Step 6: Verify
echo -e "${BLUE}Step 6: Verifying setup...${NC}"
npm run db:test-neon
echo ""

# Step 7: Next steps
echo -e "${GREEN}✅ Neon setup complete!${NC}"
echo ""
echo "📋 Next steps:"
echo ""
echo "1. Generate a report:"
echo "   npm run report:weekly -- --site 23271 --db postgres"
echo ""
echo "2. Set up daily sync (add to crontab):"
echo "   0 6 * * * cd $(pwd) && npm run ingest:incremental -- --db postgres"
echo ""
echo "3. Enable TimescaleDB (optional, for better performance):"
echo "   - Go to Neon console: https://console.neon.tech"
echo "   - Open SQL Editor"
echo "   - Run: CREATE EXTENSION IF NOT EXISTS timescaledb;"
echo ""
echo "4. Read the full guide:"
echo "   cat docs/setup/NEON_SETUP_GUIDE.md"
echo ""
echo "🎉 You're ready to go!"
