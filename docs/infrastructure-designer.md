# Infrastructure Designer - Dokumentation

Zentrale Übersicht über alle Dokumentationen zum visuellen Infrastructure Designer.

---

## Was ist der Infrastructure Designer?

Der Infrastructure Designer ist ein visuelles Tool zum Entwerfen von Cloud-Infrastruktur mit einer intuitiven Drag & Drop-Oberfläche. Entwickelt für AWS (später Azure & GCP).

**Hauptfeatures:**
- 🎨 **Drag & Drop Canvas** - Visuelle Architektur mit Cytoscape.js
- 📋 **Tab-basierte Konfiguration** - 4 Tabs (Network, Security, Data, Computing)
- 🔢 **Inline IP Calculator** - Live CIDR-Berechnung
- 🔄 **Bidirektionale Synchronisation** - Canvas ↔ Tabs ↔ JSON
- 🏗️ **Terraform Code-Generierung** - Export als .tf-Dateien
- 💾 **Auto-Save** - localStorage Draft-Speicherung
- 📸 **PNG Export** - Canvas als Bild exportieren

---

## Dokumentationen

### 1. Quick Start Guide
**Zielgruppe:** Neue Benutzer  
**Dauer:** 10 Minuten  
**Inhalt:** Installation, erste Schritte, Beispiel-Architektur

**[→ Quick Start Guide](./infrastructure-designer-quickstart.md)**

**Du lernst:**
- Wie man den Designer installiert und startet
- Wie man Komponenten per Drag & Drop hinzufügt
- Wie man VPC, Subnets und EC2 konfiguriert
- Wie man Terraform generiert

---

### 2. User Guide
**Zielgruppe:** Benutzer & Architekten  
**Dauer:** 30-60 Minuten  
**Inhalt:** Vollständige Feature-Dokumentation

**[→ User Guide](./infrastructure-designer-guide.md)**

**Du lernst:**
- Alle Component Types (VPC, EC2, RDS, S3, Lambda, etc.)
- Alle Configuration Fields im Detail
- IP Calculator Funktionsweise
- Connection Types
- Terraform Output Format
- Best Practices (Netzwerk, Security, Cost, Performance)

---

### 3. Architecture Overview
**Zielgruppe:** Entwickler & Tech Leads  
**Dauer:** 30-45 Minuten  
**Inhalt:** Technische Systemarchitektur

**[→ Architecture Overview](./infrastructure-designer-architecture.md)**

**Du lernst:**
- System-Komponenten (Frontend & Backend)
- Data Flow (Drag & Drop → State → Terraform)
- Component Architecture (Canvas, Tabs, State, Sync)
- State Management (JSON Schema, Undo/Redo)
- Backend (TerraformGeneratorV2, Jinja2 Templates)
- Performance & Security Considerations

---

### 4. API Reference
**Zielgruppe:** Backend-Entwickler & Integratoren  
**Dauer:** 20-30 Minuten  
**Inhalt:** REST API Dokumentation

**[→ API Reference](./api/terraform-api.md)**

**Du lernst:**
- `/terraform/generate-from-json` - Terraform-Generierung
- `/terraform/validate` - Architektur-Validierung
- `/cidr/validate` - CIDR-Validierung
- `/cidr/plan` - Subnet-Planung
- `/terraform/estimate-cost` - Kostenschätzung
- JSON Schemas, Error Codes, Rate Limits

---

### 5. Frontend Developer Guide
**Zielgruppe:** Frontend-Entwickler  
**Dauer:** 45-60 Minuten  
**Inhalt:** Code-Struktur, Komponenten, Testing

**[→ Frontend README](../frontend/README_DESIGNER.md)**

**Du lernst:**
- File-Struktur (Components, Lib, Pages)
- Wie man einen neuen Component Type hinzufügt
- Testing (Unit Tests, E2E Tests)
- Styling (Tailwind, Custom CSS)
- Performance Tips
- Build & Deployment

---

## Schnelleinstieg nach Rolle

### Ich bin Benutzer (Cloud Architect)
1. [Quick Start Guide](./infrastructure-designer-quickstart.md) - Erste Schritte
2. [User Guide](./infrastructure-designer-guide.md) - Alle Features lernen
3. [Best Practices](./infrastructure-designer-guide.md#best-practices) - Optimale Architektur

### Ich bin Frontend-Entwickler
1. [Frontend README](../frontend/README_DESIGNER.md) - Setup & Code-Struktur
2. [Architecture Overview](./infrastructure-designer-architecture.md) - Wie alles zusammenhängt
3. [API Reference](./api/terraform-api.md) - Backend-Integration

### Ich bin Backend-Entwickler
1. [Architecture Overview](./infrastructure-designer-architecture.md) - System-Design
2. [API Reference](./api/terraform-api.md) - API Endpoints
3. [Terraform Generator Docs](./guides/terraform-generation.md) - Template-System

### Ich bin DevOps Engineer
1. [Quick Start Guide](./infrastructure-designer-quickstart.md) - Installation
2. [Deployment Guide](./DEPLOYMENT_GUIDE.md) - Production Deployment
3. [Operations](./operations/) - Monitoring, Logging, Backup

---

## Testing

Der Infrastructure Designer wurde einem umfassenden Test unterzogen.

**Test-Reports:**
- **[Testing Guide](./testing/TESTING.md)** - Wie man Tests ausführt
- **[Test Report](../TEST_REPORT_INFRASTRUCTURE_DESIGNER.md)** - Aktuelle Test-Ergebnisse
- **[Bug Tracking](../INFRASTRUCTURE_DESIGNER_BUGS.md)** - Bekannte Issues

**Test-Status:**
- ✅ Backend API Tests (pytest)
- ✅ Frontend Component Tests (manuell)
- ⏳ E2E Tests (Playwright) - in Arbeit
- ⏳ Performance Tests - geplant

**Test-Coverage:**
- Backend: TBD
- Frontend: TBD

**Mehr Details:** Siehe [Testing Guide](./testing/TESTING.md)

---

## Häufig gestellte Fragen

### Kann ich bestehende Terraform-Dateien importieren?
**Status:** Geplant für Version 2.0  
**Aktuell:** Nur JSON-Import möglich

### Unterstützt der Designer Multi-Cloud (Azure, GCP)?
**Status:** AWS MVP (Version 1.0)  
**Roadmap:**
- Azure - Q3 2026
- GCP - Q4 2026

### Kann ich eigene Component Types hinzufügen?
**Ja!** Siehe [Frontend Developer Guide - Neuen Component Type hinzufügen](../frontend/README_DESIGNER.md#neuen-component-type-hinzufügen)

### Wie funktioniert die Cost Estimation?
Basiert auf AWS Pricing API. Siehe [API Reference - Estimate Cost](./api/terraform-api.md#5-estimate-cost)

### Gibt es eine CLI-Version?
**Status:** Geplant für Version 2.0  
CLI wird Terraform direkt generieren ohne UI.

### Kann ich Architekturen mit meinem Team teilen?
**Status:** Geplant für Version 1.5 (Real-time Collaboration)  
**Aktuell:** JSON-Export/Import möglich

---

## Video Tutorials

### Grundlagen (10 min)
[![Video Thumbnail](https://img.youtube.com/vi/PLACEHOLDER/maxresdefault.jpg)](https://youtube.com/watch?v=PLACEHOLDER)

**Inhalt:**
- Installation & Setup
- Erste Architektur erstellen
- VPC mit EC2 und RDS

### Advanced Features (20 min)
[![Video Thumbnail](https://img.youtube.com/vi/PLACEHOLDER/maxresdefault.jpg)](https://youtube.com/watch?v=PLACEHOLDER)

**Inhalt:**
- Multi-AZ Setups
- Security Groups & NACLs
- Load Balancer & Auto Scaling
- Cost Optimization

---

## Beispiel-Architekturen

### 1. Simple Web Application
**Komponenten:** VPC, 2 Public Subnets, 2 Private Subnets, ALB, 2x EC2, RDS

**[→ JSON Download](./examples/simple-web-app.json)**  
**[→ Terraform Files](./examples/simple-web-app/)**

**Monatliche Kosten:** ~$150

---

### 2. Serverless API
**Komponenten:** API Gateway, Lambda, DynamoDB, S3

**[→ JSON Download](./examples/serverless-api.json)**  
**[→ Terraform Files](./examples/serverless-api/)**

**Monatliche Kosten:** ~$20 (+ usage-based)

---

### 3. High-Availability Setup
**Komponenten:** VPC, 6 Subnets (3 AZs), ALB, Auto Scaling Group, RDS Multi-AZ, ElastiCache

**[→ JSON Download](./examples/ha-setup.json)**  
**[→ Terraform Files](./examples/ha-setup/)**

**Monatliche Kosten:** ~$500

---

## Roadmap

### Version 1.0 (MVP) - Q2 2026 ✅
- [x] Drag & Drop Canvas
- [x] 15 AWS Component Types
- [x] Inline IP Calculator
- [x] Terraform Generation
- [x] localStorage Draft-Speicherung

### Version 1.5 - Q3 2026
- [ ] Real-time Collaboration (WebSockets)
- [ ] Cost Estimation
- [ ] Security Best Practice Warnings
- [ ] Version History
- [ ] Comments on Components

### Version 2.0 - Q4 2026
- [ ] Azure Resource Manager Templates
- [ ] GCP Deployment Manager
- [ ] Terraform Import (existing infrastructure)
- [ ] CLI Version
- [ ] AI-Powered Suggestions

### Version 3.0 - Q1 2027
- [ ] Kubernetes YAML Generation
- [ ] Multi-Cloud Hybrid Architectures
- [ ] Advanced Cost Optimization
- [ ] Compliance Checks (GDPR, HIPAA, etc.)

---

## Support & Community

### Dokumentation durchsuchen
```bash
# Lokale Suche
grep -r "VPC" docs/

# Online
https://docs.stackvertex.io/search?q=vpc
```

### GitHub Issues
Fehler gefunden? Feature Request?  
**[→ GitHub Issues](https://github.com/stackvertex/stackvertex/issues)**

### Discord Community
Fragen? Diskussionen?  
**[→ Join Discord](https://discord.gg/stackvertex)**

### Support E-Mail
**support@stackvertex.io**

---

## Changelog

### v1.0.0 (2026-05-16)
- ✨ Initial Release
- ✨ 15 AWS Component Types
- ✨ Terraform Generation
- ✨ Inline IP Calculator
- ✨ localStorage Auto-Save

### v0.9.0 (2026-05-01) - Beta
- ✨ Beta Release für Testing
- 🐛 Bug Fixes aus Alpha

### v0.5.0 (2026-04-01) - Alpha
- ✨ Alpha Release
- 🎨 Canvas Prototype

---

## Lizenz

**StackVertex Infrastructure Designer**  
© 2026 StackVertex  
Lizenz: MIT

Siehe [LICENSE](../LICENSE) für Details.

---

## Mitwirken

Pull Requests sind willkommen!

**Contribution Guide:**
1. Fork Repository
2. Feature Branch erstellen (`git checkout -b feature/amazing-feature`)
3. Commit (`git commit -m 'Add amazing feature'`)
4. Push (`git push origin feature/amazing-feature`)
5. Pull Request öffnen

**Code of Conduct:** [CODE_OF_CONDUCT.md](../CODE_OF_CONDUCT.md)

---

## Kontakt

**Projekt Lead:** Andy Schwarz  
**E-Mail:** schwarz23andy@gmail.com  
**GitHub:** [@AndySchw](https://github.com/AndySchw)

---

**Viel Erfolg beim Designen deiner Cloud-Infrastruktur!** 🚀
