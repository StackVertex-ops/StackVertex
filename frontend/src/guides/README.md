# OverCloud Guides

## Übersicht

Dieses Verzeichnis enthält interaktive Schritt-für-Schritt-Anleitungen für OverCloud-Nutzer.

## Verfügbare Guides

### ✅ Fertig

- **`aws-setup.html`** - AWS Account Setup Guide (komplett, interaktiv)
- **`index.html`** - Guides Übersichtsseite

### ⏳ Geplant

- Security Best Practices
- Erste Architektur deployen
- Cost Optimization
- CI/CD Setup
- Monitoring & Alerting

## Guide-Struktur

Alle Guides folgen demselben Format:

### HTML-Guides (Interaktiv)

**Vorteile:**
- Tabs für verschiedene Sektionen
- Copy-Paste-fähige Code-Snippets
- Responsive Design (Mobile-friendly)
- Keine Dependencies (Pure HTML/CSS/JS)

**Struktur:**
```html
<!DOCTYPE html>
<html lang="de">
<head>
    <title>Guide Titel</title>
    <style>
        /* Inline CSS für Portabilität */
    </style>
</head>
<body>
    <header>
        <h1>Guide Titel</h1>
    </header>
    
    <div class="tabs">
        <!-- Tab Navigation -->
    </div>
    
    <div class="tab-content">
        <!-- Inhalte mit Beispielen, Code, Checklisten -->
    </div>
    
    <script>
        /* Interaktivität (Tab-Switching, etc.) */
    </script>
</body>
</html>
```

## Neuen Guide erstellen

### 1. HTML-Guide erstellen

```bash
# Kopiere Template
cp aws-setup.html new-guide.html

# Anpassen:
# - Title ändern
# - Header anpassen
# - Tabs definieren
# - Inhalte schreiben
```

### 2. In Index hinzufügen

`index.html` erweitern:

```html
<a href="new-guide.html" class="guide-card">
    <div class="guide-icon">🎯</div>
    <h2>Neuer Guide Titel</h2>
    <p>Beschreibung...</p>
    <div class="guide-meta">
        <span class="badge beginner">Einsteiger</span>
        <span class="badge">~X Minuten</span>
    </div>
</a>
```

### 3. In Hauptnavigation verlinken

`frontend/src/index.html` erweitern (wenn vorhanden):

```html
<nav>
    <a href="/guides">Anleitungen</a>
</nav>
```

## Best Practices für Guides

### Inhalt

✅ **Do:**
- Schritt-für-Schritt (nummeriert)
- Screenshots wo hilfreich
- Copy-Paste-fähige Commands
- Checklisten am Ende
- Häufige Fehler + Lösungen

❌ **Don't:**
- Zu technisch (Zielgruppe: Einsteiger)
- Zu lang (max. 30 Minuten Lesezeit)
- Veraltete Screenshots
- Links zu externen Seiten (können veralten)

### Code-Snippets

**Format:**
```html
<div class="command-box">
<pre>
aws configure --profile overcloud
AWS Access Key ID: AKIA...
AWS Secret Access Key: ***
Default region: eu-central-1
</pre>
</div>
```

**Regeln:**
- Immer mit Kontext (was tut dieser Command?)
- Sensitive Daten maskieren (`***`)
- Kommentare inline

### Warnungen & Tipps

**Info-Box:**
```html
<div class="info-box">
    💡 <strong>Tipp:</strong> ...
</div>
```

**Warning-Box:**
```html
<div class="warning-box">
    ⚠️ <strong>Achtung:</strong> ...
</div>
```

**Success-Box:**
```html
<div class="success-box">
    ✅ <strong>Fertig:</strong> ...
</div>
```

## Wartung

### Monatlich
- [ ] Screenshots auf Aktualität prüfen
- [ ] Links testen (404 errors?)
- [ ] Code-Snippets verifizieren (noch korrekt?)

### Bei AWS/Cloud-Provider-Änderungen
- [ ] UI-Screenshots aktualisieren
- [ ] Neue Features erwähnen
- [ ] Veraltete Informationen entfernen

## Feedback

Nutzer können Feedback geben via:
- Email: support@overcloud.io
- GitHub Issues: [github.com/AndySchw/OverCloud/issues](https://github.com/AndySchw/OverCloud/issues)

Alle Feedback-Punkte werden in einem Backlog gesammelt und priorisiert.

## Beispiel-Guide: AWS Setup

**URL:** `/guides/aws-setup.html`

**Sections:**
1. Account erstellen (Step-by-Step)
2. Security Setup (MFA, IAM)
3. Billing & Cost Management
4. IAM Users & Policies
5. Best Practices Checklist

**Zielgruppe:** Einsteiger (keine Cloud-Vorkenntnisse)  
**Dauer:** ~30 Minuten  
**Format:** Interaktive Tabs mit Copy-Paste Commands

---

**Maintainer:** Andy Schwarz  
**Last Updated:** 2026-05-15
