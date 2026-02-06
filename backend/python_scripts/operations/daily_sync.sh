#!/bin/bash
# Daily Sync Script for Argo Energy Solutions
# Runs Python ingestion for the most recent day

# Navigate to project directory
cd /Users/sargo/cursor-repo/projects/argo-energy-solutions

# Log start time
echo "========================================" >> logs/daily_sync.log
echo "🕐 Daily sync started: $(date)" >> logs/daily_sync.log

# Activate virtual environment and run ingestion
source venv/bin/activate

# Ingest the last 2 days (to handle any gaps or late-arriving data)
python backend/python_scripts/ingest/ingest_to_postgres.py --site 23271 --days 2 >> logs/daily_sync.log 2>&1

# Check exit code
if [ $? -eq 0 ]; then
    echo "✅ Daily sync completed successfully: $(date)" >> logs/daily_sync.log
else
    echo "❌ Daily sync failed: $(date)" >> logs/daily_sync.log
fi

echo "" >> logs/daily_sync.log

# Deactivate virtual environment
deactivate
