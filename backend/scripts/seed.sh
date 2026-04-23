#!/bin/bash
# OverCloud Database Seed Script Wrapper
# Führt das Python Seed-Script mit dem richtigen Virtual Environment aus

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"

# Prüfe ob Virtual Environment existiert
if [ ! -f "$BACKEND_DIR/.venv/bin/python" ]; then
    echo "❌ Fehler: Virtual Environment nicht gefunden"
    echo "   Führe zuerst 'poetry install' aus"
    exit 1
fi

# Führe Seed-Script aus
"$BACKEND_DIR/.venv/bin/python" "$BACKEND_DIR/scripts/seed_data.py" "$@"
