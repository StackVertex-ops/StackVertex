# VPC/CIDR Calculator - Demo Script

## Übersicht

Diese Anleitung zeigt die Features des CIDR Calculators Schritt für Schritt. Ideal für Screenshots, Videos oder Präsentationen.

## Setup

```bash
# Terminal 1: Backend starten
cd backend
poetry run uvicorn app.main:app --reload

# Terminal 2: Frontend starten
cd frontend
npm run dev

# Browser öffnen
open http://localhost:5173/cidr-calculator.html
```

---

## Demo 1: Einfache VPC Validierung

### Schritt 1: VPC CIDR eingeben
- Gib `10.0.0.0/16` in das VPC CIDR Feld ein
- Klicke "Validieren"

**Erwartetes Ergebnis:**
```
✓ Gültiger CIDR Block
Total IPs: 65,536
Usable IPs: 65,531 (minus 5 reserved)
CIDR Block: 10.0.0.0/16
```

### Schritt 2: Ungültigen CIDR testen
- Gib `10.0.0.0/8` ein (zu klein für AWS VPC)
- Klicke "Validieren"

**Erwartetes Ergebnis:**
```
⚠️ VPC CIDR muss mindestens /16 sein (AWS Limit)
```

### Schritt 3: Öffentliche IP-Range testen
- Gib `8.8.8.0/24` ein
- Klicke "Validieren"

**Erwartetes Ergebnis:**
```
✓ Gültiger CIDR Block
⚠️ Warnung: Öffentliche IP-Range wird normalerweise nicht für VPC verwendet
```

---

## Demo 2: Automatische Subnet-Vorschläge

### Schritt 1: VPC validieren
- VPC CIDR: `10.0.0.0/16`
- Klicke "Validieren"

### Schritt 2: Vorschläge öffnen
- Klicke "Vorschläge"

**Modal öffnet sich:**
```
Subnet-Vorschläge generieren
Anzahl Availability Zones: [3]
Subnet-Typen:
☑ Public
☑ Private
☑ Database
```

### Schritt 3: Standard-Vorschläge generieren
- Lasse alle Einstellungen wie sie sind
- Klicke "Generieren"

**Erwartetes Ergebnis:**
9 Subnets werden automatisch generiert:
- 3x Public (eine pro AZ)
- 3x Private (eine pro AZ)
- 3x Database (eine pro AZ)

### Schritt 4: VPC Plan berechnen
- Klicke "VPC Plan berechnen"

**Visueller Plan erscheint:**
- Grüne Balken zeigen IP-Allocation
- Subnet-Karten mit Details
- Keine Overlaps (✓ Status)

---

## Demo 3: Manuelle Subnet-Planung mit Overlap-Erkennung

### Schritt 1: VPC validieren
- VPC CIDR: `10.0.0.0/16`
- Klicke "Validieren"

### Schritt 2: Erstes Subnet hinzufügen
- Klicke "+ Subnet hinzufügen"
- Name: `public-1a`
- CIDR: `10.0.1.0/24`
- Typ: `Public`
- AZ: `us-east-1a`

### Schritt 3: Zweites Subnet hinzufügen (überlappend)
- Klicke "+ Subnet hinzufügen"
- Name: `private-1a`
- CIDR: `10.0.1.0/24` (GLEICHER CIDR!)
- Typ: `Private`
- AZ: `us-east-1a`

### Schritt 4: VPC Plan berechnen
- Klicke "VPC Plan berechnen"

**Erwartetes Ergebnis:**
```
⚠️ Overlaps erkannt!
Overlap: private-1a (10.0.1.0/24) überschneidet sich mit public-1a (10.0.1.0/24)
```

- Roter Balken statt grün
- Status: ✗

### Schritt 5: Overlap beheben
- Ändere zweites Subnet CIDR zu `10.0.2.0/24`
- Klicke "VPC Plan berechnen"

**Erwartetes Ergebnis:**
- Grüner Balken
- Status: ✓ Keine Overlaps

---

## Demo 4: Detaillierte Subnet-Informationen

### Schritt 1: VPC mit Subnets planen
- VPC CIDR: `10.0.0.0/16`
- Füge ein Subnet hinzu: `10.0.1.0/24`
- Berechne Plan

### Schritt 2: Subnet-Details anzeigen
- Klicke auf "Reserved IPs (5)" Details

**Erwartetes Ergebnis:**
```
10.0.1.0   (Network)
10.0.1.1   (VPC Router)
10.0.1.2   (DNS)
10.0.1.3   (Reserved)
10.0.1.255 (Broadcast)
```

### Schritt 3: Subnet-Statistiken prüfen
```
Total IPs: 256
Usable IPs: 251
First IP: 10.0.1.0
Last IP: 10.0.1.255
```

---

## Demo 5: Production-Ready VPC Setup

### Szenario: 3-Tier Web Application

**Ziel:**
- 3 Availability Zones
- Public Subnets für Load Balancer
- Private Subnets für Application Server
- Database Subnets für RDS

### Schritt 1: VPC CIDR
- Gib `10.0.0.0/16` ein
- Validieren

### Schritt 2: Vorschläge generieren
- Anzahl AZs: `3`
- Subnet-Typen: `Public`, `Private`, `Database`
- Klicke "Generieren"

### Schritt 3: Generierte Subnets prüfen
```
public-a     10.0.0.0/20   (4.091 usable)
public-b     10.0.16.0/20  (4.091 usable)
public-c     10.0.32.0/20  (4.091 usable)

private-a    10.0.48.0/20  (4.091 usable)
private-b    10.0.64.0/20  (4.091 usable)
private-c    10.0.80.0/20  (4.091 usable)

database-a   10.0.96.0/20  (4.091 usable)
database-b   10.0.112.0/20 (4.091 usable)
database-c   10.0.128.0/20 (4.091 usable)
```

### Schritt 4: Plan berechnen
- Klicke "VPC Plan berechnen"

**Erwartetes Ergebnis:**
```
VPC Plan: 10.0.0.0/16

IP Allocation: 21.3% verwendet
36,864 IPs allocated
28,672 IPs frei

Subnets (9)
✓ Status: Keine Overlaps
```

### Schritt 5: Export (Future)
- Aktuell: Manuell übernehmen
- Zukünftig: "Export als Terraform" Button

---

## Demo 6: Edge Cases & Validierung

### Test 1: Subnet außerhalb VPC
- VPC: `10.0.0.0/16`
- Subnet: `192.168.1.0/24`
- Berechne Plan

**Ergebnis:**
```
⚠️ Overlap: subnet-1 (192.168.1.0/24) liegt außerhalb der VPC 10.0.0.0/16
```

### Test 2: Zu kleines Subnet
- VPC: `10.0.0.0/16`
- Subnet: `10.0.1.0/29` (8 IPs, > /28 Limit)
- Berechne Plan

**Ergebnis:**
```
⚠️ Subnet 10.0.1.0/29 darf höchstens /28 sein (AWS Limit)
```

### Test 3: Maximale Auslastung
- VPC: `10.0.0.0/24` (256 IPs)
- 51 Subnets mit `/30` (4 IPs each)
- Berechne Plan

**Ergebnis:**
```
IP Allocation: 79.7% verwendet
204 IPs allocated
52 IPs frei
```

---

## Screenshot-Checklist

Für Dokumentation folgende Screenshots erstellen:

- [ ] **Landing Page** - Voller Calculator, leer
- [ ] **VPC Validierung** - Grünes Validierungsergebnis
- [ ] **VPC Übersicht** - Box mit Total/Usable IPs
- [ ] **Vorschläge Modal** - Subnet-Vorschläge Generator
- [ ] **Subnet Liste** - 3-4 Subnets manuell eingegeben
- [ ] **Visueller Plan** - Plan mit Balken und Subnet-Karten
- [ ] **Overlap-Erkennung** - Roter Alert mit Details
- [ ] **Subnet Details** - Aufgeklappte Reserved IPs
- [ ] **Production Setup** - 9 Subnets, 3 AZs, voller Plan
- [ ] **Mobile View** - Responsive Design

---

## API Demo (cURL)

### Validierung
```bash
curl -X POST http://localhost:8000/api/v1/cidr/validate \
  -H "Content-Type: application/json" \
  -d '{"cidr": "10.0.0.0/16"}' | jq
```

### Vorschläge
```bash
curl -X POST http://localhost:8000/api/v1/cidr/suggest \
  -H "Content-Type: application/json" \
  -d '{
    "vpc_cidr": "10.0.0.0/16",
    "num_azs": 3,
    "subnet_types": ["public", "private"]
  }' | jq
```

### VPC Plan
```bash
curl -X POST http://localhost:8000/api/v1/cidr/plan \
  -H "Content-Type: application/json" \
  -d '{
    "vpc_cidr": "10.0.0.0/16",
    "subnets": [
      {"name": "public-1a", "cidr": "10.0.1.0/24", "type": "public"},
      {"name": "private-1a", "cidr": "10.0.2.0/24", "type": "private"}
    ]
  }' | jq
```

---

## Präsentations-Script

**Intro (30 Sek.)**
> "Heute zeige ich euch den VPC/CIDR Calculator - ein Tool zur Planung von AWS Netzwerken. Er hilft bei der Berechnung von IP-Adressen, erkennt Overlaps und schlägt optimale Konfigurationen vor."

**Demo 1: Validierung (1 Min.)**
> "Zuerst gebe ich einen VPC CIDR Block ein. AWS erlaubt nur /16 bis /28. Der Calculator prüft das automatisch und zeigt mir, wie viele IPs verfügbar sind."

**Demo 2: Automatische Vorschläge (1 Min.)**
> "Für Production möchte ich 3 Availability Zones mit Public, Private und Database Subnets. Statt alles manuell zu rechnen, nutze ich die Vorschläge-Funktion."

**Demo 3: Overlap-Erkennung (1 Min.)**
> "Was passiert bei Fehlern? Ich gebe absichtlich zwei überlappende Subnets ein. Der Calculator erkennt das sofort und zeigt mir genau welche Subnets sich überschneiden."

**Demo 4: Visueller Plan (1 Min.)**
> "Der finale Plan zeigt die komplette IP-Allocation visuell. Ich sehe auf einen Blick: 9 Subnets, keine Overlaps, 28.000 IPs noch frei für zukünftiges Wachstum."

**Outro (30 Sek.)**
> "Der Calculator ist vollständig getestet, hat eine REST API und kann später in den OverCloud Architecture Builder integriert werden. Alle Features sind production-ready."

---

**Gesamtdauer:** ~5 Minuten
**Technologien:** Python/FastAPI Backend, Vanilla JS Frontend, Tailwind CSS
**Tests:** 47 Tests, alle bestanden
