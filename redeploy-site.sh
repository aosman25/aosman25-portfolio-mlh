#!/bin/bash

# Kill old tmux session if exists
tmux kill-session -t portfolio-session 2>/dev/null

# Start new detached tmux session and run everything inside it
tmux new-session -d -s portfolio-session "
cd aosman25-portfolio-mlh && \
git fetch && git reset origin/main --hard && \
if [ ! -d python3-virtualvenv ]; then python -m venv python3-virtualvenv; fi && \
source ./python3-virtualvenv/bin/activate && \
pip install -r requirements.txt && \
flask run --host 0.0.0.0
"
