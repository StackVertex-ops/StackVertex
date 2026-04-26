# Security Policy

## Supported Versions

Wir unterstützen derzeit folgende Versionen mit Security Updates:

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

**BITTE KEINE ÖFFENTLICHEN GITHUB ISSUES FÜR SICHERHEITSLÜCKEN!**

Wenn du eine Sicherheitslücke in OverCloud findest, melde sie bitte verantwortungsvoll:

### 1. Private Meldung

Nutze GitHub's [Private Security Reporting](https://github.com/AndySchw/OverCloud/security/advisories/new):
- Gehe zu "Security" → "Advisories" → "New draft security advisory"
- Beschreibe die Lücke detailliert
- Füge PoC (Proof of Concept) hinzu falls möglich

**Oder per E-Mail:**
- An: schwarz23andy@gmail.com
- Betreff: `[SECURITY] OverCloud Vulnerability Report`

### 2. Was gehört in den Report?

- **Beschreibung:** Was ist die Schwachstelle?
- **Impact:** Was kann ein Angreifer damit machen?
- **Reproduction:** Schritt-für-Schritt Anleitung
- **Affected Versions:** Welche Versionen betroffen?
- **Suggested Fix:** (Optional) Deine Idee zur Behebung

### 3. Response Timeline

- **24-48h:** Erste Rückmeldung & Bestätigung
- **7 Tage:** Analyse & Risikobewertung
- **30 Tage:** Fix entwickeln & testen
- **Coordinated Disclosure:** Gemeinsame Veröffentlichung nach Fix

## Security Features

OverCloud implementiert folgende Security Maßnahmen:

### 🔒 Authentication & Authorization
- JWT-basierte Authentication
- AWS IAM Role-based Access (AssumeRole, keine Access Keys)
- Least Privilege Principle für alle Permissions

### 🛡️ Data Protection
- Secrets verschlüsselt in AWS Secrets Manager
- Keine Plaintext Credentials in Code oder Config
- TLS/SSL für alle Netzwerk-Verbindungen
- S3 Server-Side Encryption (SSE-S3)

### 📊 Audit Logging
- Alle kritischen Actions werden geloggt
- Time-partitioned Audit Logs (GDPR-konform löschbar)
- CloudWatch Integration für Monitoring

### 🔍 Automated Security Scanning
- **GitGuardian:** Secret Detection in Commits
- **Bandit:** Python Security Linter
- **Safety:** Dependency Vulnerability Scanning
- **Semgrep:** SAST (Static Application Security Testing)
- **CodeQL:** GitHub's Code Analysis Engine
- **Dependabot:** Automatische Dependency Security Updates

### 🚨 Security Policies
- Keine Secrets in Environment Variables (nur Secrets Manager)
- Input Validation mit Pydantic Schemas
- SQL Injection Prevention (SQLAlchemy ORM)
- XSS Prevention (Framework-Level Escaping)
- CORS Policies (Whitelist-based)

## Known Security Considerations

### Cloud Credentials
- **Niemals AWS Access Keys nutzen** → Nur IAM Roles mit AssumeRole
- Credentials werden write-only gespeichert (wie GitHub Secrets)
- User sieht nur `***REDACTED***` nach dem Speichern

### Terraform State
- Terraform State enthält sensible Daten → IMMER in S3 mit Encryption
- State Files werden NIEMALS in DynamoDB gespeichert (zu groß + Security Risk)
- State Locking via DynamoDB zur Vermeidung von Race Conditions

### Multi-Tenancy
- Jeder User hat isolierte AWS Accounts/Ressourcen
- Keine Shared Infrastructure zwischen Usern
- Platform und Customer Data sind getrennt

## Security Best Practices für Contributors

### Before Committing
- ✅ Keine Secrets im Code (`git diff` prüfen!)
- ✅ `.env` Files in `.gitignore`
- ✅ Sensitive Test Data in Fixtures, nicht hardcoded
- ✅ Pre-commit Hooks für Secret Detection nutzen

### Code Review Checklist
- [ ] Input Validation vorhanden?
- [ ] Authentication/Authorization geprüft?
- [ ] Sensible Daten in Logs vermieden?
- [ ] SQL Injection Risiko ausgeschlossen?
- [ ] XSS Prevention beachtet?
- [ ] Error Messages enthalten keine sensiblen Infos?

### Dependencies
- ✅ Nur npm/pip von vertrauenswürdigen Registries
- ✅ Lock Files committen (poetry.lock, package-lock.json)
- ✅ Regelmäßig `poetry update` / `npm audit fix`
- ✅ Dependabot PRs zeitnah reviewen

## Security Updates

Wir veröffentlichen Security Updates:
- **Critical:** Sofort als Hotfix
- **High:** Innerhalb 7 Tage
- **Medium:** Im nächsten Minor Release
- **Low:** Im nächsten Major Release

## Responsible Disclosure Hall of Fame

Danke an alle Security Researcher, die uns geholfen haben OverCloud sicherer zu machen:

<!-- 
- [Name] - [Vulnerability Type] - [Date]
-->

_Liste wird nach Coordinated Disclosure aktualisiert._

## Contact

Security Team: schwarz23andy@gmail.com

**Verschlüsselte Kommunikation:** PGP Key auf Anfrage
