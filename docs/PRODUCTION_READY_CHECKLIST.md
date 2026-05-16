# Production Ready Checklist

## Pragmatische Checkliste für den Go-Live

**Ziel:** OverCloud production-ready machen - funktional, sicher, nicht over-engineered.

---

## Phase 1: Infrastructure ✅ FERTIG

- ✅ Dev/Staging/Prod Environments (Terraform)
- ✅ Automated Backups + Cross-Region DR
- ✅ WAF + DDoS Protection (CloudFront)
- ✅ CI/CD Pipeline (GitHub Actions)
- ✅ Security Scanning (automatisiert, wöchentlich)

**Status:** Bereit für Deployment

---

## Phase 2: Compliance ✅ FERTIG

- ✅ ISO 27001 Dokumentation
- ✅ SOC 2 Readiness (75%)
- ✅ DSGVO API Endpoints
- ✅ Incident Response Plan
- ✅ Risk Assessment

**Status:** Dokumentiert, ausreichend für erste Kunden

---

## Phase 3: Operational Basics (TODO - 3-5 Tage)

### 3.1 Error Tracking (1 Tag)

**Sentry Setup:**
```bash
# 1. Account erstellen: sentry.io (Free Tier reicht)
# 2. Project erstellen: overcloud-backend

# 3. DSN in Secrets Manager:
aws secretsmanager create-secret \
  --name prod/sentry/dsn \
  --secret-string "https://xxx@sentry.io/yyy"

# 4. In Backend aktivieren (schon vorbereitet):
# backend/app/core/config.py - SENTRY_DSN aus env
# Deployment triggered automatisch Sentry

# 5. Test:
# Trigger absichtlich einen Error, check Sentry Dashboard
```

**Fertig.** Keine komplexen Setups.

### 3.2 Uptime Monitoring (30 Minuten)

**UptimeRobot (oder Better Uptime):**
```bash
# 1. Account: uptimerobot.com (Free: 50 monitors)
# 2. Monitor erstellen:
#    - Name: OverCloud API Production
#    - Type: HTTPS
#    - URL: https://api.overcloud.io/health
#    - Interval: 5 minutes
#    - Alert: Email (deine Adresse)

# 3. Status Page (optional):
#    - Public Status Page erstellen
#    - Embed auf overcloud.io/status

# Fertig. Mehr braucht es nicht.
```

### 3.3 Backup Restore Test (2 Stunden)

**Einmaliger Test, dann monatlich:**
```bash
# Test Script (schon in BCP dokumentiert)
cd infrastructure/terraform/scripts
./test-backup-restore.sh

# Was es tut:
# 1. Restore staging DB aus prod backup (vor 1h)
# 2. Verify data integrity (row counts)
# 3. Cleanup test DB
# 4. Log result

# Dann: Cronjob oder GitHub Action (monatlich)
```

### 3.4 Basic Runbooks (1 Tag)

**Nur 3 essenzielle Runbooks:**

1. **API Down** - Bereits in INCIDENT_RESPONSE_PLAN.md
2. **Database Issue** - Bereits in INCIDENT_RESPONSE_PLAN.md  
3. **Rollback Deployment** - Neu (siehe unten)

```markdown
# Runbook: Rollback Deployment

## When: Nach fehlerhaftem Deployment

## Steps:
1. GitHub → Actions → Re-run previous workflow
   (oder: git revert + push)

2. Verify health:
   curl https://api.overcloud.io/health

3. Monitor errors (Sentry) für 15 min

4. Post-Mortem erstellen (wenn P1/P2)

## Done.
```

**Keine 50-seitigen Runbook-Collections.** Keep it simple.

---

## Go-Live Checklist (Final)

### Pre-Launch (1 Woche vor Go-Live)

- [ ] **Prod Deployment:** Terraform apply auf prod (smoke test)
- [ ] **Sentry:** Aktiviert, Error triggern, Alarm testen
- [ ] **Uptime Monitor:** Aktiviert, Check empfängt Alerts
- [ ] **Backup Test:** Einmal durchführen, dokumentieren
- [ ] **DNS:** api.overcloud.io → Production API Gateway
- [ ] **SSL:** Zertifikat verifizieren (Let's Encrypt)
- [ ] **Secrets:** Alle production secrets rotiert (neue Passwörter)
- [ ] **MFA:** Aktiviert auf allen AWS/GitHub Accounts

### Launch Day

- [ ] **Deployment:** Final deployment (main branch)
- [ ] **Smoke Test:** 5 kritische User Flows manuell testen
- [ ] **Monitoring:** 2 Stunden beobachten (Sentry, CloudWatch)
- [ ] **Status:** "Generally Available" kommunizieren

### Post-Launch (Erste Woche)

- [ ] **Daily Check:** Sentry (Errors), CloudWatch (5XX), Uptime
- [ ] **Customer Feedback:** Erste Kunden onboarden, Feedback sammeln
- [ ] **Incident Log:** Alle Issues dokumentieren (auch P4)
- [ ] **Iterate:** Schnell fixen, nicht perfektionieren

---

## Was NICHT tun (Anti-Patterns)

❌ **Keine fancy Dashboards bauen** - CloudWatch Default reicht  
❌ **Keine komplexen Alerting-Rules** - Start mit Basics (5XX, Errors)  
❌ **Keine Blue/Green Deployments** - Rollback via Git reicht  
❌ **Keine 10 Monitoring Tools** - Sentry + CloudWatch + Uptime = genug  
❌ **Keine perfekten Runbooks** - Learn by doing, iterieren  
❌ **Keine Pre-Optimierung** - Erst Kunden, dann Performance-Tuning  

---

## Maintenance (Nach Go-Live)

### Täglich (5 Minuten)
- Sentry Dashboard checken (neue Errors?)
- CloudWatch Alarms checken (alles grün?)

### Wöchentlich (30 Minuten)
- Security Scan Results reviewen (GitHub Actions)
- Dependency Updates mergen (Dependabot PRs)

### Monatlich (2 Stunden)
- Backup Restore Test durchführen
- Access Review (wer hat Zugriff worauf?)
- Kosten Review (AWS Cost Explorer)

### Quarterly (1 Tag)
- Risk Assessment Update
- Incident Review (alle P1/P2)
- Compliance Check (ISO, SOC 2 Readiness)

**Das reicht.** Mehr ist Over-Engineering für ein Startup.

---

## Wann skalieren?

### Bei >10 Kunden:
- Erweiterte Monitoring (APM wie Datadog)
- Dedicated Support (Ticketing System)
- On-Call Rotation (wenn Team >2)

### Bei >100 Kunden:
- Feature Flags (LaunchDarkly, Unleash)
- Canary Deployments (Lambda Aliases)
- Advanced Security (SIEM, Threat Intelligence)

### Bei >1000 Kunden:
- Multi-Region Active-Active (nicht nur DR)
- Chaos Engineering (Break stuff intentionally)
- Dedicated SRE Team

**Aktuell:** Focus auf 0→10 Kunden. Keep it simple.

---

## Summary

**Fertig für Production?**
- ✅ Infrastructure: Ja
- ✅ Security: Ja (automated scans)
- ✅ Compliance: Ja (Docs ready)
- ⏳ Operational: 3-5 Tage Setup (Sentry, Uptime, Backup Test)

**Timeline:**
- **Heute:** Phase 3 Tasks starten (Sentry, Uptime)
- **Morgen:** Backup Test, Runbook ergänzen
- **+3 Tage:** Go-Live

**Next:** Erste 10 Kunden gewinnen, lernen, iterieren. 🚀

---

**Owner:** Andy Schwarz  
**Last Updated:** 2026-05-15  
**Philosophy:** "Make it work, make it right, make it fast" - In dieser Reihenfolge.
