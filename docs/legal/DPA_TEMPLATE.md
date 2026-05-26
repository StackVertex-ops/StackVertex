# Data Processing Agreement (DPA)

## DSGVO Art. 28 - Auftragsverarbeitung

**Template Version:** 1.0  
**Effective Date:** 2026-05-15  
**Last Updated:** 2026-05-15  
**Owner:** Andy Schwarz (CISO & DPO)  
**Classification:** Public (Template)

---

> **HINWEIS:** Dies ist ein Template. Bei Vertragsabschluss müssen die markierten Felder [{PLACEHOLDER}] ausgefüllt werden.

---

## DATA PROCESSING AGREEMENT

**Zwischen**

**[KUNDE NAME]**  
[Kunde Adresse]  
[Kunde Land]  
(nachfolgend "**Verantwortlicher**" oder "**Kunde**")

**und**

**StackVertex GmbH** (oder Einzelunternehmen Andy Schwarz)  
[Adresse]  
Deutschland  
E-Mail: legal@stackvertex.io  
(nachfolgend "**Auftragsverarbeiter**" oder "**StackVertex**")

---

## Präambel

Dieser Auftragsverarbeitungsvertrag (Data Processing Agreement, "**DPA**") regelt die Verarbeitung personenbezogener Daten durch StackVertex im Auftrag des Kunden gemäß Art. 28 der Datenschutz-Grundverordnung (DSGVO).

Dieser DPA ist Bestandteil des Hauptvertrags zwischen den Parteien (nachfolgend "**Hauptvertrag**"):
- Vertrag: [{VERTRAG NAME/NUMMER}]
- Datum: [{VERTRAGSDATUM}]
- Gegenstand: Nutzung der StackVertex Platform für Cloud-Infrastruktur-Management

---

## 1. Definitionen

**1.1** Begriffe wie "personenbezogene Daten", "Verarbeitung", "Verantwortlicher", "Auftragsverarbeiter" und "betroffene Person" haben die Bedeutung gemäß Art. 4 DSGVO.

**1.2** "**Unterkauftragsverarbeiter**" bezeichnet jeden von StackVertex beauftragten Dritten, der personenbezogene Daten im Auftrag des Kunden verarbeitet.

**1.3** "**StackVertex Platform**" bezeichnet die SaaS-Plattform zur Verwaltung von Cloud-Infrastruktur, gehostet unter app.stackvertex.io.

---

## 2. Gegenstand und Dauer der Verarbeitung

**2.1 Gegenstand**

StackVertex verarbeitet personenbezogene Daten im Auftrag des Kunden ausschließlich zum Zweck der Bereitstellung der StackVertex Platform gemäß Hauptvertrag.

**2.2 Dauer**

Dieser DPA tritt mit Wirksamkeit des Hauptvertrags in Kraft und endet mit Beendigung des Hauptvertrags oder auf Anforderung des Kunden.

**2.3 Art der Daten**

StackVertex verarbeitet folgende Kategorien personenbezogener Daten:

- **Benutzerdaten:**
  - E-Mail-Adresse (für Account-Erstellung)
  - Name (optional, für Profilinformationen)
  - Passwort-Hash (verschlüsselt, nicht lesbar)
  - IP-Adresse (für Sicherheitsprotokolle, max. 90 Tage)
  - Session-Tokens (temporär, für Authentifizierung)

- **Nutzungsdaten:**
  - Zeitstempel von API-Anfragen
  - Audit-Logs (wer hat was wann geändert)
  - Fehlerprotokolle (für technischen Support)

- **Inhaltsdaten (vom Kunden hochgeladen):**
  - JSON-Architekturen (können Kommentare, Tags mit Namen enthalten)
  - Deployment-Historie
  - Terraform-States (können Cloud-Provider-Credentials enthalten)

**2.4 Kategorien betroffener Personen**

- Mitarbeiter des Kunden (Administratoren, Entwickler)
- Kunden des Kunden (wenn deren Daten in Architekturen referenziert werden)

**2.5 Zweck der Verarbeitung**

- Bereitstellung der StackVertex Platform (SaaS)
- Authentifizierung und Autorisierung
- Technischer Support
- Sicherheitsüberwachung (Incident Detection)
- Abrechnung und Rechnungsstellung

---

## 3. Weisungsgebundenheit

**3.1** StackVertex verarbeitet personenbezogene Daten ausschließlich auf dokumentierte Weisung des Kunden. Die Weisung erfolgt durch:
- Diesen DPA und den Hauptvertrag
- Nutzung der StackVertex Platform durch den Kunden
- Schriftliche Anweisungen per E-Mail an support@stackvertex.io

**3.2** StackVertex informiert den Kunden unverzüglich, wenn eine Weisung nach Auffassung von StackVertex gegen die DSGVO oder andere Datenschutzvorschriften verstößt.

**3.3** Weisungen, die über den Hauptvertrag und diesen DPA hinausgehen, bedürfen einer gesonderten schriftlichen Vereinbarung und können zusätzliche Kosten verursachen.

---

## 4. Vertraulichkeit

**4.1** StackVertex stellt sicher, dass alle Personen, die Zugang zu personenbezogenen Daten haben, zur Vertraulichkeit verpflichtet sind.

**4.2** Mitarbeiter von StackVertex unterzeichnen Vertraulichkeitsvereinbarungen (NDAs) vor Zugriff auf Kundendaten.

**4.3** Die Verpflichtung zur Vertraulichkeit besteht auch nach Beendigung dieses DPA fort.

---

## 5. Technische und organisatorische Maßnahmen (TOM)

**5.1** StackVertex trifft technische und organisatorische Maßnahmen gemäß Art. 32 DSGVO, um ein dem Risiko angemessenes Schutzniveau zu gewährleisten.

**5.2** Die aktuellen TOMs sind in **Anhang A** dieses DPA aufgeführt.

**5.3** StackVertex behält sich das Recht vor, die TOMs anzupassen, solange das Schutzniveau nicht unterschritten wird. Wesentliche Änderungen werden dem Kunden vorab mitgeteilt.

---

## 6. Unterauftragsverarbeiter

**6.1 Genehmigung**

Der Kunde erteilt StackVertex hiermit die generelle Genehmigung, Unterauftragsverarbeiter einzusetzen. Die aktuelle Liste ist in **Anhang B** aufgeführt.

**6.2 Informationspflicht**

StackVertex informiert den Kunden mindestens 30 Tage vor Beauftragung eines neuen oder Austausch eines bestehenden Unterauftragsverarbeiters per E-Mail.

**6.3 Widerspruchsrecht**

Der Kunde kann innerhalb von 14 Tagen nach Benachrichtigung Widerspruch erheben, wenn berechtigte datenschutzrechtliche Gründe vorliegen. In diesem Fall:
- StackVertex sucht nach einer zumutbaren Alternative, oder
- Der Kunde kann den Hauptvertrag außerordentlich kündigen.

**6.4 Vertragliche Bindung**

StackVertex verpflichtet Unterauftragsverarbeiter vertraglich zu denselben Datenschutzpflichten wie in diesem DPA.

**6.5 Haftung**

StackVertex haftet gegenüber dem Kunden für die Einhaltung der Datenschutzpflichten durch Unterauftragsverarbeiter.

---

## 7. Rechte betroffener Personen

**7.1 Unterstützung**

StackVertex unterstützt den Kunden bei der Erfüllung von Anfragen betroffener Personen (Art. 15-22 DSGVO):
- Auskunft (Art. 15)
- Berichtigung (Art. 16)
- Löschung (Art. 17)
- Einschränkung (Art. 18)
- Datenübertragbarkeit (Art. 20)
- Widerspruch (Art. 21)

**7.2 Bereitstellung von Daten**

StackVertex stellt dem Kunden über die StackVertex Platform Tools zur Verfügung:
- **Datenexport:** `/api/v1/dsgvo/data-export` (JSON, CSV, PDF)
- **Datenlöschung:** `/api/v1/dsgvo/data-deletion`
- **Datenberichtigung:** Über UI oder API

**7.3 Bearbeitungszeit**

StackVertex bearbeitet Anfragen innerhalb von 5 Werktagen nach Erhalt der Weisung des Kunden.

**7.4 Zusätzliche Kosten**

Anfragen, die über die im Hauptvertrag vereinbarten Leistungen hinausgehen, können zusätzliche Kosten verursachen (Time & Materials, €100/Stunde).

---

## 8. Datenschutz-Folgenabschätzung und vorherige Konsultation

**8.1** StackVertex unterstützt den Kunden bei der Durchführung einer Datenschutz-Folgenabschätzung (Art. 35 DSGVO), sofern erforderlich.

**8.2** StackVertex stellt dem Kunden auf Anfrage Informationen zur Verfügung über:
- Art der verarbeiteten Daten
- Technische und organisatorische Maßnahmen
- Risiken für betroffene Personen
- Sicherheitsmaßnahmen

**8.3** Die Unterstützung erfolgt im Rahmen der vertraglichen Leistungen. Umfangreiche Unterstützung kann zusätzliche Kosten verursachen.

---

## 9. Datensicherheit und Meldung von Verletzungen

**9.1 Sicherheitsmaßnahmen**

StackVertex implementiert angemessene technische und organisatorische Maßnahmen (siehe Anhang A), einschließlich:
- Verschlüsselung im Ruhezustand (AES-256)
- Verschlüsselung bei Übertragung (TLS 1.3)
- Multi-Faktor-Authentifizierung (MFA)
- Regelmäßige Sicherheitsaudits (wöchentlich automatisiert)
- Web Application Firewall (WAF)

**9.2 Meldung von Datenschutzverletzungen**

StackVertex meldet dem Kunden Verletzungen des Schutzes personenbezogener Daten unverzüglich, spätestens jedoch innerhalb von **48 Stunden** nach Kenntniserlangung.

**9.3 Informationen bei Datenschutzverletzungen**

Die Meldung enthält mindestens:
- Art der Verletzung
- Betroffene Datenkategorien und Anzahl betroffener Personen
- Wahrscheinliche Folgen
- Ergriffene oder vorgeschlagene Maßnahmen

**9.4 Unterstützung bei Meldepflichten**

StackVertex unterstützt den Kunden bei der Meldung an die Aufsichtsbehörde (Art. 33 DSGVO) und Benachrichtigung betroffener Personen (Art. 34 DSGVO).

---

## 10. Löschung und Rückgabe von Daten

**10.1 Bei Vertragsende**

Nach Beendigung des Hauptvertrags löscht oder gibt StackVertex nach Wahl des Kunden alle personenbezogenen Daten zurück und löscht vorhandene Kopien, sofern nicht:
- Eine gesetzliche Aufbewahrungspflicht besteht (z.B. Rechnungsdaten: 10 Jahre)
- Die Daten anonymisiert wurden (keine personenbezogenen Daten mehr)

**10.2 Löschfrist**

Die Löschung erfolgt innerhalb von **30 Tagen** nach Vertragsende.

**10.3 Bestätigung**

StackVertex bestätigt dem Kunden schriftlich die vollständige Löschung oder Rückgabe.

**10.4 Ausnahmen**

Daten, die zur Erfüllung gesetzlicher Aufbewahrungspflichten erforderlich sind, werden gesondert gespeichert und nur für diesen Zweck verwendet.

---

## 11. Prüfungsrechte

**11.1 Audits**

Der Kunde hat das Recht, die Einhaltung dieses DPA durch StackVertex zu überprüfen, einschließlich Inspektionen vor Ort.

**11.2 Informationsbereitstellung**

StackVertex stellt dem Kunden auf Anfrage folgende Nachweise zur Verfügung:
- Aktuelle TOMs (Anhang A)
- Zertifizierungen (ISO 27001, SOC 2)
- Ergebnisse externer Audits (nach Unterzeichnung NDA)
- Liste der Unterauftragsverarbeiter (Anhang B)

**11.3 Vor-Ort-Inspektionen**

Vor-Ort-Inspektionen erfordern:
- Schriftliche Anfrage mindestens 30 Tage im Voraus
- Terminvereinbarung (während Geschäftszeiten)
- Unterzeichnung NDA
- Koordination mit AWS (für physischen Zugang zu Datacentern)

**11.4 Kosten**

- Bereitstellung von Dokumenten: Kostenfrei (1x jährlich)
- Vor-Ort-Inspektion: Time & Materials (€150/Stunde + Reisekosten)
- Häufigkeit: Max. 1x jährlich (außer bei begründetem Verdacht)

---

## 12. Haftung und Schadensersatz

**12.1 Haftung gegenüber betroffenen Personen**

Gemäß Art. 82 DSGVO haftet StackVertex gegenüber betroffenen Personen für Schäden aus DSGVO-Verstößen, soweit StackVertex seine Pflichten nicht eingehalten hat.

**12.2 Haftung gegenüber Kunde**

Die Haftung von StackVertex gegenüber dem Kunden ist auf den im Hauptvertrag vereinbarten Haftungsumfang beschränkt.

**12.3 Freistellung**

StackVertex stellt den Kunden von Ansprüchen betroffener Personen frei, soweit die Ansprüche auf einer Pflichtverletzung durch StackVertex beruhen.

---

## 13. Datenübermittlung in Drittländer

**13.1 Standort der Datenverarbeitung**

StackVertex verarbeitet personenbezogene Daten ausschließlich in der Europäischen Union (EU):
- **Primärer Standort:** Deutschland (Frankfurt, AWS eu-central-1)
- **Disaster Recovery:** Irland (Dublin, AWS eu-west-1)

**13.2 Drittlandsübermittlung durch Unterauftragsverarbeiter**

Einige Unterauftragsverarbeiter (siehe Anhang B) können Zugriff auf Daten haben (z.B. Support, Monitoring). Für diese gelten:
- **Standard-Vertragsklauseln (SCCs)** gemäß Art. 46 DSGVO
- **Angemessenheitsbeschluss** (z.B. Schweiz, UK)
- **Zertifizierung** (z.B. EU-US Data Privacy Framework, wenn anwendbar)

**13.3 Widerspruchsrecht**

Der Kunde kann einer Datenübermittlung in ein Drittland widersprechen (siehe Abschnitt 6.3).

---

## 14. Änderungen des DPA

**14.1** StackVertex kann diesen DPA ändern, um:
- Rechtliche Anforderungen zu erfüllen (DSGVO-Änderungen, neue Gesetze)
- Technische oder organisatorische Verbesserungen umzusetzen
- Klarstellungen vorzunehmen

**14.2** Wesentliche Änderungen werden dem Kunden mindestens 30 Tage vor Inkrafttreten per E-Mail mitgeteilt.

**14.3** Wenn der Kunde mit den Änderungen nicht einverstanden ist, kann er den Hauptvertrag außerordentlich kündigen.

---

## 15. Anwendbares Recht und Gerichtsstand

**15.1 Anwendbares Recht**

Für diesen DPA gilt das Recht der Bundesrepublik Deutschland unter Ausschluss des UN-Kaufrechts.

**15.2 Gerichtsstand**

Ausschließlicher Gerichtsstand ist [{GERICHTSSTAND}], sofern gesetzlich zulässig.

---

## 16. Schlussbestimmungen

**16.1 Vorrang**

Im Falle von Widersprüchen zwischen diesem DPA und dem Hauptvertrag hat dieser DPA Vorrang für alle datenschutzrechtlichen Fragen.

**16.2 Salvatorische Klausel**

Sollten einzelne Bestimmungen dieses DPA unwirksam sein, bleibt die Wirksamkeit der übrigen Bestimmungen unberührt.

**16.3 Schriftform**

Änderungen und Ergänzungen dieses DPA bedürfen der Schriftform (oder qualifizierter elektronischer Signatur).

---

## Unterschriften

**Für den Verantwortlichen (Kunde):**

Name: [{KUNDE NAME}]  
Position: [{KUNDE POSITION}]  
Datum: [{DATUM}]  
Unterschrift: _________________

**Für den Auftragsverarbeiter (StackVertex):**

Name: Andy Schwarz  
Position: CEO & Data Protection Officer  
Datum: [{DATUM}]  
Unterschrift: _________________

---

## ANHANG A: Technische und organisatorische Maßnahmen (TOMs)

### 1. Zutrittskontrolle (Physischer Zugang)

**Maßnahmen:**
- StackVertex betreibt keine eigenen Rechenzentren (100% Cloud-basiert)
- Physischer Zugang wird von AWS kontrolliert (siehe AWS SOC 2 Report)
- AWS-Rechenzentren:
  - Biometrische Zugangskontrollen
  - 24/7 Videoüberwachung
  - Sicherheitspersonal
  - Zutrittsprotokolle

**Verantwortung:** AWS (Shared Responsibility Model)

### 2. Zugangskontrolle (Systemzugang)

**Maßnahmen:**
- **Multi-Faktor-Authentifizierung (MFA):** Mandatory für alle Production-Zugriffe
- **Single Sign-On (SSO):** Geplant für Enterprise-Kunden (Q4 2026)
- **Passwort-Policy:**
  - Mindestlänge: 16 Zeichen
  - Komplexität: Groß-/Kleinbuchstaben + Zahlen + Sonderzeichen
  - Ablauf: 90 Tage (für privilegierte Accounts)
- **Session-Management:** JWT-Tokens mit 24h Ablauf
- **Inaktivitäts-Timeout:** 30 Minuten (automatisches Logout)

### 3. Zugriffskontrolle (Berechtigungen)

**Maßnahmen:**
- **Principle of Least Privilege:** Minimale notwendige Berechtigungen
- **Role-Based Access Control (RBAC):**
  - Admin: Full access (Owner only)
  - Developer: Read/Write (eigene Architekturen)
  - ReadOnly: View-only (geplant für Auditors)
- **AWS IAM Policies:** Granulare Berechtigungen per Ressource
- **Quarterly Access Review:** Überprüfung aller Berechtigungen
- **Automated Deprovisioning:** Accounts werden nach 90 Tagen Inaktivität deaktiviert

### 4. Trennungskontrolle (Mandantenfähigkeit)

**Maßnahmen:**
- **Logische Trennung:** Jeder Kunde hat separate Namespace (user_id Filterung)
- **Datenbank-Isolation:** Row-Level Security (RLS) in PostgreSQL
- **S3-Bucket-Isolation:** Separater Prefix pro Kunde (`users/{user_id}/`)
- **Keine Shared Credentials:** Jeder Kunde verwaltet eigene Cloud-Provider-Credentials
- **Audit Logs:** Alle Zugriffe protokolliert mit user_id

### 5. Pseudonymisierung

**Maßnahmen:**
- **User IDs:** UUIDs statt fortlaufender Nummern
- **IP-Adressen:** Gehashed in Audit Logs (SHA-256)
- **Anonymisierung bei Löschung:** User-Daten werden durch Platzhalter ersetzt (Audit Logs bleiben)
- **Kein Tracking:** Keine Cookies, keine Third-Party-Analytics (opt-in für Kunden)

### 6. Verschlüsselung

#### 6.1 Verschlüsselung im Ruhezustand (at rest)

**Database (Aurora PostgreSQL):**
- Algorithmus: AES-256
- Key Management: AWS KMS (Customer Managed Key)
- Key Rotation: Automatisch jährlich

**S3 Buckets:**
- Algorithmus: AES-256
- Methode: SSE-KMS (Server-Side Encryption mit KMS)
- Versioning: Enabled (90 Tage Retention)

**Secrets Manager:**
- Algorithmus: AES-256
- Key Management: AWS KMS
- Access: IAM Role-based

**Backups:**
- Automatisch verschlüsselt (AES-256)
- Cross-Region Replication: Verschlüsselt

#### 6.2 Verschlüsselung bei Übertragung (in transit)

**HTTPS/TLS:**
- Protokoll: TLS 1.3 (TLS 1.2 als Fallback)
- Zertifikate: Let's Encrypt (automatische Erneuerung)
- HSTS: Enabled (Strict-Transport-Security Header)
- Certificate Pinning: Geplant für Mobile App (zukünftig)

**Database Connections:**
- TLS 1.2+ (SSL erzwungen)
- Certificate Verification: Enabled

**API Gateway:**
- TLS 1.3
- Custom Domain mit ACM Certificate

### 7. Verfügbarkeitskontrolle

**Maßnahmen:**
- **Backup-Strategie:**
  - Automated Backups: Daily (30 Tage Retention)
  - Manual Snapshots: Vor major changes
  - Cross-Region Backups: Daily zu DR-Region (eu-west-1)
  - Point-in-Time Recovery (PITR): 5 Minuten RPO
- **High Availability:**
  - Multi-AZ Deployment (Production: 3 Availability Zones)
  - Auto-Scaling: Lambda (1-1000 concurrent), Aurora Serverless (2-16 ACU)
  - Load Balancing: Application Load Balancer + CloudFront
- **Disaster Recovery:**
  - RTO: 1 Stunde (Recovery Time Objective)
  - RPO: 15 Minuten (Recovery Point Objective)
  - DR-Region: eu-west-1 (Ireland)
  - DR-Drill: Halbjährlich
- **Monitoring:**
  - CloudWatch: Metrics, Logs, Alarms
  - Sentry: Error Tracking
  - UptimeRobot: External Uptime Monitoring (99.9% SLA)

### 8. Eingabekontrolle (Audit Logs)

**Maßnahmen:**
- **Audit Logging:**
  - Wer hat was wann geändert (User, Action, Timestamp, IP)
  - Retention: 90 Tage (in Database), 1 Jahr (in CloudWatch Logs)
  - Unveränderbarkeit: CloudWatch Logs (append-only)
- **CloudTrail:**
  - Alle AWS API Calls protokolliert
  - Multi-Region Trail (Production)
  - Log File Integrity Validation: Enabled
  - Retention: 90 Tage (CloudWatch), 1 Jahr (S3)
- **Application Logs:**
  - Alle API Requests (ohne Passwörter, Tokens)
  - Fehler und Exceptions (mit Stack Trace)
  - Performance Metrics (Latency, Throughput)

### 9. Auftragskontrolle

**Maßnahmen:**
- **Vertragsmanagement:** Alle Auftragsverarbeiter haben schriftlichen Vertrag (DPA)
- **Unterauftragsverarbeiter-Liste:** Siehe Anhang B
- **Vendor Risk Assessment:** Jährliche Überprüfung aller Vendors
- **Data Processing Agreements (DPAs):**
  - AWS: Standard DPA (https://aws.amazon.com/service-terms/)
  - GitHub: Standard DPA
  - Stripe: Standard DPA (PCI DSS Level 1 certified)

### 10. Datenschutz-Management

**Maßnahmen:**
- **Data Protection Officer (DPO):** Andy Schwarz (dpo@stackvertex.io)
- **ISMS Policy:** ISO 27001 konform
- **Security Awareness Training:** Jährlich für alle Mitarbeiter
- **Incident Response Plan:** Dokumentiert, getestet halbjährlich
- **Risk Assessment:** Jährlich, dokumentiert

### 11. Belastbarkeit der Systeme

**Maßnahmen:**
- **WAF (Web Application Firewall):**
  - AWS WAF mit managed rule groups
  - Rate Limiting: 2000 Requests / 5 Minuten / IP
  - Bot Detection: AWS Bot Control (Production)
  - Geo-Blocking: Optional, nur EU + US (Production)
- **DDoS Protection:**
  - AWS Shield Standard (automatisch, kostenfrei)
  - CloudFront Edge Locations (global)
  - Auto-Scaling (elastische Kapazität)
- **Vulnerability Management:**
  - Automated Security Scans: Wöchentlich (Trivy, Safety, OWASP ZAP)
  - Dependency Updates: Dependabot (automatisch)
  - Penetration Testing: Jährlich (geplant Q4 2026)
- **Patch Management:**
  - Serverless (AWS Lambda): Automatisch von AWS
  - Container Images: Weekly rebuild mit latest base images
  - Database (Aurora): Automatische Minor-Version-Updates (Wartungsfenster)

---

## ANHANG B: Liste der Unterauftragsverarbeiter

| Name | Land | Zweck | Datenkategorien | Schutzmechanismus |
|------|------|-------|-----------------|-------------------|
| **Amazon Web Services (AWS)** | USA (Hosting: EU) | Cloud Infrastructure (Hosting, Database, Storage) | Alle vom Kunden hochgeladenen Daten | Standard DPA, ISO 27001, SOC 2, EU Data Residency |
| **GitHub, Inc.** | USA | Source Code Repository, CI/CD | Code, Deployment Logs (keine Kundendaten) | Standard DPA, SOC 2 |
| **Sentry (Functional Software, Inc.)** | USA | Error Tracking & Monitoring | Fehlerprotokolle (können IP, User-ID enthalten) | Standard DPA, Privacy Shield Successor (planned) |
| **Stripe, Inc.** | USA | Payment Processing | Zahlungsdaten (Kreditkarte), Rechnungsinformationen | Standard DPA, PCI DSS Level 1 |
| **Postmark (Wildbit, LLC)** | USA (optional, geplant) | Transactional Email (Passwort-Reset, etc.) | E-Mail-Adressen | Standard DPA, GDPR Compliant |

**Hinweis:** 
- Alle Unterauftragsverarbeiter haben DSGVO-konforme Datenschutzerklärungen und Standard-Vertragsklauseln (SCCs) oder Angemessenheitsbeschlüsse.
- AWS verarbeitet Daten ausschließlich in EU-Regionen (Frankfurt, Dublin).
- Änderungen dieser Liste werden dem Kunden 30 Tage im Voraus mitgeteilt (siehe Abschnitt 6.2).

**Aktualisierungen:**
Diese Liste wird aktualisiert unter: https://stackvertex.io/legal/subprocessors

---

**Ende des DPA Templates**

---

## Anleitung zur Verwendung

### Für StackVertex Team:

1. **Kundengespräch:** Vor Vertragsabschluss DPA mit Kunde besprechen
2. **Anpassung:** Platzhalter [{PLACEHOLDER}] durch kundenspezifische Daten ersetzen
3. **Anhänge:** Anhang A & B aktuell halten (bei Änderungen)
4. **Unterzeichnung:** Beidseitig unterzeichnen (elektronisch oder physisch)
5. **Speicherung:** In CRM hinterlegen (verschlüsselt)
6. **Erneuerung:** Bei Hauptvertragsverlängerung prüfen ob DPA-Update nötig

### Für Kunden:

1. **Review:** DPA von Rechtsabteilung/Datenschutzbeauftragten prüfen lassen
2. **Verhandlung:** Anpassungen besprechen (falls erforderlich)
3. **Unterzeichnung:** Zusammen mit Hauptvertrag
4. **Archivierung:** Mindestens 10 Jahre aufbewahren (gesetzliche Pflicht)

---

**Template Owner:** Andy Schwarz (CISO & DPO)  
**Legal Review:** Empfohlen vor finaler Verwendung  
**Last Updated:** 2026-05-15
