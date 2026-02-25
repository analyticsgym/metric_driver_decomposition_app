#!/bin/bash
set -euo pipefail

# Only run in remote Claude Code on the web sessions
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

# Install Python dependencies
pip install -r "$CLAUDE_PROJECT_DIR/requirements.txt" -q

# Start the Streamlit app on port 8501 if not already running
if ! pgrep -f "streamlit run app.py" > /dev/null 2>&1; then
  nohup streamlit run "$CLAUDE_PROJECT_DIR/app.py" \
    --server.port 8501 \
    --server.headless true \
    > /tmp/streamlit.log 2>&1 &
fi
