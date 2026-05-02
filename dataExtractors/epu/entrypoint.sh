#!/bin/bash
set -e

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting EPU extractor container"

# ======================
# ENV + PATHS
# ======================

DATA_PATH=${SHARED_DATA_PATH:-/app/data/epu}
LOG_PATH="/app/data/epu/logs"

mkdir -p "$DATA_PATH"
mkdir -p "$LOG_PATH"

echo "Using data path: $DATA_PATH"
echo "Logs will be written to: $LOG_PATH"

# ======================
# CRON SETUP
# ======================

CRON_LOG="$LOG_PATH/epu_cron.log"

echo "Setting up cron job..."

(crontab -l 2>/dev/null; echo "0 12 5 * * cd /app && PYTHONPATH=/app/src python -u src/epu_bot_workflow.py >> $CRON_LOG 2>&1") | crontab -

# ======================
# INITIAL RUN
# ======================

echo "[$(date '+%Y-%m-%d %H:%M:%S')] === Initial EPU workflow run ==="

cd /app
PYTHONPATH=/app/src python -u src/epu_bot_workflow.py

echo "[$(date '+%Y-%m-%d %H:%M:%S')] === Initial run completed ==="

# ======================
# CRON START
# ======================

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Cron active — next run: day 5 at 12:00"
echo "Cron log: $CRON_LOG"

# Forward cron logs to docker logs (VERY useful)
touch $CRON_LOG
tail -f $CRON_LOG &

exec cron -f