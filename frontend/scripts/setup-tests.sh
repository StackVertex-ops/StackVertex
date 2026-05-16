#!/bin/bash

# OverCloud Frontend Test Setup Script
# Installiert Vitest und ergänzt package.json Scripts

set -e

echo "🧪 OverCloud Frontend Test Setup"
echo "================================"
echo ""

# Check if npm is available
if ! command -v npm &> /dev/null; then
    echo "❌ npm nicht gefunden. Bitte Node.js installieren."
    exit 1
fi

# Check if we're in the frontend directory
if [ ! -f "package.json" ]; then
    echo "❌ package.json nicht gefunden. Bitte im frontend/ Verzeichnis ausführen."
    exit 1
fi

# Install Vitest dependencies
echo "📦 Installiere Vitest Dependencies..."
npm install -D vitest@latest jsdom@latest @vitest/ui@latest happy-dom@latest

echo ""
echo "✅ Vitest Dependencies installiert"
echo ""

# Check if scripts need to be added
echo "📝 Prüfe package.json Scripts..."

# Create backup of package.json
cp package.json package.json.backup
echo "   Backup erstellt: package.json.backup"

# Add test scripts if not present
if ! grep -q '"test": "vitest"' package.json; then
    echo "   Ergänze Test-Scripts in package.json..."

    # Use Node.js to safely modify package.json
    node -e "
    const fs = require('fs');
    const pkg = JSON.parse(fs.readFileSync('package.json', 'utf8'));

    // Update test scripts
    pkg.scripts = pkg.scripts || {};
    pkg.scripts.test = 'vitest';
    pkg.scripts['test:unit'] = 'vitest run';
    pkg.scripts['test:unit:watch'] = 'vitest';
    pkg.scripts['test:unit:ui'] = 'vitest --ui';
    pkg.scripts['test:unit:coverage'] = 'vitest run --coverage';
    pkg.scripts['test:all'] = 'npm run test:unit && npm run test:e2e';

    fs.writeFileSync('package.json', JSON.stringify(pkg, null, 2) + '\n');
    "

    echo "   ✅ Test-Scripts hinzugefügt"
else
    echo "   ℹ️  Test-Scripts bereits vorhanden"
fi

echo ""
echo "🎉 Setup abgeschlossen!"
echo ""
echo "Verfügbare Test-Commands:"
echo "  npm run test              # Vitest im Watch-Mode"
echo "  npm run test:unit         # Unit-Tests ausführen"
echo "  npm run test:unit:watch   # Unit-Tests im Watch-Mode"
echo "  npm run test:unit:ui      # Unit-Tests mit UI"
echo "  npm run test:unit:coverage # Coverage Report erstellen"
echo "  npm run test:e2e          # E2E-Tests ausführen"
echo "  npm run test:all          # Alle Tests ausführen"
echo ""
echo "📚 Dokumentation:"
echo "  tests/TEST_SETUP.md       # Setup & Konfiguration"
echo "  tests/TEST_FINDINGS.md    # Test-Ergebnisse & Empfehlungen"
echo ""
echo "Nächste Schritte:"
echo "  1. Tests ausführen: npm run test:unit"
echo "  2. Fehlende Implementierungen ergänzen (siehe TEST_FINDINGS.md)"
echo "  3. Coverage prüfen: npm run test:unit:coverage"
echo ""
