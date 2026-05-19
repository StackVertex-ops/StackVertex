# OverCloud - Business Roadmap & Gründungsplan

> Schritt-für-Schritt Anleitung von Solo-Entwickler bis zur Firmengründung

**Autor:** Andy Schwarz  
**Erstellt:** 2026-05-19  
**Status:** 🚀 In Umsetzung

---

## 📊 Übersicht - Die 4 Phasen

```
Phase 1: MVP Vorbereitung (Jetzt - 2 Wochen)
├── Marke schützen
├── Rechtliches klären
├── Open Source vorbereiten
└── Beta-Seite aufsetzen

Phase 2: Soft Launch (2-8 Wochen)
├── Beta-Tester gewinnen
├── Feedback sammeln
├── Pricing finalisieren
└── Erste Marketing-Aktionen

Phase 3: Public Launch (3-6 Monate)
├── Kleinunternehmer anmelden
├── Erste zahlende Kunden
├── Community aufbauen
└── Feature-Entwicklung

Phase 4: Skalierung (6-12 Monate)
├── UG gründen
├── Steuerberater + Infrastruktur
├── Team erweitern (optional)
└── Investoren-Pitch (optional)
```

---

## 🎯 Phase 1: MVP Vorbereitung (JETZT - 2 Wochen)

**Ziel:** Rechtlich absichern, Marke schützen, Beta vorbereiten  
**Budget:** ~€500  
**Zeitaufwand:** ~20 Stunden

---

### Woche 1: Rechtliches & Marke

#### ☑️ 1.1 Domain sichern

**Warum:** Deine Online-Identität schützen  
**Zeitaufwand:** 30 Minuten  
**Kosten:** ~€15-30/Jahr

**Schritte:**
1. [ ] Domain-Verfügbarkeit prüfen:
   - https://www.namecheap.com
   - https://www.checkdomain.de
   
2. [ ] Folgende Domains checken (Priorität):
   - [ ] `overcloud.io` (hauptsächlich)
   - [ ] `overcloud.de` (Deutschland)
   - [ ] `overcloud.com` (falls frei & günstig)

3. [ ] Domain kaufen bei:
   - **Empfohlen:** Namecheap (günstig, guter Support)
   - **Alternative:** Cloudflare (kostenlos nach 1. Jahr)
   - **DE-Anbieter:** IONOS, Strato

4. [ ] DNS auf Cloudflare umziehen (kostenlos):
   - Nameserver bei Domain-Anbieter ändern
   - Cloudflare Account erstellen: https://dash.cloudflare.com
   - **Vorteil:** Kostenlose SSL-Zertifikate, schnelleres CDN

**Ergebnis:** ✅ Domain gesichert, DNS auf Cloudflare

---

#### ☑️ 1.2 Marke recherchieren & anmelden

**Warum:** "OverCloud" Name schützen vor Nachahmern  
**Zeitaufwand:** 2 Stunden (Recherche) + 1 Stunde (Anmeldung)  
**Kosten:** ~€300

**Schritte:**

1. [ ] **Marken-Recherche (KOSTENLOS):**
   - Gehe zu: https://register.dpma.de/DPMAregister/marke/basis
   - Suche nach: "OverCloud", "Over Cloud", "Overcloud"
   - Check auch: "Cloud", "Infrastructure" (ähnliche Begriffe)
   - **Falls frei:** Weiter zu Schritt 2
   - **Falls blockiert:** Alternative Namen überlegen

2. [ ] **Markenklassen bestimmen:**
   
   Für OverCloud brauchst du:
   - **Klasse 9:** Software, Apps, SaaS
   - **Klasse 42:** IT-Dienstleistungen, Cloud-Services
   
   Optional (später):
   - Klasse 35: Werbung, Marketing (wenn du Agentur-Services anbietest)
   - Klasse 41: Schulungen, Workshops

3. [ ] **Marke anmelden (2 Optionen):**

   **Option A: Selbst anmelden (€300)**
   - Gehe zu: https://www.dpma.de/marken/anmeldung/index.html
   - Wähle: "Online-Anmeldung"
   - Account erstellen
   - Formular ausfüllen:
     - Marke: "OverCloud"
     - Typ: Wortmarke (einfacher Text, kein Logo)
     - Klassen: 9, 42
     - Waren/Dienstleistungen beschreiben (siehe unten)
   - Zahlung: €300 (2 Klassen)
   
   **Option B: Mit Anwalt (€800-1.200)**
   - Suche "Markenanwalt" auf: https://www.markenanwalt.de
   - Vorteil: Professionelle Beratung, höhere Erfolgsquote
   - Nachteil: Teurer

4. [ ] **Waren/Dienstleistungen beschreiben (Beispieltext):**

   ```
   Klasse 9:
   Software für Cloud-Infrastruktur-Management; SaaS-Plattformen;
   Computersoftware für Terraform-Code-Generierung; 
   Anwendungssoftware für Infrastructure-as-Code;
   Downloadbare Software für Cloud-Architektur-Design

   Klasse 42:
   Software-as-a-Service (SaaS) für Cloud-Infrastruktur-Verwaltung;
   Bereitstellung von Online-Software für IaC-Generierung;
   Cloud-Computing-Dienste; Technische Beratung im Bereich Cloud-Infrastruktur;
   Hosting von Software-Plattformen
   ```

5. [ ] **Nach Anmeldung:**
   - DPMA prüft (3-6 Monate)
   - Bei Rückfragen: Beantworten (sonst Ablehnung)
   - Nach Genehmigung: 10 Jahre Schutz
   - Verlängerung: Alle 10 Jahre (~€750)

**Ergebnis:** ✅ Marke angemeldet, Schutz in Deutschland

**Hinweis:** EU-Marke (€850) kannst du später machen wenn du international expandierst.

---

#### ☑️ 1.3 Open Source License & Copyright

**Warum:** Code rechtlich schützen  
**Zeitaufwand:** 1 Stunde  
**Kosten:** €0

**Schritte:**

1. [ ] **LICENSE File erstellen (Backend):**

   Erstelle: `/backend/LICENSE`
   
   ```
   GNU AFFERO GENERAL PUBLIC LICENSE
   Version 3, 19 November 2007
   
   Copyright (C) 2026 Andy Schwarz
   
   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU Affero General Public License as published
   by the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.
   
   [... kompletter AGPLv3 Text von https://www.gnu.org/licenses/agpl-3.0.txt]
   ```

   **Warum AGPLv3?**
   - ✅ Andere dürfen nutzen/ändern
   - ✅ ABER: Müssen auch Open Source sein (auch bei SaaS!)
   - ✅ Schützt vor direkten Klonen ohne Beitrag zurück

2. [ ] **LICENSE File erstellen (Frontend):**

   Erstelle: `/frontend/LICENSE`
   
   ```
   MIT License
   
   Copyright (c) 2026 Andy Schwarz
   
   Permission is hereby granted, free of charge, to any person obtaining a copy
   of this software and associated documentation files (the "Software"), to deal
   in the Software without restriction...
   
   [... kompletter MIT Text von https://choosealicense.com/licenses/mit/]
   ```

   **Warum MIT?**
   - ✅ Maximale Freiheit
   - ✅ Zeigt deine Skills (Portfolio)
   - ✅ Community kann beitragen

3. [ ] **Copyright-Notice in Code-Dateien:**

   Füge in JEDE wichtige Python/JS Datei ein (oben):
   
   ```python
   # Copyright (C) 2026 Andy Schwarz
   # This file is part of OverCloud.
   # Licensed under AGPLv3 - see LICENSE file for details.
   ```

4. [ ] **README.md updaten:**

   Füge hinzu:
   ```markdown
   ## License

   - **Backend:** AGPLv3 - see [backend/LICENSE](backend/LICENSE)
   - **Frontend:** MIT - see [frontend/LICENSE](frontend/LICENSE)
   
   ## Copyright
   
   Copyright (C) 2026 Andy Schwarz. All rights reserved.
   ```

5. [ ] **GitHub Repository Settings:**
   - Gehe zu: Settings → General → Features
   - Enable: "Issues", "Discussions"
   - Add topics: `cloud`, `terraform`, `infrastructure-as-code`, `saas`

**Ergebnis:** ✅ Code rechtlich geschützt, Open Source ready

---

### Woche 2: Beta-Vorbereitung & Marketing

#### ☑️ 1.4 Beta-Landing-Page erstellen

**Warum:** Waitlist aufbauen, erste Nutzer gewinnen  
**Zeitaufwand:** 4-8 Stunden  
**Kosten:** €0

**Schritte:**

1. [ ] **Simple Landing Page bauen:**

   Erstelle: `/frontend/src/beta.html`
   
   **Elemente:**
   - Hero Section: "Cloud Infrastructure, Simplified"
   - Problem Statement: "Terraform is complex. OverCloud makes it visual."
   - 3 Key Features (mit Icons)
   - Waitlist Form (Email + "Join Beta" Button)
   - Footer: Copyright, Social Links

2. [ ] **Email-Collection Setup:**

   **Option A: Selbst hosten (empfohlen für Anfang)**
   - DynamoDB Table für Beta-Signups
   - API Endpoint: `POST /api/v1/beta/signup`
   - Speichere: email, signup_date, referrer

   **Option B: Extern (schneller)**
   - https://mailchimp.com (kostenlos bis 500 Subscriber)
   - https://convertkit.com (kostenlos bis 300 Subscriber)
   - Embedded Form auf Landing Page

3. [ ] **Analytics einbauen:**
   - https://plausible.io (DSGVO-konform, €9/Monat)
   - ODER: https://umami.is (selbst hosten, kostenlos)
   - Track: Page Views, Signups, Conversion Rate

4. [ ] **SEO Basics:**
   - [ ] Title: "OverCloud - Visual Cloud Infrastructure Builder"
   - [ ] Meta Description: "Transform requirements into production-ready Terraform code. Visual builder, cost estimation, and deployment in minutes."
   - [ ] Open Graph Tags (für Social Sharing)
   - [ ] Favicon erstellen: https://favicon.io

**Ergebnis:** ✅ Beta-Seite live, Email-Collection funktioniert

---

#### ☑️ 1.5 Rechtliche Pflichtseiten (DSGVO)

**Warum:** Abmahnung vermeiden, DSGVO-konform  
**Zeitaufwand:** 2 Stunden  
**Kosten:** €0 (Generator) oder €100-200 (Anwalt)

**Schritte:**

1. [ ] **Impressum erstellen:**
   
   Generator: https://www.e-recht24.de/impressum-generator.html
   
   **Mindestangaben:**
   ```
   Andy Schwarz (Einzelunternehmer / Kleinunternehmer)
   [Deine Adresse]
   Email: contact@overcloud.io
   
   Umsatzsteuer-ID: [noch keine - erst bei Anmeldung]
   
   Verantwortlich für Inhalte: Andy Schwarz
   ```

2. [ ] **Datenschutzerklärung:**
   
   Generator: https://www.e-recht24.de/dsgvo.html
   
   **Must-Have Punkte:**
   - Welche Daten werden gesammelt? (Email, IP, Cookies)
   - Wo gespeichert? (DynamoDB in AWS Frankfurt/eu-central-1)
   - Wie lange? (Email-Liste: bis Abmeldung, Logs: 90 Tage)
   - Rechte des Nutzers (Auskunft, Löschung, Widerspruch)
   - Cookies? (Plausible ist cookie-less, erwähnen!)

3. [ ] **Cookie-Banner (falls Cookies):**
   
   **WENN du Google Analytics o.ä. nutzt:**
   - https://github.com/orestbida/cookieconsent (Open Source)
   - ODER: https://www.cookiebot.com (€9/Monat)
   
   **Plausible/Umami = kein Banner nötig!** (Cookie-less tracking)

4. [ ] **AGB (Terms of Service) - SPÄTER:**
   
   Brauchst du erst wenn du zahlende Kunden hast.
   Dann: https://a템플릿.de oder Anwalt (€200-500)

**Ergebnis:** ✅ Impressum + Datenschutz live, DSGVO-konform

---

#### ☑️ 1.6 GitHub perfekt aufsetzen

**Warum:** Open Source Community vorbereiten  
**Zeitaufwand:** 2 Stunden  
**Kosten:** €0

**Schritte:**

1. [ ] **README.md perfektionieren:**
   - [ ] Badge hinzufügen: Tests Passing, License, Version
   - [ ] Screenshot/GIF vom UI
   - [ ] Quick Start Guide (5 Minuten Setup)
   - [ ] Link zu Live-Demo (Beta-Seite)

2. [ ] **CONTRIBUTING.md erstellen:**
   ```markdown
   # Contributing to OverCloud
   
   Thanks for your interest! Here's how you can help:
   
   ## Reporting Bugs
   - Use GitHub Issues
   - Include: Steps to reproduce, expected vs actual behavior
   
   ## Pull Requests
   - Fork → Branch → PR
   - Follow code style (Black, Ruff)
   - Add tests for new features
   
   ## Questions?
   - GitHub Discussions
   - Email: andy@overcloud.io
   ```

3. [ ] **CODE_OF_CONDUCT.md:**
   - Template: https://www.contributor-covenant.org
   - Copy & paste (Standard in Open Source)

4. [ ] **Issue Templates:**
   - `.github/ISSUE_TEMPLATE/bug_report.md`
   - `.github/ISSUE_TEMPLATE/feature_request.md`
   - GitHub bietet Auto-Generator an

5. [ ] **GitHub Sponsors aktivieren (optional):**
   - Settings → Features → Sponsorships
   - Falls jemand dich unterstützen will (selten, aber nice)

**Ergebnis:** ✅ GitHub professional, Community-ready

---

#### ☑️ 1.7 Social Media Präsenz

**Warum:** Erste Follower sammeln, Launch vorbereiten  
**Zeitaufwand:** 1 Stunde Setup, dann 10 Min/Tag  
**Kosten:** €0

**Schritte:**

1. [ ] **Twitter/X Account:**
   - Handle: `@overcloud_io` (oder ähnlich)
   - Bio: "Visual Cloud Infrastructure Builder | Open Source | Terraform made simple"
   - Link: overcloud.io
   - **Erste Posts:**
     - "Building OverCloud - a visual way to design cloud infrastructure"
     - Screenshot vom Canvas
     - "Join the beta: [Link]"

2. [ ] **LinkedIn (wichtig für B2B!):**
   - Persönliches Profil updaten: "Founder @ OverCloud"
   - Posts über Entwicklungs-Journey
   - Hashtags: #CloudComputing #DevOps #OpenSource

3. [ ] **GitHub Discussions aktivieren:**
   - Repo Settings → Features → Discussions
   - Erste Kategorie: "Announcements", "Ideas", "Q&A"

4. [ ] **ProductHunt vorbereiten:**
   - Account erstellen: https://www.producthunt.com
   - **NICHT jetzt launchen!** - erst wenn MVP fertig
   - Aber: Profil anlegen, Follower sammeln

**Ergebnis:** ✅ Social Media ready, erste Sichtbarkeit

---

### ✅ Phase 1 Checkpoint

**Hast du alle Punkte?**
- [ ] Domain gesichert (overcloud.io)
- [ ] Marke angemeldet (DPMA)
- [ ] LICENSE Files erstellt (AGPLv3 + MIT)
- [ ] Beta-Landing-Page live
- [ ] Impressum + Datenschutz vorhanden
- [ ] GitHub professional aufgesetzt
- [ ] Social Media Accounts erstellt

**Budget bisher:** ~€500  
**Nächste Phase:** Beta-Tester gewinnen!

---

## 🚀 Phase 2: Soft Launch (2-8 Wochen)

**Ziel:** 10-50 Beta-Tester, Feedback sammeln, MVP stabilisieren  
**Budget:** ~€100-300 (optional: Werbung)  
**Zeitaufwand:** ~40-80 Stunden

---

#### ☑️ 2.1 Beta-Tester Akquise

**Ziel:** 10 aktive Beta-Tester in Woche 1, 50 in Woche 8  
**Zeitaufwand:** 10-20 Stunden  
**Kosten:** €0-200

**Schritte:**

1. [ ] **Persönliches Netzwerk (Woche 1):**
   - [ ] 10 Freunde/Kollegen direkt anschreiben
   - [ ] DevOps/Cloud-Engineers in LinkedIn kontaktieren
   - [ ] "Ich baue OverCloud - magst du testen?" (persönlich!)
   
   **Nachricht-Template:**
   ```
   Hey [Name],
   
   ich baue gerade OverCloud - ein Tool das Terraform-Config aus
   visuellen Diagrammen generiert. Bist du interessiert mal reinzuschauen?
   
   Beta-Link: overcloud.io/beta
   Würde mich mega über Feedback freuen!
   
   Grüße,
   Andy
   ```

2. [ ] **Reddit Posts (Woche 1-2):**
   
   Subreddits:
   - [ ] r/devops (1.2M members)
   - [ ] r/terraform (50k members)
   - [ ] r/selfhosted (450k members)
   - [ ] r/aws (200k members)
   - [ ] r/webdev (1.5M members)
   
   **Post-Template:**
   ```
   Title: "I built OverCloud - visual Terraform generator [Open Source]"
   
   Body:
   Hey r/devops!
   
   I've been frustrated with Terraform's learning curve, so I built
   OverCloud - a visual way to design cloud infrastructure that generates
   production-ready Terraform code.
   
   Features:
   - Drag & Drop AWS components
   - Real-time cost estimation
   - JSON-based architecture (versionable)
   - Open Source (AGPLv3)
   
   Looking for beta testers! What do you think?
   
   Demo: overcloud.io/beta
   GitHub: github.com/andy/overcloud
   ```
   
   **Wichtig:** Keine blanke Werbung, echte Value bieten!

3. [ ] **HackerNews "Show HN" (Woche 2):**
   
   - Timing: Dienstag/Mittwoch, 9-11 Uhr EST (US-Peak)
   - Title: "Show HN: OverCloud – Visual Terraform builder (Open Source)"
   - Text: Kurz & knapp, Problem → Lösung, Link
   - **Tipp:** Aktiv in Comments antworten (erste 2 Stunden kritisch!)

4. [ ] **Dev.to Blog Post (Woche 2-3):**
   
   Title: "Building OverCloud: How I made Terraform visual"
   
   Inhalte:
   - Warum ich es gebaut habe (Problem)
   - Tech Stack (FastAPI, DynamoDB, Vanilla JS)
   - Herausforderungen (JSON → Terraform Mapping)
   - Screenshots
   - "Try the beta" CTA
   
   Tags: #terraform #devops #opensource #aws

5. [ ] **Twitter Launch Thread (Woche 3):**
   
   ```
   🧵 Thread: I spent 3 months building OverCloud - here's why...
   
   1/ Managing cloud infrastructure with Terraform is powerful but complex.
      I wanted something visual. Something that explains itself.
   
   2/ OverCloud lets you design AWS infrastructure visually.
      Drag VPC, EC2, RDS on a canvas → generates Terraform code.
      [Screenshot]
   
   3/ Key features:
      ✅ Visual architecture builder
      ✅ Real-time cost estimation
      ✅ JSON-first (versionable, inspectable)
      ✅ Open Source (AGPLv3)
   
   4/ Looking for beta testers!
      👉 overcloud.io/beta
      
      What features would YOU want? 🤔
   ```

6. [ ] **Influencer Outreach (Woche 4+):**
   
   DevOps YouTuber/Blogger:
   - TechWorld with Nana (YouTube)
   - Fireship (YouTube)
   - ThePrimeagen (Twitch/YouTube)
   - DevOps Blogs (Google "DevOps blog")
   
   **Nachricht:**
   ```
   Hey [Name],
   
   Großer Fan deiner Inhalte! Ich hab OverCloud gebaut - ein Visual
   Builder für Terraform. Denkst du das wäre interessant für deine
   Community?
   
   Falls ja, würde ich mich freuen wenn du es erwähnst/testest!
   
   Demo: overcloud.io
   ```

**Ergebnis:** ✅ 50+ Beta-Signups, 10+ aktive Tester

---

#### ☑️ 2.2 Feedback-Prozess etablieren

**Warum:** Systematisch lernen was funktioniert  
**Zeitaufwand:** 2 Stunden Setup, dann 30 Min/Tag  
**Kosten:** €0

**Schritte:**

1. [ ] **User Interviews (1:1 Calls):**
   - [ ] 5-10 Beta-Testern Zoom-Call anbieten (30 Min)
   - [ ] Fragen vorbereiten:
     - "Was wolltest du als erstes tun?"
     - "Was war verwirrend?"
     - "Welches Feature fehlt dir am meisten?"
     - "Würdest du dafür zahlen? Wenn ja, wie viel?"

2. [ ] **Feedback-Board:**
   - GitHub Discussions: "Feature Requests"
   - ODER: https://canny.io (kostenlos bis 25 Posts/Monat)
   - User können Features upvoten

3. [ ] **Analytics Dashboard:**
   - Welche Features werden genutzt?
   - Wo steigen User aus?
   - Conversion: Signup → First Architecture
   
   Tools:
   - Plausible (Events tracking)
   - Mixpanel (kostenlos bis 100k Events/Monat)

4. [ ] **Weekly Summary:**
   - Jeden Freitag: Top 3 Learnings dokumentieren
   - Datei: `docs/user-feedback/2026-week-XX.md`

**Ergebnis:** ✅ Strukturierter Feedback-Loop, klare Roadmap

---

#### ☑️ 2.3 MVP stabilisieren

**Warum:** Production-ready machen  
**Zeitaufwand:** 20-40 Stunden  
**Kosten:** €0

**Schritte:**

1. [ ] **Bug-Fixing Priorität:**
   - [ ] Alle "Can't use the app" Bugs sofort fixen
   - [ ] "Annoying but workaround exists" → Backlog
   - [ ] "Nice to have" → Ignorieren für jetzt

2. [ ] **Performance Optimierung:**
   - [ ] Lighthouse Score > 90 (alle Seiten)
   - [ ] API Response Time < 200ms (p95)
   - [ ] Terraform Generation < 5s

3. [ ] **Error Handling:**
   - [ ] Alle API Errors mit klaren Messages
   - [ ] Frontend: Loading States überall
   - [ ] Sentry: Error Tracking aktivieren

4. [ ] **Documentation:**
   - [ ] Quick Start Guide (5 Minuten)
   - [ ] FAQ erweitern (aus User-Fragen)
   - [ ] Video-Tutorial (5 Minuten, Loom)

**Ergebnis:** ✅ Stabiles MVP, ready für Paying Customers

---

#### ☑️ 2.4 Pricing finalisieren

**Warum:** Bereit sein für "Shut up and take my money!"  
**Zeitaufwand:** 4-8 Stunden (Research + Kalkulation)  
**Kosten:** €0

**Schritte:**

1. [ ] **Competitor Research:**
   - Pulumi Cloud: Pricing?
   - Terraform Cloud: Pricing?
   - Spacelift: Pricing?
   - env0: Pricing?
   
   → Notiere: Features pro Tier, Preise

2. [ ] **Deine Kosten kalkulieren:**
   
   ```
   Pro User/Monat:
   - AWS (DynamoDB, S3, Lambda): ~€0.50-2
   - Stripe Fees (3%): ~€0.15-1
   - Support-Zeit (1h/10 User): ~€5
   - TOTAL: ~€6-8/User
   
   → Mindestpreis: €15/User/Monat (50% Marge)
   ```

3. [ ] **Pricing Tiers definieren:**
   
   **Mein Vorschlag:**
   
   ```
   FREE (Forever)
   ├── 1 User
   ├── 3 Architectures
   ├── Community Support
   └── MIT License Code-Export
   
   STARTER (€29/Monat) ⭐ MEISTE NEHMEN DAS
   ├── 1 User
   ├── Unlimited Architectures
   ├── Email Support (48h)
   ├── Cost Estimation
   └── Terraform Download
   
   PRO (€99/Monat)
   ├── 5 Users
   ├── Everything in Starter
   ├── Priority Support (24h)
   ├── AWS Deployment (Beta)
   └── Team Collaboration
   
   ENTERPRISE (Custom)
   ├── Unlimited Users
   ├── Everything in Pro
   ├── SLA 99.9%
   ├── Dedicated Support
   ├── On-Premise Option
   └── Custom Integrations
   ```

4. [ ] **Value-Based Pricing Check:**
   - User spart 10h/Monat → €500-1000 Wert
   - Dein Preis €29-99 → 3-10% des Werts
   - ✅ Fair!

5. [ ] **Pricing Page erstellen:**
   - Comparison Table
   - FAQ: "Can I cancel anytime?" (Ja!)
   - CTA: "Start Free Trial"

**Ergebnis:** ✅ Klare Pricing-Strategie, bereit zu launchen

---

### ✅ Phase 2 Checkpoint

**Hast du alle Punkte?**
- [ ] 50+ Beta-Signups
- [ ] 10+ aktive Tester
- [ ] Feedback-Prozess läuft
- [ ] MVP stabil (keine Critical Bugs)
- [ ] Pricing finalisiert

**Budget bisher:** ~€600-800  
**Nächste Phase:** PUBLIC LAUNCH! 🚀

---

## 💰 Phase 3: Public Launch (3-6 Monate)

**Ziel:** Erste zahlende Kunden (Target: 10-50), €500-5000 MRR  
**Budget:** €500-2000  
**Zeitaufwand:** Vollzeit (falls möglich)

---

#### ☑️ 3.1 Kleinunternehmer anmelden

**Wann:** SOBALD du erste Zahlung erwartest  
**Zeitaufwand:** 2 Stunden  
**Kosten:** €0 (Anmeldung), €100-300/Jahr (Buchhaltung)

**Schritte:**

1. [ ] **Finanzamt informieren:**
   
   - Formular: "Fragebogen zur steuerlichen Erfassung"
   - Download: https://www.formulare-bfinv.de
   - Ausfüllen:
     - Tätigkeit: "Softwareentwicklung und SaaS-Betrieb"
     - Kleinunternehmerregelung §19 UStG: JA (wenn Umsatz < €22.000)
     - Einnahmen-Überschuss-Rechnung (EÜR): JA
   
2. [ ] **Was bedeutet Kleinunternehmer?**
   
   ✅ **Vorteile:**
   - Keine Umsatzsteuer auf Rechnungen (einfacher!)
   - Keine monatliche USt-Voranmeldung
   - Einfache Buchhaltung (EÜR statt Bilanz)
   
   ❌ **Nachteile:**
   - Keine Vorsteuer-Abzug (AWS-Kosten inkl. USt)
   - Gilt NUR bis €22.000 Umsatz/Jahr
   - Dann: Regelbesteuerung Pflicht
   
   **Für dich perfekt bis ~20 zahlende Kunden!**

3. [ ] **Steuernummer erhalten:**
   - Finanzamt sendet nach 2-4 Wochen
   - Diese Nummer kommt auf Rechnungen
   - Format: `12/345/67890`

4. [ ] **Buchhaltung-Tool:**
   
   **Option A: Lexoffice (€10/Monat)**
   - https://www.lexoffice.de
   - Rechnungen schreiben
   - Belege sammeln (Foto-Upload)
   - EÜR automatisch
   
   **Option B: sevDesk (€9/Monat)**
   - Ähnlich wie Lexoffice
   - Bessere Bankanbindung
   
   **Option C: Excel (kostenlos, aber mühsam)**
   - Template: https://www.excel-vorlagen.net

**Ergebnis:** ✅ Kleinunternehmer angemeldet, Rechnungen schreiben OK

---

#### ☑️ 3.2 Stripe Account & Zahlungen

**Warum:** Professionelle Zahlungsabwicklung  
**Zeitaufwand:** 3 Stunden Setup  
**Kosten:** €0 + 1.5% + €0.25 pro Transaktion

**Schritte:**

1. [ ] **Stripe Account erstellen:**
   - https://dashboard.stripe.com/register
   - Business Type: Individual (später zu Company ändern)
   - Land: Deutschland
   - Bankkonto hinterlegen (Auszahlungen)

2. [ ] **Stripe Products anlegen:**
   
   ```
   Product: OverCloud Starter
   - Price: €29/Monat
   - Recurring: Monthly
   - Trial: 14 Tage
   
   Product: OverCloud Pro
   - Price: €99/Monat
   - Recurring: Monthly
   - Trial: 14 Tage
   ```

3. [ ] **Stripe Checkout Integration:**
   
   Backend:
   ```python
   # app/api/billing.py
   @router.post("/create-checkout-session")
   async def create_checkout_session(plan: str):
       session = stripe.checkout.Session.create(
           payment_method_types=['card'],
           line_items=[{
               'price': PRICE_IDS[plan],  # aus Stripe
               'quantity': 1,
           }],
           mode='subscription',
           success_url='https://overcloud.io/success',
           cancel_url='https://overcloud.io/pricing',
       )
       return {"checkout_url": session.url}
   ```
   
   Frontend:
   ```javascript
   // Redirect to Stripe Checkout
   const response = await fetch('/api/v1/billing/create-checkout-session', {
       method: 'POST',
       body: JSON.stringify({ plan: 'starter' })
   });
   const { checkout_url } = await response.json();
   window.location.href = checkout_url;
   ```

4. [ ] **Webhooks einrichten:**
   
   - Stripe Dashboard → Developers → Webhooks
   - Endpoint: `https://api.overcloud.io/api/v1/webhooks/stripe`
   - Events:
     - `checkout.session.completed` (Erfolgreiche Zahlung)
     - `customer.subscription.updated` (Plan-Wechsel)
     - `customer.subscription.deleted` (Kündigung)
   
   Backend:
   ```python
   @router.post("/webhooks/stripe")
   async def stripe_webhook(request: Request):
       payload = await request.body()
       sig = request.headers.get('stripe-signature')
       
       event = stripe.Webhook.construct_event(
           payload, sig, STRIPE_WEBHOOK_SECRET
       )
       
       if event['type'] == 'checkout.session.completed':
           # User-Account auf "paid" setzen
           # Email: "Welcome to OverCloud Pro!"
       
       return {"status": "success"}
   ```

5. [ ] **Rechnungen automatisieren:**
   - Stripe sendet automatisch Invoices
   - Email-Vorlage anpassen (Stripe Dashboard)
   - Dein Logo hochladen
   - Kleinunternehmer-Hinweis:
     ```
     Hinweis: Gemäß §19 UStG wird keine Umsatzsteuer berechnet.
     ```

6. [ ] **Test-Zahlung durchführen:**
   - Stripe Test-Modus
   - Testkarte: `4242 4242 4242 4242`
   - Prüfe: Webhook funktioniert, User-Upgrade klappt

**Ergebnis:** ✅ Zahlungen funktionieren, automatisiert

---

#### ☑️ 3.3 Launch auf ProductHunt

**Warum:** Maximale Sichtbarkeit, viele Signups  
**Zeitaufwand:** 1 Tag Vorbereitung, 1 Tag aktiv  
**Kosten:** €0

**Schritte:**

1. [ ] **2 Wochen vorher - Vorbereitung:**
   
   - [ ] Teaser-Post: "Launching OverCloud on PH soon! 🚀"
   - [ ] Sammle Email-Liste: "Notify me on launch day"
   - [ ] Screenshots perfektionieren
   - [ ] Video-Demo erstellen (60-90 Sekunden)
   - [ ] Tagline optimieren: "Visual Terraform builder for cloud infrastructure"

2. [ ] **1 Woche vorher - Hunter finden:**
   
   **Was ist ein Hunter?**
   - Jemand mit vielen PH-Followern submits dein Produkt
   - → Mehr initiale Upvotes → Bessere Platzierung
   
   **Wo finden?**
   - https://www.producthunt.com/@rrhoover (Founder)
   - Top-Hunter: https://www.producthunt.com/leaderboard/hunters
   - Twitter: "Looking for PH Hunter for my launch"
   
   **ODER:** Selbst launchen (weniger Boost, aber OK)

3. [ ] **Launch-Tag (Dienstag-Donnerstag optimal):**
   
   - [ ] 00:01 PST (Pacific Time) submit
   - [ ] Erste 6 Stunden kritisch - aktiv in Comments!
   - [ ] Tweet: "We're live on ProductHunt! 🚀"
   - [ ] LinkedIn Post
   - [ ] Email an Beta-Liste: "Vote for us!"
   - [ ] Freunde mobilisieren (Upvote + Comment)

4. [ ] **Beschreibung perfektionieren:**
   
   ```
   Tagline: Visual Terraform builder - design cloud infrastructure, get code
   
   Description:
   OverCloud transforms complex Terraform configurations into visual diagrams.
   
   🎯 Problem: Terraform has a steep learning curve
   ✨ Solution: Drag & drop AWS components, get production-ready code
   
   Features:
   ✅ Visual architecture builder
   ✅ Real-time cost estimation
   ✅ JSON-first (git-friendly)
   ✅ Open Source (AGPLv3)
   
   Perfect for: DevOps engineers, startups, cloud consultants
   
   Try the beta: overcloud.io
   ```

5. [ ] **Erster Kommentar als Maker:**
   
   ```
   Hey Product Hunt! 👋
   
   I'm Andy, solo developer behind OverCloud.
   
   I built this because Terraform felt unnecessarily complex. I wanted
   something visual that my non-DevOps teammates could understand.
   
   What makes OverCloud different:
   - Requirements → Decisions → Code (transparent)
   - JSON source of truth (not Terraform)
   - Cost estimation BEFORE deploying
   
   Looking forward to your feedback! AMA 🚀
   ```

6. [ ] **Ziel:**
   - Top 5 Product of the Day → ~500-2000 Visits
   - Top 1 Product of the Day → ~2000-5000 Visits
   - Conversion: 5-10% → 100-500 Signups

**Ergebnis:** ✅ Massiv Traffic, erste Presse-Erwähnungen

---

#### ☑️ 3.4 Content Marketing starten

**Warum:** Nachhaltiger Traffic, SEO aufbauen  
**Zeitaufwand:** 4-8 Stunden/Woche  
**Kosten:** €0

**Schritte:**

1. [ ] **Blog starten:**
   
   Erstelle: `/frontend/src/blog/`
   
   **Erste Posts (1 pro Woche):**
   - "Terraform vs OverCloud: Side-by-side comparison"
   - "5 ways to reduce your AWS bill (with examples)"
   - "How we generate Terraform from JSON (Technical Deep-Dive)"
   - "OverCloud vs Pulumi: Which to choose?"
   
   **SEO-Optimiert:**
   - Keywords: "terraform alternative", "visual terraform", "terraform builder"
   - Internal Links
   - Meta Descriptions
   - Open Graph Images

2. [ ] **YouTube Channel (optional, aber powerful):**
   
   **Video-Ideen:**
   - "Build a 3-tier web app in OverCloud (10 Minutes)"
   - "Terraform made visual - OverCloud demo"
   - "Cost optimization tricks for AWS"
   
   **Equipment:**
   - ❌ Keine teure Kamera nötig!
   - ✅ Screen Recording: OBS Studio (kostenlos)
   - ✅ Mikrofon: €50-100 (Blue Yeti, Audio-Technica)

3. [ ] **Guest Posts:**
   
   DevOps Blogs:
   - https://dev.to
   - https://medium.com
   - https://hashnode.com
   - https://dzone.com
   
   Pitch: "I built a visual Terraform builder - here's what I learned"

4. [ ] **SEO Foundations:**
   - [ ] Google Search Console einrichten
   - [ ] Sitemap.xml generieren
   - [ ] robots.txt erstellen
   - [ ] Schema.org Markup (SoftwareApplication)

**Ergebnis:** ✅ Konstanter organischer Traffic

---

### ✅ Phase 3 Checkpoint

**Hast du alle Punkte?**
- [ ] Kleinunternehmer angemeldet
- [ ] Stripe funktioniert, erste Zahlungen
- [ ] ProductHunt Launch erfolgreich (Top 10?)
- [ ] 10-50 zahlende Kunden
- [ ] €500-5000 MRR (Monthly Recurring Revenue)
- [ ] Content Marketing läuft

**Budget bisher:** ~€1.500-3.000  
**Nächste Phase:** Skalieren & Firma gründen!

---

## 🏢 Phase 4: Skalierung (6-12 Monate)

**Ziel:** UG gründen, 100+ Kunden, €10.000+ MRR  
**Budget:** €5.000-10.000  
**Zeitaufwand:** Vollzeit

---

#### ☑️ 4.1 UG gründen (bei >€2.000 MRR)

**Warum:** Haftungsbeschränkung, professioneller für Investoren  
**Zeitaufwand:** 1 Tag (Vorbereitung) + 1 Tag (Notar)  
**Kosten:** €600 (Gründung) + €1.500/Jahr (Steuerberater)

**Schritte:**

1. [ ] **Vorbereitung (vor Notar):**
   
   Benötigt:
   - [ ] Firmenname: "OverCloud UG (haftungsbeschränkt)"
   - [ ] Geschäftsadresse (kann Privatadresse sein)
   - [ ] Stammkapital: €2.500 (empfohlen, mind. €1)
   - [ ] Geschäftszweck:
     ```
     Entwicklung und Betrieb von Software-as-a-Service (SaaS) Lösungen
     für Cloud-Infrastruktur-Management; Beratung im Bereich DevOps
     und Cloud Computing.
     ```

2. [ ] **Notar-Termin buchen:**
   - Google: "Notar [deine Stadt] UG Gründung"
   - Termin: ~1 Stunde
   - Kosten: ~€200-300

3. [ ] **Notar-Termin:**
   - Gesellschaftsvertrag unterschreiben
   - Geschäftsführer-Bestellung (du)
   - Notarielle Beurkundung

4. [ ] **Nach Notar - Handelsregister:**
   - Notar sendet Unterlagen ans Amtsgericht
   - Wartezeit: 2-4 Wochen
   - Handelsregister-Nummer: HRB XXXXX
   - **Wichtig:** Erst JETZT darfst du als UG agieren!

5. [ ] **Geschäftskonto eröffnen:**
   
   **Optionen:**
   - **N26 Business** (€0-10/Monat, schnell online)
   - **Kontist** (€9/Monat, mit Buchhaltung)
   - **FYRST** (€0, Deutsche Bank)
   - **Holvi** (€9/Monat, EU-weit)
   
   **Erforderlich:**
   - Handelsregister-Auszug
   - Personalausweis
   - Gesellschaftsvertrag

6. [ ] **Stammkapital einzahlen:**
   - €2.500 von Privatkonto → Geschäftskonto
   - Buchung: "Stammkapital-Einlage"

7. [ ] **Gewerbeanmeldung:**
   - Gewerbeamt deiner Stadt
   - Formular: "Gewerbeanmeldung"
   - Kosten: ~€20-50
   - → IHK-Mitgliedschaft automatisch (~€150-300/Jahr)

8. [ ] **Finanzamt (erneut):**
   - Bekommt automatisch Info vom Gewerbeamt
   - Fragebogen ausfüllen (UG = Kapitalgesellschaft)
   - USt-ID beantragen (für EU-Geschäfte)

9. [ ] **Steuerberater suchen:**
   
   **Warum brauchst du jetzt einen?**
   - UG = Doppelte Buchführung (komplex!)
   - Körperschaftsteuer-Erklärung
   - Gewerbesteuer-Erklärung
   - Umsatzsteuer-Voranmeldung (monatlich!)
   
   **Kosten:**
   - €100-300/Monat (je nach Umsatz)
   - Jahresabschluss: €800-1.500/Jahr
   
   **Finden:**
   - Google: "Steuerberater Startups [Stadt]"
   - Empfehlungen von Gründern
   - Spezialisierung: "Digitale Geschäftsmodelle", "SaaS"

**Ergebnis:** ✅ UG gegründet, Geschäftskonto, Steuerberater

---

#### ☑️ 4.2 Versicherungen abschließen

**Warum:** Risiken absichern  
**Zeitaufwand:** 2 Stunden  
**Kosten:** €300-800/Jahr

**Schritte:**

1. [ ] **Betriebshaftpflicht (PFLICHT):**
   - Deckung: €3-5 Millionen
   - Kosten: €150-300/Jahr
   - Anbieter: Hiscox, exali, Allianz
   - Schützt vor: Kundendaten-Verlust, Server-Ausfall, Fehler in Software

2. [ ] **Cyber-Versicherung (optional, empfohlen):**
   - Deckung: Hackerangriffe, Datenlecks
   - Kosten: €200-500/Jahr
   - **Für SaaS wichtig!**

3. [ ] **Rechtsschutz (optional):**
   - Kosten: €300-500/Jahr
   - Schützt vor: Abmahnungen, Vertragsstreitigkeiten

**Ergebnis:** ✅ Risiken abgesichert

---

#### ☑️ 4.3 Team erweitern (optional)

**Wann:** Bei >€10.000 MRR, wenn du Solo nicht mehr schaffst  
**Optionen:**

1. **Freelancer (flexibel):**
   - Frontend-Dev: €50-100/Stunde
   - Backend-Dev: €60-120/Stunde
   - Designer: €40-80/Stunde
   - Plattformen: Upwork, Fiverr, Malt

2. **Teilzeit-Mitarbeiter (520€-Job):**
   - 10-20 Stunden/Woche
   - €520/Monat (Minijob)
   - Pauschalabgaben: ~€150 (UG zahlt)

3. **Co-Founder (Equity):**
   - 10-30% Firmenanteile
   - Kein Gehalt (am Anfang)
   - Suche: Startup-Events, AngelList

**Ergebnis:** ✅ Team-Support, schnellere Entwicklung

---

#### ☑️ 4.4 Investoren-Pitch (optional)

**Wann:** Bei >€5.000 MRR + klarem Wachstumsplan  
**Zeitaufwand:** 40-80 Stunden (Pitch Deck)  
**Kosten:** €0

**Schritte:**

1. [ ] **Pitch Deck erstellen (10-12 Slides):**
   
   ```
   1. Problem
   2. Solution (OverCloud)
   3. Market Size (TAM/SAM/SOM)
   4. Product Demo (Screenshots/Video)
   5. Business Model (Pricing)
   6. Traction (Customers, MRR, Growth)
   7. Roadmap (Next 12 Months)
   8. Team (du + evtl. Co-Founder)
   9. Competition (Pulumi, Terraform Cloud)
   10. Financials (MRR, CAC, LTV)
   11. Ask (€100k Seed für 10%)
   12. Vision (Multi-Cloud, AI-Features)
   ```

2. [ ] **Investoren finden:**
   - AngelList: https://angel.co
   - Crunchbase: VC-Suche
   - Startup-Events: Bits & Pretzels (München), TOA (Berlin)
   - Y Combinator: https://www.ycombinator.com/apply

3. [ ] **Due Diligence vorbereiten:**
   - Saubere Buchhaltung
   - Alle Verträge dokumentiert
   - GitHub gut strukturiert
   - Metriken dashboard (MRR, Churn, CAC, LTV)

**Ergebnis:** ✅ Funding (oder Decision: Bootstrapping)

---

### ✅ Phase 4 Checkpoint

**Hast du alle Punkte?**
- [ ] UG gegründet
- [ ] Geschäftskonto + Steuerberater
- [ ] Versicherungen abgeschlossen
- [ ] 100+ zahlende Kunden
- [ ] €10.000+ MRR
- [ ] Team (optional)
- [ ] Investoren-Gespräche (optional)

**Budget gesamt:** ~€10.000-20.000  
**Status:** 🚀 **SKALIERBARES BUSINESS!**

---

## 📊 Kosten-Übersicht (Gesamt)

### Jahr 1 - Bootstrapping

| Phase | Zeitraum | Kosten | MRR Ziel |
|-------|----------|--------|----------|
| Phase 1: MVP Vorbereitung | Woche 1-2 | €500 | €0 |
| Phase 2: Soft Launch | Woche 3-10 | €300 | €0 |
| Phase 3: Public Launch | Monat 3-6 | €2.000 | €2.000-5.000 |
| Phase 4: Skalierung | Monat 7-12 | €5.000 | €10.000+ |
| **TOTAL** | **12 Monate** | **€7.800** | **€10.000+/Monat** |

### Detaillierte Kosten

**Einmalig:**
- Markenanmeldung: €300
- UG-Gründung: €600
- Domain (3 Jahre): €45
- **TOTAL Einmalig:** €945

**Jährlich (nach UG-Gründung):**
- Steuerberater: €1.500-2.400
- Geschäftskonto: €0-120
- Versicherungen: €300-800
- Domain: €15
- IHK-Beitrag: €150-300
- **TOTAL Jährlich:** €2.000-3.700

**Laufend (AWS, Tools):**
- AWS (10 Kunden): ~€100/Monat
- Stripe Fees (€2.000 MRR): ~€60/Monat
- Plausible Analytics: €9/Monat
- Email (Mailchimp): €0-20/Monat
- **TOTAL Laufend:** €170-190/Monat

---

## 🎯 Milestones & KPIs

### Monat 1-2: Foundation
- [ ] Marke angemeldet
- [ ] Beta-Seite live
- [ ] 50+ Email-Signups
- [ ] 10 aktive Beta-Tester

### Monat 3-4: Soft Launch
- [ ] ProductHunt Launch (Top 10)
- [ ] 500+ Visits
- [ ] 100+ Free Users
- [ ] Erste 5 zahlende Kunden
- [ ] €150 MRR

### Monat 5-6: Growth
- [ ] Kleinunternehmer angemeldet
- [ ] 20-30 zahlende Kunden
- [ ] €600-900 MRR
- [ ] 5% MoM Growth

### Monat 7-12: Scale
- [ ] UG gegründet
- [ ] 50-100 zahlende Kunden
- [ ] €1.500-3.000 MRR
- [ ] 10% MoM Growth

### Jahr 2: Skalierung
- [ ] 200-500 zahlende Kunden
- [ ] €6.000-15.000 MRR
- [ ] Team: 2-3 Personen
- [ ] Seed-Funding (optional): €100k-500k

---

## 🚨 Häufige Fehler (vermeiden!)

### ❌ Zu früh optimieren
- **Fehler:** Perfekte Infrastruktur bauen bevor erste Kunden
- **Lösung:** Ship MVP, dann iterieren

### ❌ Zu spät Firma gründen
- **Fehler:** Bei €5.000 MRR noch als Privatperson
- **Lösung:** Bei €2.000 MRR UG gründen (Haftungsschutz!)

### ❌ Kein Marketing
- **Fehler:** "Build it and they will come"
- **Lösung:** 50% Zeit für Development, 50% für Marketing

### ❌ Zu komplexe Features
- **Fehler:** 20 Features, keins perfekt
- **Lösung:** 3 Features, die perfekt funktionieren

### ❌ Feedback ignorieren
- **Fehler:** Eigene Vision über User-Needs
- **Lösung:** Build what users WANT, not what du DENKST

---

## 📞 Nächste Schritte - SOFORT starten!

### Diese Woche (5-10 Stunden):
1. [ ] Domain checken & kaufen (overcloud.io)
2. [ ] Marken-Recherche auf DPMA.de
3. [ ] LICENSE Files ins Repo
4. [ ] Beta-Landing-Page Wireframe skizzieren

### Nächste Woche (10-15 Stunden):
5. [ ] Marke anmelden (€300)
6. [ ] Beta-Seite live
7. [ ] Impressum + Datenschutz
8. [ ] 5 Freunde als Beta-Tester einladen

### Nächster Monat:
9. [ ] Reddit + HackerNews Posts
10. [ ] 50+ Beta-Signups
11. [ ] Feedback sammeln
12. [ ] MVP stabilisieren

---

## 🎓 Ressourcen-Links

### Rechtliches
- **DPMA Markenanmeldung:** https://www.dpma.de/marken/anmeldung/index.html
- **Marken-Recherche:** https://register.dpma.de/DPMAregister/marke/basis
- **eRecht24 (Impressum):** https://www.e-recht24.de/impressum-generator.html
- **Open Source Licenses:** https://choosealicense.com

### Firmengründung
- **Gründerplattform:** https://gruenderplattform.de
- **IHK Startup-Guide:** https://www.ihk.de/gruendung
- **Für-Gründer.de:** https://www.fuer-gruender.de

### Tools
- **Stripe:** https://stripe.com
- **Plausible Analytics:** https://plausible.io
- **Lexoffice (Buchhaltung):** https://www.lexoffice.de
- **N26 Business:** https://n26.com/de-de/business

### Marketing
- **ProductHunt:** https://www.producthunt.com
- **HackerNews:** https://news.ycombinator.com/submit
- **Dev.to:** https://dev.to
- **Reddit r/SideProject:** https://reddit.com/r/SideProject

---

## ✅ Quick-Check: Bist du bereit?

**JA, wenn:**
- [ ] MVP ist 80% fertig (Tests laufen, keine Critical Bugs)
- [ ] Du kannst 20+ Stunden/Woche investieren
- [ ] Du hast €500-1000 Budget für Start
- [ ] Du bist bereit für Feedback (auch negatives!)

**NEIN / WARTEN, wenn:**
- [ ] MVP crasht ständig
- [ ] Du hast <5 Stunden/Woche Zeit
- [ ] Budget = €0
- [ ] Du willst "perfektes Produkt" vor Launch

---

**Fragen? Probleme? Nächste Schritte unklar?**

→ Frag mich! Ich helfe bei jedem Schritt.

**Viel Erfolg mit OverCloud! 🚀**
