#!/bin/bash

echo "==================================="
echo "Infrastructure Designer Test Suite"
echo "==================================="

# Check backend is running
echo ""
echo "1. Checking backend..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "   ✓ Backend is running"
else
    echo "   ✗ Backend is NOT running"
    echo "   Start with: cd backend && uvicorn app.main:app --reload"
    exit 1
fi

# Check frontend is running
echo ""
echo "2. Checking frontend..."
if curl -s http://localhost:5173 > /dev/null 2>&1; then
    echo "   ✓ Frontend is running (port 5173)"
elif curl -s http://localhost:5174 > /dev/null 2>&1; then
    echo "   ✓ Frontend is running (port 5174)"
else
    echo "   ✗ Frontend is NOT running"
    echo "   Start with: cd frontend && npm run dev"
    exit 1
fi

# Check Cytoscape.js is installed
echo ""
echo "3. Checking dependencies..."
if [ -d "node_modules/cytoscape" ]; then
    echo "   ✓ Cytoscape.js installed"
else
    echo "   ✗ Cytoscape.js NOT installed"
    echo "   Install with: npm install"
    exit 1
fi

# Check all files exist
echo ""
echo "4. Checking files..."
FILES=(
    "src/infrastructure-designer.html"
    "src/js/pages/infrastructure-designer.js"
    "src/js/components/InfrastructureCanvas.js"
    "src/js/components/ComponentPalette.js"
    "src/js/components/TabSystem.js"
    "src/js/state/ArchitectureState.js"
    "src/js/sync/SyncCoordinator.js"
    "src/js/demo/sample-architecture.js"
    "src/css/components/infrastructure-canvas.css"
)

ALL_FOUND=true
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✓ $file"
    else
        echo "   ✗ $file MISSING"
        ALL_FOUND=false
    fi
done

# Check CSS imports
echo ""
echo "5. Checking CSS imports in main.css..."
if grep -q "infrastructure-canvas.css" src/css/main.css; then
    echo "   ✓ infrastructure-canvas.css imported"
else
    echo "   ✗ infrastructure-canvas.css NOT imported"
    ALL_FOUND=false
fi

if [ "$ALL_FOUND" = false ]; then
    echo ""
    echo "==================================="
    echo "✗ Some files are missing!"
    echo "==================================="
    exit 1
fi

echo ""
echo "==================================="
echo "✓ All checks passed!"
echo ""
echo "Open in browser:"
echo "  - http://localhost:5173/infrastructure-designer.html"
echo "  - http://localhost:5173/infrastructure-designer.html?id=demo (Load demo)"
echo ""
echo "Test checklist:"
echo "  1. Drag VPC from palette onto canvas"
echo "  2. Click VPC node → Tab should open"
echo "  3. Change CIDR → IP info should update"
echo "  4. Delete component → Should remove from canvas"
echo "  5. Load demo architecture (add ?id=demo to URL)"
echo "  6. Export JSON (Cmd/Ctrl+S or Save button)"
echo "==================================="
