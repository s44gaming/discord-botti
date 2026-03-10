#!/bin/sh
# Käynnistää Discord-botin ja web-dashboardin (Linux / macOS)
# Käyttö: ./start.sh  tai  sh start.sh

cd "$(dirname "$0")"

PYTHON=""
if command -v python3 >/dev/null 2>&1; then
    PYTHON=python3
elif command -v python >/dev/null 2>&1; then
    PYTHON=python
fi

if [ -z "$PYTHON" ]; then
    echo "Virhe: Python ei löydy. Asenna Python 3.8+."
    exit 1
fi

exec $PYTHON run.py
