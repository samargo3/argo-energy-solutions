#!/bin/bash
# Cron Setup Helper for Argo Energy Solutions Daily Sync

echo "🔧 Setting up automated daily sync for Argo Energy Solutions"
echo ""

# Get the current directory
PROJECT_DIR="/Users/sargo/cursor-repo/projects/argo-energy-solutions"

# Create the cron job entry
CRON_ENTRY="0 6 * * * $PROJECT_DIR/backend/python_scripts/operations/daily_sync.sh"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "daily_sync.sh"; then
    echo "⚠️  Cron job already exists!"
    echo ""
    echo "Current cron jobs:"
    crontab -l | grep "daily_sync.sh"
    echo ""
    echo "To modify, run: crontab -e"
else
    echo "📅 This will add a daily sync job that runs at 6:00 AM every day."
    echo ""
    echo "Cron entry:"
    echo "   $CRON_ENTRY"
    echo ""
    read -p "Do you want to add this cron job? (y/n) " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Add the cron job
        (crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -
        
        if [ $? -eq 0 ]; then
            echo "✅ Cron job added successfully!"
            echo ""
            echo "To verify, run: crontab -l"
            echo "To view logs: tail -f $PROJECT_DIR/logs/daily_sync.log"
            echo "To test manually: $PROJECT_DIR/backend/python_scripts/operations/daily_sync.sh"
        else
            echo "❌ Failed to add cron job"
        fi
    else
        echo "❌ Cancelled. No cron job added."
    fi
fi

echo ""
echo "📖 Manual Setup Instructions:"
echo "   1. Run: crontab -e"
echo "   2. Add this line:"
echo "      $CRON_ENTRY"
echo "   3. Save and exit"
echo ""
echo "💡 Cron Time Options:"
echo "   0 6 * * *    → Every day at 6:00 AM"
echo "   0 */4 * * *  → Every 4 hours"
echo "   0 8,20 * * * → At 8:00 AM and 8:00 PM"
