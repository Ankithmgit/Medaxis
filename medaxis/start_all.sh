#!/bin/bash
# start_all.sh — Start all MedAxis microservices in background

set -e

export $(cat .env | grep -v '#' | xargs)

echo "🚀 Starting MedAxis Platform..."
echo ""

# Auth Service — Port 8001
echo "Starting Auth Service on :8001..."
cd auth-service
pip install -r requirements.txt -q
uvicorn main:app --host 0.0.0.0 --port 8001 --reload &
AUTH_PID=$!
cd ..

sleep 2

# Inventory Service — Port 8002
echo "Starting Inventory Service on :8002..."
cd inventory-service
pip install -r requirements.txt -q
uvicorn main:app --host 0.0.0.0 --port 8002 --reload &
INV_PID=$!
cd ..

sleep 2

# Billing Service — Port 8003
echo "Starting Billing Service on :8003..."
cd billing-service
pip install -r requirements.txt -q
uvicorn main:app --host 0.0.0.0 --port 8003 --reload &
BILL_PID=$!
cd ..

sleep 2

# AI Service — Port 8004
echo "Starting AI Service on :8004..."
cd ai-service
pip install -r requirements.txt -q
uvicorn main:app --host 0.0.0.0 --port 8004 --reload &
AI_PID=$!
cd ..

sleep 2

echo ""
echo "✅ All services running!"
echo ""
echo "  Auth Service      → http://localhost:8001/docs"
echo "  Inventory Service → http://localhost:8002/docs"
echo "  Billing Service   → http://localhost:8003/docs"
echo "  AI Service        → http://localhost:8004/docs"
echo ""
echo "PIDs: auth=$AUTH_PID inventory=$INV_PID billing=$BILL_PID ai=$AI_PID"
echo ""
echo "To stop all: kill $AUTH_PID $INV_PID $BILL_PID $AI_PID"

wait
