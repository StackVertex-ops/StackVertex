# Live Cost Calculation - Quick Start

**5-Minuten Setup Guide**

## Backend Setup

### 1. Abhängigkeiten installiert?

Die neuen Module verwenden nur Standard-Dependencies die bereits vorhanden sind:

- `fastapi`
- `pydantic`
- `decimal` (Python Standard Library)

Keine zusätzlichen `pip install` erforderlich!

### 2. Backend starten

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

### 3. API testen

```bash
cd backend
./test_live_cost_api.sh
```

Erwartete Ausgabe:

```json
{
  "total": 86.65,
  "currency": "USD",
  "period": "monthly",
  "items": [...]
}
```

✅ Wenn JSON zurückkommt: **Backend funktioniert!**

## Frontend Setup

### 1. Dev Server starten

```bash
cd frontend
npm run dev
```

### 2. Test-Seite öffnen

```
http://localhost:5173/src/test-live-cost.html
```

### 3. Interaktiv testen

1. Blueprint auswählen: "Static Website"
2. Storage ändern: 100 GB
3. Traffic ändern: 2000 GB
4. **Rechts sollte Cost Panel live updaten!**

✅ Wenn Kosten sich ändern: **Frontend funktioniert!**

## Integration in eigene Formulare

### Beispiel: Minimales Blueprint-Formular

```html
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="/src/css/main.css">
</head>
<body>
    <div class="grid grid-cols-2 gap-4">
        <!-- Form -->
        <div>
            <form id="myForm">
                <input type="number" name="storage_gb" value="50">
                <input type="number" name="traffic_gb" value="1000">
            </form>
        </div>

        <!-- Cost Panel -->
        <div id="liveCostPanel"></div>
    </div>

    <script type="module">
        import { LiveCostPanel } from './js/components/LiveCostPanel.js';

        const costPanel = new LiveCostPanel('static-website');
        costPanel.render();

        // Update on form change
        document.getElementById('myForm').addEventListener('input', (e) => {
            const formData = new FormData(e.target.form);
            const data = Object.fromEntries(formData);
            
            // Convert to numbers
            data.storage_gb = parseFloat(data.storage_gb);
            data.traffic_gb = parseFloat(data.traffic_gb);
            
            costPanel.updateCost(data);
        });
    </script>
</body>
</html>
```

## Troubleshooting

### Problem: "Failed to fetch"

**Ursache:** Backend nicht erreichbar

**Lösung:**

```bash
# Backend läuft?
curl http://localhost:8000/health

# CORS aktiviert?
# In app/main.py sollte sein:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Problem: Cost Panel bleibt leer

**Ursache:** Container nicht vorhanden

**Lösung:**

```html
<!-- HTML muss enthalten: -->
<div id="liveCostPanel"></div>
```

### Problem: Kosten = $0.00

**Ursache:** Blueprint ID unbekannt

**Lösung:**

Unterstützte Blueprint IDs:

- `static-website`
- `three-tier-web`
- `serverless-api`

Groß-/Kleinschreibung beachten!

## Nächste Schritte

1. **Dokumentation lesen:** `docs/live-cost-calculation.md`
2. **Tests ausführen:** `pytest tests/test_cost_calculator.py`
3. **Eigene Blueprints hinzufügen:** Siehe Dokumentation

---

**Fertig!** 🎉 Du hast jetzt ein funktionierendes Real-Time Cost Calculation System.
