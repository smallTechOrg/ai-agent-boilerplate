#!/bin/bash
# update_app.sh
# Cleans old logs, runs on VM startup, pulls latest code, and triggers deploy.sh

# Clean or rotate old logs
LOG_FILE="/var/log/update_app.log"

# Clean old log file if exists
if [ -f "$LOG_FILE" ]; then
  echo "Removing old log file..."
  rm -f "$LOG_FILE"
fi



# Start logging
echo "==== $(date): Starting update_app.sh ====" | tee -a "$LOG_FILE"
exec >> "$LOG_FILE" 2>&1
set -ex

sudo su
cd /opt/ai-agent-boilerplate

# Read branch name from metadata
BRANCH=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/attributes/BRANCH_NAME" -H "Metadata-Flavor: Google")
echo "Pulling latest code from branch: $BRANCH"

echo "Pulling latest code..."
git -c safe.directory=/opt/ai-agent-boilerplate fetch --all
git -c safe.directory=/opt/ai-agent-boilerplate reset --hard origin/$BRANCH
git -c safe.directory=/opt/ai-agent-boilerplate clean -fd

echo "Running deploy.sh..." | tee -a "$LOG_FILE"
chmod +x scripts/deploy.sh
./scripts/deploy.sh deploy >> "$LOG_FILE" 2>&1
