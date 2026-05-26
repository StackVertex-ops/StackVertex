# Information Security Management System (ISMS) Policy

## ISO 27001:2022 Compliance

**Document Version:** 1.0  
**Effective Date:** 2026-05-15  
**Review Date:** 2027-05-15  
**Owner:** Andy Schwarz (CEO & CISO)  
**Classification:** Internal

---

## 1. Executive Summary

Dieses Dokument definiert die Information Security Management System (ISMS) Policy von StackVertex gemäß ISO/IEC 27001:2022. Das ISMS stellt sicher, dass alle Informationssicherheitsrisiken systematisch identifiziert, bewertet und behandelt werden.

### 1.1 Zweck

- Schutz der Vertraulichkeit, Integrität und Verfügbarkeit von Informationen
- Erfüllung gesetzlicher und vertraglicher Anforderungen (DSGVO, ISO 27001, SOC 2)
- Vertrauen von Kunden und Stakeholdern aufbauen
- Kontinuierliche Verbesserung der Informationssicherheit

### 1.2 Geltungsbereich

**In Scope:**
- StackVertex Platform (Frontend, Backend, API)
- Cloud-Infrastruktur (AWS eu-central-1, eu-west-1)
- Kundendaten (Architecture JSON, Deployment States, Logs)
- Mitarbeiterdaten (wenn Team wächst)
- Geschäftsinformationen (Source Code, Dokumentation)

**Out of Scope:**
- Persönliche Geräte von Mitarbeitern (BYOD - separate Policy)
- Drittanbieter-Systeme außerhalb unserer Kontrolle (GitHub, AWS Services)

---

## 2. Information Security Objectives

### 2.1 Strategic Objectives

1. **Verfügbarkeit:** 99.9% Uptime SLA für Production (monatlich gemessen)
2. **Vertraulichkeit:** Keine Datenlecks oder unbefugter Zugriff
3. **Integrität:** Keine Datenmanipulation oder -verlust
4. **Compliance:** 100% Konformität mit DSGVO, ISO 27001, SOC 2
5. **Incident Response:** MTTR (Mean Time to Resolve) <4 Stunden für Critical Issues

### 2.2 Measurable Targets (2026)

| Metric | Target | Current Status | Review Frequency |
|--------|--------|----------------|------------------|
| Security Incidents | 0 High/Critical | 0 (Baseline) | Monatlich |
| Vulnerability Remediation | <7 Tage (HIGH) | N/A (neu) | Wöchentlich |
| Security Training Completion | 100% Mitarbeiter | N/A (solo) | Jährlich |
| Penetration Test Findings | 0 Critical | Ausstehend | Jährlich |
| Backup Success Rate | 100% | Ausstehend | Täglich |

---

## 3. Information Security Organization

### 3.1 Rollen & Verantwortlichkeiten

#### CISO (Chief Information Security Officer)
- **Inhaber:** Andy Schwarz
- **Verantwortung:**
  - Gesamtverantwortung für ISMS
  - Risikobewertung & -behandlung
  - Security Policy Entwicklung & Enforcement
  - Incident Response Koordination
  - Compliance Audits & Reporting

#### Information Security Committee
- **Zusammensetzung:** CISO + CTO (wenn Rolle besetzt)
- **Frequenz:** Quartalsweise
- **Aufgaben:**
  - ISMS-Review
  - Risk Assessment Updates
  - Policy Updates & Approvals
  - Budget-Entscheidungen für Security-Maßnahmen

#### Entwickler (wenn Team wächst)
- **Verantwortung:**
  - Secure Coding Practices befolgen
  - Code Reviews durchführen
  - Security Findings beheben
  - Security Incidents melden

### 3.2 Segregation of Duties

**Aktuell (Solo):** Alle Rollen bei Andy Schwarz.

**Zukünftig (Team >2 Personen):**
- Entwicklung ≠ Production Deployment (4-Augen-Prinzip)
- Code Review ≠ Code Author
- Security Audit ≠ Implementierung

---

## 4. Asset Management

### 4.1 Information Assets

| Asset Category | Examples | Classification | Owner |
|----------------|----------|----------------|-------|
| **Customer Data** | Architecture JSON, Deployments | CONFIDENTIAL | CISO |
| **Source Code** | Backend, Frontend, IaC | INTERNAL | CISO |
| **Credentials** | AWS Keys, DB Passwords | SECRET | CISO |
| **Business Data** | Customer Contracts, Financials | CONFIDENTIAL | CISO |
| **Public Data** | Marketing Website, Docs | PUBLIC | Marketing |

### 4.2 Classification Levels

#### SECRET (Höchste Vertraulichkeit)
- **Beispiele:** Root Passwords, AWS Access Keys, Encryption Keys
- **Zugriff:** Nur CISO (Secrets Manager)
- **Speicherung:** AWS Secrets Manager (encrypted at rest)
- **Übertragung:** TLS 1.3
- **Retention:** Löschen nach Rotation

#### CONFIDENTIAL (Vertraulich)
- **Beispiele:** Kundendaten, Verträge, Source Code
- **Zugriff:** Authentifizierte User (Role-Based Access Control)
- **Speicherung:** S3 (KMS encrypted), RDS (encrypted)
- **Übertragung:** TLS 1.3
- **Retention:** Siehe Data Retention Policy

#### INTERNAL (Intern)
- **Beispiele:** Technische Dokumentation, Policies
- **Zugriff:** Alle Mitarbeiter
- **Speicherung:** GitHub (private repo)
- **Übertragung:** HTTPS
- **Retention:** Unbegrenzt

#### PUBLIC (Öffentlich)
- **Beispiele:** Marketing Website, Blog Posts
- **Zugriff:** Öffentlich
- **Speicherung:** S3 (öffentlich), CloudFront
- **Übertragung:** HTTPS
- **Retention:** Unbegrenzt

---

## 5. Access Control

### 5.1 Access Control Policy

**Principle of Least Privilege:** Jeder User erhält nur die minimal notwendigen Berechtigungen.

#### Authentication
- **Multi-Factor Authentication (MFA):** Mandatory für alle Production-Zugriffe
  - AWS Console: MFA required
  - GitHub: 2FA required
  - Admin-Accounts: Hardware Token (YubiKey empfohlen)

#### Authorization
- **Role-Based Access Control (RBAC):**
  - Admin: Full access (CISO only)
  - Developer: Code + Dev/Staging deployment
  - ReadOnly: Logs + Monitoring (zukünftig für Support)

#### Password Policy
- **Mindestlänge:** 16 Zeichen
- **Komplexität:** Groß-/Kleinbuchstaben + Zahlen + Sonderzeichen
- **Rotation:** Alle 90 Tage (AWS, kritische Systeme)
- **Wiederverwendung:** Letzte 5 Passwörter gesperrt
- **Storage:** Password Manager (1Password, Bitwarden) mandatory

### 5.2 Access Review

**Frequenz:** Quartalsweise (oder bei Mitarbeiterwechsel)

**Prozess:**
1. Liste aller Accounts & Berechtigungen exportieren (AWS IAM, GitHub, etc.)
2. Mit aktuellen Rollen abgleichen
3. Überschüssige Berechtigungen entfernen
4. Inaktive Accounts deaktivieren (>90 Tage keine Nutzung)
5. Review dokumentieren (Datum, Reviewer, Findings)

---

## 6. Risk Management

### 6.1 Risk Assessment Process

**Frequenz:** Jährlich (oder bei signifikanten Änderungen)

**Methodik:**
1. **Asset Identification:** Alle kritischen Assets identifizieren
2. **Threat Identification:** Bedrohungen pro Asset identifizieren
3. **Vulnerability Assessment:** Schwachstellen identifizieren
4. **Impact Analysis:** Schaden bei Eintritt bewerten (1-5 Skala)
5. **Likelihood Analysis:** Eintrittswahrscheinlichkeit bewerten (1-5 Skala)
6. **Risk Scoring:** Risk = Impact × Likelihood
7. **Risk Treatment:** Accept, Mitigate, Transfer, Avoid

**Risk Matrix:**
```
Likelihood
5 │  5   10   15   20   25
4 │  4    8   12   16   20
3 │  3    6    9   12   15
2 │  2    4    6    8   10
1 │  1    2    3    4    5
  └─────────────────────────
    1    2    3    4    5
         Impact
```

**Risk Levels:**
- 1-5: LOW (Accept)
- 6-10: MEDIUM (Monitor)
- 11-15: HIGH (Mitigate within 30 days)
- 16-25: CRITICAL (Mitigate immediately)

### 6.2 Risk Treatment Options

1. **Mitigate:** Technische/organisatorische Maßnahmen (z.B. WAF, MFA)
2. **Transfer:** Versicherung, Drittanbieter (z.B. AWS Shared Responsibility)
3. **Avoid:** Funktion nicht implementieren
4. **Accept:** Risiko akzeptieren (nur LOW/MEDIUM mit Begründung)

**Risk Register:** Siehe `RISK_ASSESSMENT.md`

---

## 7. Incident Management

### 7.1 Security Incident Definition

**Incident:** Ereignis mit negativem Einfluss auf Vertraulichkeit, Integrität oder Verfügbarkeit.

**Severity Levels:**

#### P1 - CRITICAL
- **Beispiele:** Data Breach, RCE, Production Down >1h
- **Response Time:** Sofort (<15min)
- **Eskalation:** CISO + Management
- **Kommunikation:** Kunden informieren (binnen 24h)

#### P2 - HIGH
- **Beispiele:** Auth Bypass, Partial Outage, SQLi
- **Response Time:** <1 Stunde
- **Eskalation:** CISO
- **Kommunikation:** Intern

#### P3 - MEDIUM
- **Beispiele:** Non-Critical Vulnerability, Performance Issues
- **Response Time:** <4 Stunden
- **Eskalation:** On-Duty Engineer
- **Kommunikation:** Intern

#### P4 - LOW
- **Beispiele:** Cosmetic Bugs, Minor Config Issues
- **Response Time:** Best Effort
- **Eskalation:** Keine
- **Kommunikation:** Ticket System

### 7.2 Incident Response Process

**Siehe:** `INCIDENT_RESPONSE_PLAN.md` (detaillierter Prozess)

**High-Level Steps:**
1. **Detection:** Monitoring, Alerts, User Reports
2. **Triage:** Severity Assessment
3. **Containment:** Threat isolieren (z.B. Server abschalten, Credentials rotieren)
4. **Eradication:** Root Cause beheben
5. **Recovery:** Systeme wiederherstellen
6. **Post-Mortem:** Lessons Learned dokumentieren

---

## 8. Business Continuity & Disaster Recovery

### 8.1 Recovery Objectives

| System | RTO (Recovery Time) | RPO (Recovery Point) | Priority |
|--------|---------------------|----------------------|----------|
| Production API | 1 Stunde | 15 Minuten | P1 |
| Production Database | 1 Stunde | 15 Minuten (PITR) | P1 |
| Staging | 4 Stunden | 1 Stunde | P2 |
| Dev | 24 Stunden | 24 Stunden | P3 |

### 8.2 Backup Strategy

**Automated Backups:**
- **Daily:** Aurora Snapshots (30d retention)
- **Weekly:** Full System Backup (90d retention)
- **Monthly:** Long-term Archive (1y retention)
- **Cross-Region:** DR Backups in eu-west-1

**Backup Testing:** Monatlich (Restore-Test in Staging)

**Siehe:** `BUSINESS_CONTINUITY_PLAN.md`

---

## 9. Compliance & Audit

### 9.1 Compliance Requirements

**Gesetzliche Anforderungen:**
- ✅ DSGVO (EU GDPR)
- ✅ ISO 27001:2022
- ✅ SOC 2 Type II (in Vorbereitung)

**Vertragliche Anforderungen:**
- Enterprise-Kunden: Security Questionnaires (SOC 2 Report)
- AWS: Shared Responsibility Model

### 9.2 Internal Audit Schedule

| Audit Type | Frequency | Owner | Output |
|------------|-----------|-------|--------|
| Access Review | Quartalsweise | CISO | Access Report |
| Vulnerability Scan | Wöchentlich | Automated | Security Scan Report |
| Risk Assessment | Jährlich | CISO | Risk Register Update |
| ISMS Review | Jährlich | CISO | Management Review Report |
| Penetration Test | Jährlich | External | Pentest Report |

### 9.3 External Audit

**ISO 27001 Certification:**
- **Stage 1 Audit:** Documentation Review (Remote)
- **Stage 2 Audit:** On-Site / Remote Implementation Review
- **Surveillance Audits:** Jährlich (nach Zertifizierung)
- **Re-Certification:** Alle 3 Jahre

**SOC 2 Type II:**
- **Readiness Assessment:** Intern (vor Audit)
- **Type II Audit:** 12 Monate Operating Effectiveness Period
- **Report Delivery:** Nach Audit (für Kunden)

---

## 10. Security Awareness & Training

### 10.1 Training Requirements

**Onboarding Training (für neue Mitarbeiter):**
- ISMS Policy Overview
- Secure Coding Practices
- Incident Reporting
- DSGVO Basics
- Phishing Awareness

**Annual Refresher Training:**
- Security Updates (neue Threats)
- Policy Changes
- Incident Case Studies

**Specialized Training (role-based):**
- Developers: OWASP Top 10, Secure SDLC
- CISO: Advanced Threat Detection, Forensics

### 10.2 Phishing Simulation

**Frequenz:** Quartalsweise

**Prozess:**
1. Simulated Phishing Email senden
2. Click-Rate messen
3. Reporting-Rate messen (wer meldet Phishing?)
4. Training für "Clicker" (wer draufgeklickt hat)

---

## 11. Supplier & Third-Party Management

### 11.1 Supplier Security Assessment

**Vor Engagement:**
1. Security Questionnaire senden
2. Certifications prüfen (ISO 27001, SOC 2)
3. Data Processing Agreement (DPA) unterschreiben
4. Risk Assessment durchführen

**Critical Suppliers:**
- **AWS:** SOC 2, ISO 27001, PCI DSS certified
- **GitHub:** SOC 2, ISO 27001 certified
- **Stripe:** PCI DSS Level 1 certified

### 11.2 Data Processing Agreements (DPA)

**Required for:**
- Cloud Providers (AWS)
- SaaS Tools with Customer Data Access (Sentry, Analytics)
- Payment Processors (Stripe)

**Template:** Siehe `DPA_TEMPLATE.md`

---

## 12. Continuous Improvement

### 12.1 Management Review

**Frequenz:** Jährlich (oder nach Major Incidents)

**Agenda:**
1. ISMS Performance Review (Metrics)
2. Risk Assessment Updates
3. Audit Findings & Corrective Actions
4. Policy Updates
5. Budget & Resource Planning

**Output:** Management Review Report (dokumentiert Entscheidungen)

### 12.2 Corrective Actions

**Quellen:**
- Internal Audits
- External Audits (ISO, SOC 2)
- Security Incidents
- Vulnerability Scans

**Tracking:**
- Jira/GitHub Issues (Label: "security")
- SLA: HIGH within 30 days, CRITICAL immediately

---

## 13. Policy Review & Approval

### 13.1 Policy Lifecycle

**Creation:** CISO drafts policy  
**Review:** Management Review (bei Team >1 Person)  
**Approval:** CISO (aktuell), CEO (zukünftig)  
**Publication:** Intern (GitHub Repo), Extern (auf Anfrage für Kunden)  
**Review Frequency:** Jährlich  
**Version Control:** Git (jede Änderung mit Commit Message)

### 13.2 Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-05-15 | Andy Schwarz | Initial Policy Creation |

---

## 14. References

**ISO/IEC 27001:2022 Clauses:**
- Clause 4: Context of the Organization
- Clause 5: Leadership
- Clause 6: Planning (Risk Assessment)
- Clause 7: Support (Resources, Training)
- Clause 8: Operation (Incident Management, Change Management)
- Clause 9: Performance Evaluation (Internal Audit, Management Review)
- Clause 10: Improvement (Corrective Actions)

**Related Documents:**
- `RISK_ASSESSMENT.md` - Risk Register & Treatment Plan
- `ACCESS_CONTROL_POLICY.md` - Detailed Access Control Rules
- `INCIDENT_RESPONSE_PLAN.md` - Incident Handling Procedures
- `BUSINESS_CONTINUITY_PLAN.md` - DR & BCP Procedures
- `DPA_TEMPLATE.md` - Data Processing Agreement Template

---

## 15. Approval

**Approved by:**  
Name: Andy Schwarz  
Title: CEO & CISO  
Date: 2026-05-15  
Signature: _________________

**Next Review Date:** 2027-05-15
