#!/bin/bash
# Daily Sync Script for Argo Energy Solutions
# Iterates over all active sites from the sites table and runs ingestion + validation.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKG_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_ROOT="$(cd "$PKG_ROOT/../.." && pwd)"
LOG_DIR="$PROJECT_ROOT/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/daily_sync.log"

echo "========================================" >> "$LOG_FILE"
echo "Daily sync started: $(date)" >> "$LOG_FILE"

# Activate virtual environment if available
if [ -f "$PROJECT_ROOT/venv/bin/activate" ]; then
    source "$PROJECT_ROOT/venv/bin/activate"
fi

# Discover active sites from the database
SITES=$(python "$PKG_ROOT/operations/list_active_sites.py" 2>>"$LOG_FILE")

if [ -z "$SITES" ]; then
    echo "No active sites found — nothing to sync" >> "$LOG_FILE"
    exit 0
fi

FAILED=0

for SITE_ID in $SITES; do
    echo "--- Syncing site $SITE_ID ---" >> "$LOG_FILE"

    python "$PKG_ROOT/ingest/ingest_to_postgres.py" \
        --site "$SITE_ID" --days 2 >> "$LOG_FILE" 2>&1 \
    && echo "  Site $SITE_ID ingestion OK" >> "$LOG_FILE" \
    || { echo "  Site $SITE_ID ingestion FAILED" >> "$LOG_FILE"; FAILED=1; }
done

# Run data validation (covers all sites)
echo "--- Running data validation ---" >> "$LOG_FILE"
python "$PKG_ROOT/govern/validate_data.py" >> "$LOG_FILE" 2>&1 \
    && echo "  Validation OK" >> "$LOG_FILE" \
    || { echo "  Validation FAILED" >> "$LOG_FILE"; FAILED=1; }

if [ $FAILED -eq 0 ]; then
    echo "Daily sync completed successfully: $(date)" >> "$LOG_FILE"
else
    echo "Daily sync finished with errors: $(date)" >> "$LOG_FILE"
    exit 1
fi

echo "" >> "$LOG_FILE"
