#!/usr/bin/env bash
# Avaitor Runner Script
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    .venv/bin/pip install -r requirements.txt
fi

echo "Starting Avaitor Pilot Trainee Monitor..."
exec .venv/bin/python bot.py "$@"
