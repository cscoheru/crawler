#!/bin/bash
# Setup macOS launchd service for automated crawling

PROJECT_DIR="/Users/kjonekong/pyStcratch"
PLIST_FILE="$PROJECT_DIR/com.claudecrawler.scheduler.plist"
LAUNCH_AGENT_DIR="$HOME/Library/LaunchAgents"
LAUNCH_AGENT_PATH="$LAUNCH_AGENT_DIR/com.claudecrawler.scheduler.plist"

echo "Setting up automated crawler scheduler..."

# Create LaunchAgents directory if it doesn't exist
mkdir -p "$LAUNCH_AGENT_DIR"

# Copy plist file to LaunchAgents
cp "$PLIST_FILE" "$LAUNCH_AGENT_PATH"

# Make the script executable
chmod +x "$PROJECT_DIR/scripts/auto_crawl_and_sync.sh"

# Unload existing service if running
launchctl unload "$LAUNCH_AGENT_PATH" 2>/dev/null || true

# Load the service
launchctl load "$LAUNCH_AGENT_PATH"

# Start the service
launchctl start com.claudecrawler.scheduler

echo "✓ Scheduler installed and started"
echo ""
echo "Service details:"
echo "  - Run time: Daily at 16:00 (4:00 PM)"
echo "  - Log files: $PROJECT_DIR/logs/"
echo "  - Plist file: $LAUNCH_AGENT_PATH"
echo ""
echo "Commands:"
echo "  - Check status: launchctl list | grep claudecrawler"
echo "  - Stop service: launchctl stop com.claudecrawler.scheduler"
echo "  - Uninstall: launchctl unload $LAUNCH_AGENT_PATH"
echo ""
echo "To run immediately for testing:"
echo "  bash $PROJECT_DIR/scripts/auto_crawl_and_sync.sh"
