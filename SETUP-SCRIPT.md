# OverCloud - Automatisches Setup Script

> Ein-Klick-Installation für alle Prerequisites und Projekt-Initialisierung

---

## 🚀 Quick Start

```bash
# Navigiere zum Projektordner
cd /Users/andyschwarz/Documents/Privat/OverCloud

# Führe Setup-Script aus
./setup.sh
```

**Das war's!** Das Script macht den Rest automatisch.

---

## 📋 Was das Script macht

### Step 1: Homebrew
- ✅ Prüft ob Homebrew installiert ist
- ⚙️ Installiert Homebrew falls nicht vorhanden

### Step 2: Python 3.11+
- ✅ Prüft ob Python 3.11+ installiert ist
- ⚙️ Installiert `python@3.11` via Homebrew falls nötig

### Step 3: Node.js 20+
- ✅ Prüft ob Node.js v20+ installiert ist
- ⚙️ Installiert `node@20` via Homebrew falls nötig

### Step 4: Poetry
- ✅ Prüft ob Poetry installiert ist
- ⚙️ Installiert Poetry via `install.python-poetry.org`
- ⚙️ Fügt Poetry zu `$PATH` hinzu (in `~/.zshrc` oder `~/.bashrc`)
- ⚙️ **Konfiguriert Poetry für projekt-lokale venvs:**
  ```bash
  poetry config virtualenvs.in-project true
  ```

### Step 5: AWS CLI (Optional)
- ✅ Prüft ob AWS CLI installiert ist
- ⚙️ Fragt ob installiert werden soll
- ⚙️ Installiert `awscli` via Homebrew (falls gewünscht)

### Step 6: Terraform (Optional)
- ✅ Prüft ob Terraform installiert ist
- ⚙️ Fragt ob installiert werden soll
- ⚙️ Installiert `terraform` via Homebrew (falls gewünscht)

### Step 7: Backend Initialisierung
- ⚙️ Erstellt `backend/` Verzeichnis
- ⚙️ Initialisiert Poetry Projekt (`pyproject.toml`)
- ⚙️ Installiert alle Python Dependencies:
  - **Core:** fastapi, uvicorn, pydantic, boto3, sqlalchemy, alembic
  - **Dev:** pytest, black, ruff, mypy, httpx
- ⚙️ Erstellt `backend/.venv/` (projekt-lokal!)

### Step 8: Frontend Initialisierung
- ⚙️ Erstellt `frontend/` Verzeichnisstruktur
- ⚙️ Initialisiert NPM Projekt (`package.json`)
- ⚙️ Installiert alle Node Dependencies:
  - **Build:** vite
  - **Styling:** tailwindcss, postcss, autoprefixer
- ⚙️ Initialisiert Tailwind CSS Konfiguration
- ⚙️ Erstellt `frontend/node_modules/` (projekt-lokal!)

### Step 9: Git Initialisierung
- ⚙️ Erstellt `.gitignore` (falls nicht vorhanden)
- ⚙️ Initialisiert Git Repository (falls nicht vorhanden)
- ⚙️ Erstellt initialen Commit

---

## 🎯 Nach dem Setup

Das Script zeigt dir am Ende:

```
✓ Alle Prerequisites installiert
✓ Backend initialisiert (Python + Poetry)
✓ Frontend initialisiert (Vanilla JS + Vite)

Verzeichnisstruktur:
  backend/.venv/          ← Python Virtual Environment
  frontend/node_modules/  ← NPM Dependencies

Nächste Schritte:
  1. Backend testen:
     cd backend
     poetry shell
     python --version

  2. Frontend testen:
     cd frontend
     npm run dev

  3. Claude Code Tools installieren:
     Siehe docs/SETUP.md
```

---

## ⚙️ Interaktive Bestätigungen

Das Script fragt dich bei folgenden Schritten um Erlaubnis:

1. **Setup starten?** (Ja/Nein)
2. **Homebrew installieren?** (falls nicht vorhanden)
3. **Python 3.11 installieren?** (falls zu alt oder nicht vorhanden)
4. **Node.js 20 installieren?** (falls zu alt oder nicht vorhanden)
5. **Poetry installieren?** (falls nicht vorhanden)
6. **AWS CLI installieren?** (optional)
7. **Terraform installieren?** (optional)
8. **Dependencies neu installieren?** (falls schon vorhanden)

**Du hast volle Kontrolle** über jede Installation!

---

## 🔄 Re-Run des Scripts

### Szenario 1: Alles ist schon installiert
```bash
./setup.sh
```

**Resultat:**
- Script erkennt vorhandene Installationen
- Überspringt bereits installierte Tools
- Fragt nur bei Dependencies ob neu installiert werden soll

### Szenario 2: Nur Dependencies neu installieren
```bash
./setup.sh
```

**Resultat:**
- Script überspringt Homebrew, Python, Node, Poetry
- Fragt: "Dependencies neu installieren?"
- Führt `poetry install` und `npm install` aus

### Szenario 3: Backend existiert, Frontend fehlt
```bash
./setup.sh
```

**Resultat:**
- Backend wird übersprungen (fragt nur nach Dependencies)
- Frontend wird komplett initialisiert

**Das Script ist idempotent** - kann beliebig oft ausgeführt werden!

---

## 🛠️ Troubleshooting

### Script findet Poetry nicht nach Installation

```bash
# Reload shell
source ~/.zshrc

# Verify
poetry --version
```

### .venv wird nicht erstellt

Das Script konfiguriert automatisch:
```bash
poetry config virtualenvs.in-project true
```

Falls trotzdem nicht vorhanden:
```bash
cd backend
poetry env remove python
poetry install
ls -la .venv/  # Sollte jetzt existieren
```

### Permission Denied beim Ausführen

```bash
chmod +x setup.sh
./setup.sh
```

### Script bricht ab

Das Script nutzt `set -e` (exit on error).

**Letzter Fehler sehen:**
```bash
echo $?  # Exit code des letzten Commands
```

**Manuell weitermachen:**
Siehe `QUICKSTART.md` für manuelle Schritte

---

## 📖 Was das Script NICHT macht

Das Script installiert **NICHT**:
- ❌ Claude Code Tools (Superpowers, GSD, Agent Swarm)
- ❌ Docker (optional)
- ❌ Backend/Frontend Code (nur Dependencies)

**Dafür siehe:**
- Claude Code Tools: `docs/SETUP.md` (Phase 1)
- Backend Code: Wird von Agents erstellt (Phase 1)
- Frontend Code: Wird von Agents erstellt (Phase 1)

---

## 🔍 Script Log ausgeben

```bash
# Script mit Verbose Output
./setup.sh 2>&1 | tee setup.log

# Log anschauen
cat setup.log
```

---

## ✅ Verification nach Setup

```bash
# Check Backend
cd backend
ls -la .venv/          # ✅ Sollte existieren
poetry run python --version  # ✅ Sollte 3.11+ zeigen

# Check Frontend
cd ../frontend
ls -la node_modules/   # ✅ Sollte existieren
npm list --depth=0     # ✅ Zeigt installierte Packages

# Check Git
git status             # ✅ .venv/ und node_modules/ ignoriert
```

---

## 🎨 Script Features

### Colored Output
- 🔵 Blau = Info
- 🟢 Grün = Success
- 🟡 Gelb = Warning
- 🔴 Rot = Error

### Progress Indication
```
================================================
  Step 1/8: Homebrew
================================================

✓ Homebrew ist bereits installiert
```

### Smart Detection
- Prüft ob Tools bereits installiert sind
- Überspringt unnötige Schritte
- Fragt nur bei Bedarf

---

## 🚀 Nächste Schritte nach Setup

### 1. Verify Installation
```bash
# Backend
cd backend
poetry shell
python --version
which python  # Sollte .venv/bin/python zeigen

# Frontend
cd ../frontend
npm run dev  # (nach Scaffolding)
```

### 2. Claude Code Tools installieren
```bash
# Siehe docs/SETUP.md
npx @joshuapowell/superpowers install
npm install -g @gsd-build/cli
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
```

### 3. Code Scaffolding
Sag Claude: **"Setup fertig, erstelle Backend + Frontend Scaffolding!"**

---

## 📞 Support

Bei Problemen:
1. Check `setup.log` (falls erstellt)
2. Siehe `QUICKSTART.md` für manuelle Schritte
3. Siehe `docs/SETUP.md` für Details
4. Frag Claude: "Problem bei Schritt X"

---

**Viel Erfolg beim Setup! 🚀**

---

**Last Updated:** 2026-03-22
