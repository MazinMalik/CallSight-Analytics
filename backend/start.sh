#!/bin/bash
set -e

echo "Starting Telecaller Audio Automation System Backend..."

# Create storage directories
mkdir -p data uploads exports

# Run migrations/table setup and start Uvicorn
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
