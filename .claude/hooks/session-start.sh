#!/bin/bash
set -euo pipefail

# Only run in remote Claude Code environments
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

echo "=== Session Start Hook ===" >&2

# Install Python dependencies
echo "Installing dependencies..." >&2
pip install -q -r "$CLAUDE_PROJECT_DIR/requirements.txt"

# Kill any existing Streamlit process
pkill -f "streamlit run app.py" 2>/dev/null || true
sleep 1

# Start Streamlit in the background
echo "Starting Streamlit app..." >&2
cd "$CLAUDE_PROJECT_DIR"
nohup streamlit run app.py \
  --server.port 8501 \
  --server.address 0.0.0.0 \
  > /tmp/streamlit.log 2>&1 &

# Wait for startup and print URL
sleep 3
echo "Streamlit app started. Access URL:" >&2
grep "External URL" /tmp/streamlit.log >&2 || echo "  http://localhost:8501" >&2
