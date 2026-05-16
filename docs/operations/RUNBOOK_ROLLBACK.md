# Runbook: Deployment Rollback

> **When:** Nach fehlerhaftem Deployment  
> **Severity:** P1 (Critical) - P3 (Minor)  
> **RTO:** 15 Minuten  
> **Owner:** DevOps / On-Call Engineer

---

## Wann dieses Runbook verwenden?

**Symptome eines fehlerhaften Deployments:**
- ✗ API gibt 500 Errors zurück
- ✗ Uptime Monitor zeigt "Down"
- ✗ Sentry zeigt plötzlich viele neue Errors
- ✗ CloudWatch Alarms triggern
- ✗ Kunden melden Probleme
- ✗ Health Check schlägt fehl

**Entscheidung: Rollback oder Forward-Fix?**

| Rollback wenn: | Forward-Fix wenn: |
|----------------|-------------------|
| Production ist down | Nur kleine Bugs (UI, Text, etc.) |
| Kritische Features broken | Fix dauert < 10 Minuten |
| Keine schnelle Lösung in Sicht | Root-Cause klar & einfach fixbar |
| Mehrere User betroffen | Nur 1-2 User betroffen |

**Faustregel:** Bei Zweifel → Rollback! Stabilität geht vor.

---

## Schnell-Übersicht (TL;DR)

```bash
# 1. GitHub → Actions → Neuestes Working Deployment → Re-run
# ODER
# 2. Git Revert + Push:
git revert HEAD --no-edit
git push origin main

# 3. Verify:
curl https://api.overcloud.io/health

# 4. Monitor:
# - Check Sentry (errors stopped?)
# - Check Uptime (back to "Up"?)
# - Manual smoke test

# 5. Post-Mortem (wenn P1/P2)
```

---

## Detailed Rollback Procedure

### Phase 1: Verify Problem (2 Min)

#### 1.1 Check Current Deployment

```bash
# What's deployed?
git log -1 --oneline

# When was it deployed?
gh run list --limit 1

# Check commit that broke it
git diff HEAD~1 HEAD
```

#### 1.2 Check Symptoms

**API Health:**
```bash
curl -I https://api.overcloud.io/health
# Expected: 200 OK
# Actual: 503 Service Unavailable → PROBLEM!
```

**Sentry Errors:**
```bash
# Open Sentry Dashboard
open https://sentry.io/organizations/overcloud/projects/overcloud-backend/

# New errors after deployment time?
# Filter: timesSeen:1 (new errors)
```

**CloudWatch Metrics:**
```bash
# Check error rate
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApiGateway \
  --metric-name 5XXError \
  --dimensions Name=ApiName,Value=overcloud-api \
  --start-time $(date -u -d '30 minutes ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

#### 1.3 Inform Team

```bash
# Post in Slack #overcloud-incidents
🚨 INCIDENT: Production API down after deployment
Commit: abc123 "Add feature X"
Symptoms: 500 errors, Uptime down
Action: Initiating rollback
ETA: 15 minutes
```

---

### Phase 2: Rollback (5-10 Min)

#### Option A: GitHub Actions Re-run (empfohlen)

**Vorteile:**
- ✅ Schnell (keine neuen Commits)
- ✅ Gleicher Workflow wie ursprüngliches Deployment
- ✅ Audit Trail in GitHub Actions

**Steps:**

1. **Öffne GitHub Actions:**
   ```
   https://github.com/AndySchw/OverCloud/actions
   ```

2. **Finde letztes ERFOLGREICHES Deployment:**
   - Filter: Workflow "Deploy to Production"
   - Status: ✅ Success
   - Zeitpunkt: VOR dem fehlerhaften Deployment

3. **Re-run Workflow:**
   - Klick auf das Working Deployment
   - Oben rechts: "Re-run all jobs"
   - Bestätige: "Re-run jobs"

4. **Monitor Deployment:**
   ```bash
   # Watch logs
   gh run watch
   ```

5. **Warte auf Completion** (~5-10 Min)

#### Option B: Git Revert + Push

**Vorteile:**
- ✅ Sauberer Git-History
- ✅ Kann lokal getestet werden
- ✅ Funktioniert immer (auch wenn Actions down)

**Steps:**

1. **Identify Bad Commit:**
   ```bash
   git log --oneline -5
   # abc123 [BREAKING] Add feature X  ← Das ist das Problem
   # def456 Update config
   # ghi789 Fix bug Y
   ```

2. **Revert Commit:**
   ```bash
   # Single commit revert
   git revert abc123 --no-edit

   # Multiple commits revert (wenn mehrere broken)
   git revert abc123 def456 --no-edit
   ```

3. **Verify Locally (optional, wenn Zeit):**
   ```bash
   # Start backend locally
   poetry run uvicorn app.main:app --reload

   # Test endpoint
   curl http://localhost:8000/health
   ```

4. **Push Revert:**
   ```bash
   git push origin main
   ```

5. **Monitor CI/CD:**
   ```bash
   # Watch deployment
   gh run watch

   # Or open in browser
   gh run view --web
   ```

#### Option C: Force Deploy Previous Version (Emergency)

**Nur wenn Option A/B nicht funktionieren!**

```bash
# 1. Checkout previous working commit
git checkout def456  # Previous working commit

# 2. Force push (DANGEROUS!)
git push origin HEAD:main --force

# 3. Trigger deployment manually
gh workflow run deploy.yml
```

**⚠️ Warning:** Force push kann zu Problemen führen. Nur in echten Notfällen!

---

### Phase 3: Verify Rollback (5 Min)

#### 3.1 Health Check

```bash
# Wait 2-3 minutes for deployment to complete

# Then check health
curl -I https://api.overcloud.io/health

# Expected: 200 OK
HTTP/2 200
content-type: application/json
```

#### 3.2 Smoke Test (Critical Paths)

```bash
# Test Authentication
curl -X POST https://api.overcloud.io/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'

# Test Architecture List
curl https://api.overcloud.io/api/v1/architectures \
  -H "Authorization: Bearer $TOKEN"

# Test Deployment Create (Mock)
curl -X POST https://api.overcloud.io/api/v1/deployments \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"architecture_id":"test-123","action":"plan"}'
```

#### 3.3 Monitor Errors

**Sentry:**
```bash
# Open Sentry
open https://sentry.io/organizations/overcloud/projects/overcloud-backend/

# Filter: Last 15 minutes
# New errors should stop appearing
```

**CloudWatch:**
```bash
# Check 5XX error rate
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApiGateway \
  --metric-name 5XXError \
  --dimensions Name=ApiName,Value=overcloud-api \
  --start-time $(date -u -d '15 minutes ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum

# Should be near 0
```

**Uptime Monitor:**
```bash
# Check UptimeRobot
open https://uptimerobot.com/dashboard

# Status should be "Up"
```

---

### Phase 4: Communication (3 Min)

#### 4.1 Update Incident Channel

```bash
# Post in Slack #overcloud-incidents
✅ RESOLVED: Rollback successful
Commit: Reverted to def456
Health: API is UP
Errors: Stopped
Uptime: 99.98%
Duration: 12 minutes downtime
Next: Post-mortem scheduled for tomorrow
```

#### 4.2 Update Status Page (wenn vorhanden)

```
UptimeRobot → Status Page → Post Update

Title: Service Restored
Message: "Das Problem wurde behoben. Alle Services laufen wieder normal."
Status: Resolved
```

#### 4.3 Inform Customers (wenn nötig)

**Wenn Downtime > 5 Minuten:**

```
Email Template:

Subject: [Resolved] Kurze Service-Unterbrechung

Liebe OverCloud-Nutzer,

heute zwischen 14:32 und 14:44 UTC (12 Minuten) kam es zu einer kurzen 
Service-Unterbrechung. Das Problem wurde identifiziert und behoben.

Was ist passiert?
- Ein fehlerhaftes Deployment verursachte API-Fehler
- Unser Monitoring hat das Problem sofort erkannt
- Wir haben innerhalb von 15 Minuten auf die vorherige Version zurückgerollt

Was tun wir dagegen?
- Verbesserte Pre-Deployment Tests
- Automatische Rollback-Mechanismen
- Detaillierter Post-Mortem Report

Danke für eure Geduld!

Das OverCloud Team
```

---

### Phase 5: Post-Mortem (1 Tag später)

**Nur für P1/P2 Incidents! P3/P4 → Optional**

#### 5.1 Post-Mortem Template

**Datei:** `docs/incidents/YYYY-MM-DD-deployment-rollback.md`

```markdown
# Incident Post-Mortem: Deployment Rollback

**Date:** 2026-05-15
**Duration:** 12 minutes (14:32 - 14:44 UTC)
**Severity:** P1 (Critical)
**Affected Services:** API (100%), Frontend (partial)
**User Impact:** ~50 users unable to login

---

## Timeline

| Time (UTC) | Event |
|------------|-------|
| 14:30 | Deployment of commit abc123 started |
| 14:32 | Deployment completed, API started returning 500 errors |
| 14:33 | Uptime Monitor alert received |
| 14:34 | On-call engineer investigated |
| 14:36 | Decision: Rollback (no quick fix available) |
| 14:37 | Rollback initiated (git revert + push) |
| 14:42 | Rollback deployment completed |
| 14:44 | Health check passed, errors stopped |
| 14:45 | Incident resolved |

---

## Root Cause

**What went wrong?**
- Feature X introduced a database query that caused deadlocks under load
- Query timeout was set to 30s instead of 3s
- Pre-deployment tests didn't catch this (no load testing)

**Why wasn't it caught?**
- Unit tests passed (mocked database)
- Staging environment has only test data (no load)
- No integration tests for this specific code path

---

## What Went Well

✅ Monitoring detected issue within 1 minute
✅ On-call engineer responded within 2 minutes
✅ Rollback completed in 10 minutes (under 15min RTO)
✅ Clear runbook available (this document)
✅ Team communication was fast and clear

---

## What Went Wrong

❌ Deployment had critical bug
❌ Pre-deployment tests insufficient
❌ No automatic rollback on health check failure
❌ Load testing not part of CI/CD

---

## Action Items

| Action | Owner | Due Date | Status |
|--------|-------|----------|--------|
| Add load tests to CI/CD | DevOps | 2026-05-20 | Open |
| Implement automatic health check rollback | Backend | 2026-05-22 | Open |
| Review query timeouts in code | Backend | 2026-05-18 | Open |
| Add integration test for auth flow | QA | 2026-05-25 | Open |
| Document load testing best practices | DevOps | 2026-05-30 | Open |

---

## Lessons Learned

1. **Always load test:** Integration tests ≠ Production load
2. **Fail fast:** Query timeouts should be < 5 seconds
3. **Automate rollback:** Health check failures should trigger automatic rollback
4. **Staging ≈ Production:** Use realistic data in staging

---

## Conclusion

This incident highlighted gaps in our pre-deployment testing. While our 
monitoring and rollback procedures worked well, we need better testing 
to prevent such issues from reaching production.

**Estimated cost of incident:** €50 (12 min downtime × 50 users)
**Estimated cost of prevention:** €200 (4h load testing setup)
**ROI of prevention:** 4x

**Next review:** 2026-06-15
```

---

## Rollback Decision Matrix

| Factor | Rollback | Forward-Fix |
|--------|----------|-------------|
| **Downtime** | > 5 minutes | < 5 minutes |
| **Fix Complexity** | Unknown or complex | Simple & clear |
| **User Impact** | High (many users) | Low (few users) |
| **Risk of Fix** | Might break more | Confident fix |
| **Time to Fix** | > 10 minutes | < 5 minutes |

**Score:** 3+ Rollback factors → Rollback

---

## Automated Rollback (Future)

**Ziel:** Automatisches Rollback bei Health Check Failure

**Implementierung in GitHub Actions:**

```yaml
# .github/workflows/deploy.yml

- name: Deploy to Production
  run: terraform apply -auto-approve

- name: Health Check
  run: |
    sleep 30  # Wait for deployment
    HEALTH=$(curl -s -o /dev/null -w "%{http_code}" https://api.overcloud.io/health)
    if [ "$HEALTH" != "200" ]; then
      echo "Health check failed! Status: $HEALTH"
      exit 1
    fi

- name: Rollback on Failure
  if: failure()
  run: |
    echo "Triggering automatic rollback..."
    git revert HEAD --no-edit
    git push origin main
    # Notify team
    curl -X POST $SLACK_WEBHOOK \
      -d '{"text":"🚨 Auto-rollback triggered! Health check failed."}'
```

---

## Contact & Escalation

**On-Call Engineer:**
- Slack: @oncall-engineer
- Phone: +49 XXX XXXXXXX
- Email: oncall@overcloud.io

**Escalation Path:**
1. **L1:** On-Call Engineer (response: 15 min)
2. **L2:** DevOps Lead (response: 30 min)
3. **L3:** CTO (response: 1 hour)

**Escalate when:**
- Rollback doesn't fix the issue
- Infrastructure-level problem (AWS outage)
- Multiple services affected
- Customer data at risk

---

## Checkliste

**Während Incident:**
- [ ] Problem verifiziert (Sentry, Uptime, CloudWatch)
- [ ] Team informiert (Slack #overcloud-incidents)
- [ ] Rollback-Entscheidung getroffen
- [ ] Rollback durchgeführt (GitHub Actions oder Git Revert)
- [ ] Health Check bestanden
- [ ] Smoke Tests durchgeführt
- [ ] Errors gestoppt (Sentry)
- [ ] Status Page updated
- [ ] Customers informiert (wenn > 5min Downtime)

**Nach Incident:**
- [ ] Post-Mortem geschrieben (P1/P2)
- [ ] Action Items erstellt
- [ ] Runbook updated (lessons learned)
- [ ] Team Review Meeting (optional)

---

## Related Documents

- [Incident Response Plan](./INCIDENT_RESPONSE_PLAN.md)
- [Business Continuity Plan](./BUSINESS_CONTINUITY_PLAN.md)
- [Deployment Guide](../../DEPLOYMENT_GUIDE.md)

---

**Last Updated:** 2026-05-15  
**Next Review:** 2026-06-15  
**Owner:** DevOps Team
