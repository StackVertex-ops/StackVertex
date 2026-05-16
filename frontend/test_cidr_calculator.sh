#!/bin/bash

# Test Script für CIDR Calculator Frontend
# Startet Backend und Frontend gleichzeitig

set -e

# Farben für Output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=====================================${NC}"
echo -e "${BLUE}VPC/CIDR Calculator - Test Setup${NC}"
echo -e "${BLUE}=====================================${NC}"
echo ""

# 1. Backend starten
echo -e "${YELLOW}[1/3] Starte Backend (FastAPI)...${NC}"
cd ../backend
poetry run uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!
echo -e "${GREEN}✓ Backend läuft (PID: $BACKEND_PID)${NC}"
echo ""

# Warte kurz auf Backend
sleep 3

# 2. Frontend Dev Server starten
echo -e "${YELLOW}[2/3] Starte Frontend (Vite)...${NC}"
cd ../frontend
npm run dev &
FRONTEND_PID=$!
echo -e "${GREEN}✓ Frontend läuft (PID: $FRONTEND_PID)${NC}"
echo ""

# Warte auf Vite Start
sleep 2

# 3. Browser öffnen
echo -e "${YELLOW}[3/3] Öffne Browser...${NC}"
sleep 1
open "http://localhost:5173/cidr-calculator.html"
echo -e "${GREEN}✓ Browser geöffnet${NC}"
echo ""

echo -e "${BLUE}=====================================${NC}"
echo -e "${GREEN}CIDR Calculator bereit!${NC}"
echo -e "${BLUE}=====================================${NC}"
echo ""
echo "Backend API:  http://localhost:8000/api/docs"
echo "Frontend:     http://localhost:5173/cidr-calculator.html"
echo ""
echo -e "${YELLOW}Drücke Ctrl+C zum Beenden${NC}"

# Trap für sauberes Cleanup
trap cleanup INT

cleanup() {
    echo ""
    echo -e "${YELLOW}Beende Prozesse...${NC}"
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    echo -e "${GREEN}✓ Cleanup abgeschlossen${NC}"
    exit 0
}

# Warte auf Beenden
wait
