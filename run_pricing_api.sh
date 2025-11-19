#!/bin/bash
# Script to run Pricing Calculator API server

cd "$(dirname "$0")"
export PYTHONPATH="src:$PYTHONPATH"

echo "🚀 Starting Pricing Calculator API on http://localhost:8001"
echo "📊 Frontend available at: http://localhost:8001/frontend"
echo "📋 API docs available at: http://localhost:8001/docs"
echo ""

python3 -m uvicorn pricing_calculator.example_api_usage:app \
    --host 127.0.0.1 \
    --port 8001 \
    --reload

