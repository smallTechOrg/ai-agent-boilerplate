#!/bin/bash
set -euo pipefail

# Re-run as root in a non-interactive way if needed.
if [ "${EUID:-$(id -u)}" -ne 0 ]; then
	exec sudo -n "$0" "$@"
fi

echo "==== Starting deploy.sh ===="

cd /opt/ai-agent-boilerplate

echo "Activating virtualenv..."
source venv/bin/activate
 
cd code

echo "Cleaning old .env and Flask logs..."
rm -f .env
rm -f flask.log

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Generating .env file using Python script..."
python3 get_env.py

echo "Restarting service..."

echo "Stopping only ai-agent service..."
pkill -f "/opt/ai-agent-boilerplate"

cd /opt/ai-agent-boilerplate/code
export FLASK_APP=app.py
nohup flask run --host=0.0.0.0 --port=5000 > flask.log 2>&1 &


echo "✅ Deployment complete!"
