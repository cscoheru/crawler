#!/bin/bash
# Automated crawling and Dify sync script

# Set project directory
PROJECT_DIR="/Users/kjonekong/pyStcratch"
cd "$PROJECT_DIR" || exit 1

# Activate virtual environment if exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Log file
LOG_FILE="$PROJECT_DIR/logs/auto_crawl.log"
mkdir -p "$(dirname "$LOG_FILE")"

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "Starting automated crawling and sync"

# Run crawling for all sources
log "Running crawlers..."
python3 main.py crawl --source all --max-pages 2 2>&1 | tee -a "$LOG_FILE"

# Run classification
log "Running classification..."
python3 main.py classify 2>&1 | tee -a "$LOG_FILE"

# Export to TXT for Dify
EXPORT_DIR="$PROJECT_DIR/data/dify_export"
mkdir -p "$EXPORT_DIR"

log "Exporting articles to TXT..."
python3 main.py export --output "$EXPORT_DIR" --format txt 2>&1 | tee -a "$LOG_FILE"

# Sync to Dify if API key is configured
if [ -n "$DIFY_API_KEY" ]; then
    log "Syncing to Dify knowledge base..."
    python3 -c "
from utils.dify_integration import DifyKnowledgeBase
from storage.database import DatabaseManager
import os

dify = DifyKnowledgeBase()
db = DatabaseManager()
syncer = DifyBatchSyncer(dify_client=dify)

# Export and sync
syncer.export_and_sync(db, output_dir='$EXPORT_DIR', min_quality=0.6)
" 2>&1 | tee -a "$LOG_FILE"
else
    log "DIFY_API_KEY not configured, skipping sync"
fi

# Show statistics
log "Database statistics:"
python3 main.py stats 2>&1 | tee -a "$LOG_FILE"

log "Automated crawling and sync completed"
