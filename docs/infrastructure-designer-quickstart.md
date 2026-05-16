# Infrastructure Designer - Quick Start

## Überblick

Der Infrastructure Designer ist ein visuelles Tool zum Entwerfen von AWS-Infrastruktur mit einer intuitiven Drag & Drop-Oberfläche.

**Features:**
- 🎨 Drag & Drop Canvas mit AWS-Komponenten (Cytoscape.js)
- 📋 Tab-basierte Konfiguration (Network, Security, Data, Computing)
- 🔢 Inline IP Calculator (keine separate Seite!)
- 🔄 Bidirektionale Synchronisation (Canvas ↔ Tabs ↔ JSON)
- 🏗️ Terraform Code-Generierung
- 💾 Auto-Save (localStorage)
- 📸 Export als PNG-Bild

---

## Installation

### 1. Dependencies installieren

```bash
cd frontend
npm install
```

**Hauptabhängigkeiten:**
- Vite (Build Tool)
- Cytoscape.js (Graph Visualisierung)
- Tailwind CSS (Styling)

### 2. Services starten

**Backend (FastAPI):**
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

**Frontend (Vite Dev Server):**
```bash
cd frontend
npm run dev
```

### 3. Designer öffnen

Öffne im Browser:
**http://localhost:5174/infrastructure-designer.html**

---

## Verwendung

### Schritt 1: Komponenten hinzufügen

#### Via Drag & Drop (empfohlen)
1. Wähle Komponente aus Palette (links)
2. Ziehe auf Canvas
3. Komponente erscheint + Tab öffnet sich automatisch

#### Via Tab
1. Wähle Tab (Network, Security, Data, Computing)
2. Komponente im Canvas anklicken
3. Konfiguration im Tab anpassen

### Schritt 2: Konfigurieren

#### Via Canvas
- **Klick auf Node** → Öffnet richtigen Tab automatisch
- **IP-Adressen** werden direkt auf Node angezeigt
- **Drag** zum Verschieben

#### Via Tab (Network-Beispiel)
**VPC konfigurieren:**
- CIDR eingeben → Zeigt sofort "X IPs total, Y usable"
- DNS-Einstellungen aktivieren
- Region auswählen

**Subnet konfigurieren:**
- CIDR eingeben → Zeigt IP Range + Reserved IPs
- VPC auswählen
- Typ wählen: Public / Private / Database
- Availability Zone festlegen

**EC2 konfigurieren:**
- Instance Type wählen
- Subnet zuordnen
- Private IP: Auto oder Manual
- Public IP: Checkbox aktivieren

### Schritt 3: Verbindungen erstellen

Verbindungen zwischen Komponenten können aktuell manuell im JSON definiert werden. Eine UI-basierte Edge-Creation kommt in einer späteren Version.

### Schritt 4: Terraform generieren

1. Klick **"Save" Button** (Toolbar oben)
2. JSON wird in localStorage gespeichert
3. Über API: `POST /api/v1/terraform/generate-from-json`
4. Backend generiert Terraform-Dateien
5. Download als `.tf` Files

---

## Keyboard Shortcuts

- `Delete` / `Backspace` - Ausgewählte Komponenten löschen
- `Ctrl/Cmd + S` - Architektur speichern
- `Ctrl/Cmd + Z` - Undo (geplant)

---

## Beispiel: VPC mit EC2 & RDS

### 1. VPC hinzufügen
- Drag **"VPC"** auf Canvas
- **CIDR:** `10.0.0.0/16`
- **Region:** `us-east-1`
- → Zeigt "65,536 IPs total, 65,531 usable"

### 2. Public Subnet hinzufügen
- Drag **"Subnet"** auf Canvas
- **VPC:** Wähle "VPC 1"
- **CIDR:** `10.0.1.0/24`
- **Type:** Public
- **AZ:** `us-east-1a`
- → Zeigt "256 IPs, 251 usable"
- → AWS Reserved: `.0, .1, .2, .3, .255`

### 3. Private Subnet für Datenbank
- Drag **"Subnet"** auf Canvas
- **VPC:** Wähle "VPC 1"
- **CIDR:** `10.0.2.0/24`
- **Type:** Database
- **AZ:** `us-east-1a`

### 4. EC2 Instance hinzufügen
- Drag **"EC2"** auf Canvas
- **Name:** "web-server"
- **Instance Type:** t3.small
- **Subnet:** Wähle "Public Subnet"
- **Private IP:** Auto (wird aus 10.0.1.0/24 vergeben)
- **Public IP:** ☑ Aktivieren

### 5. RDS Database hinzufügen
- Drag **"RDS"** auf Canvas
- **Name:** "production-db"
- **Engine:** PostgreSQL
- **Instance Class:** db.t3.micro
- **Subnet Group:** Wähle "Database Subnet"

### 6. Terraform generieren
- Klick **"Save"** Button
- Terraform wird generiert:
  - `main.tf` - Provider-Konfiguration
  - `variables.tf` - Variablen
  - `vpc.tf` - VPC & Subnets
  - `ec2.tf` - EC2 Instance
  - `rds.tf` - RDS Database
  - `outputs.tf` - Outputs

---

## Toolbar-Funktionen

**Auto Layout** - Automatische Anordnung der Nodes (Breadth-First)  
**Fit to View** - Canvas an Viewport anpassen  
**Export Image** - Canvas als PNG exportieren  
**Delete** - Ausgewählte Komponenten löschen  
**Save** - Architektur speichern

---

## Troubleshooting

### Canvas ist leer
**Lösung:** Cytoscape.js nicht geladen → `npm install` ausführen + Dev-Server neu starten

### Drag & Drop funktioniert nicht
**Lösung:** Browser Console prüfen (F12) → Fehler in JavaScript?

### IP Calculator zeigt "0 IPs"
**Lösung:** CIDR-Format prüfen (z.B. `10.0.0.0/16`, nicht `10.0.0.0`)

### Tabs öffnen sich nicht bei Canvas-Click
**Lösung:** Event-Listener nicht registriert → Seite neu laden

### Komponente verschwindet nach Reload
**Lösung:** "Save" Button klicken bevor Seite geschlossen wird (localStorage)

### Backend-Fehler beim Terraform-Export
**Lösung:** Backend läuft? → `uvicorn app.main:app --reload --port 8000`

---

## Nächste Schritte

- [Detaillierter User Guide](./infrastructure-designer-guide.md)
- [Architecture Overview](./infrastructure-designer-architecture.md)
- [API Reference](./api/terraform-api.md)
- [Frontend README](../frontend/README_DESIGNER.md)

---

## Support

Bei Fragen oder Problemen:
1. Check Browser Console (F12)
2. Check Backend Logs
3. Siehe [Troubleshooting Guide](./guides/troubleshooting.md)

**Viel Erfolg beim Designen deiner Cloud-Infrastruktur!**
