#!/bin/bash
# Start local development services

set -e

echo "Starting local development services..."

# Start API service in the background
echo "Starting API service..."
cd apps/api
python3 main.py &
API_PID=$!
cd ../..

# Start frontend development server
echo "Starting frontend development server..."
cd apps/frontend
npm start &
FRONTEND_PID=$!
cd ../..

# Wait for interrupt
echo "Services started. API PID: $API_PID, Frontend PID: $FRONTEND_PID"
echo "Press Ctrl+C to stop all services."

# Wait for either process to exit
wait -n

# If one process exits, kill the other
echo "One service has stopped. Stopping the other..."
kill $API_PID 2>/dev/null || true
kill $FRONTEND_PID 2>/dev/null || true

wait $API_PID 2>/dev/null || true
wait $FRONTEND_PID 2>/dev/null || true

echo "All services stopped."