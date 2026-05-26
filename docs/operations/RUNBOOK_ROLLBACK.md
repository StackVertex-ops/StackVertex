# Runbook: Deployment Rollback

**Version:** 1.0.0  
**Datum:** 2026-05-17  
**Owner:** DevOps Team  
**Review:** Monatlich

---

## 📋 Übersicht

Dieses Runbook beschreibt wie ein fehlerhaftes Deployment zurückgerollt wird.

**Wann verwenden:**
- Nach fehlerhaftem Deployment
- Production Errors steigen dramatisch
- Critical Bugs entdeckt
- Performance-Degradation
- Security-Incident

**Ziel:** System in letzten stabilen Zustand zurückversetzen (<15 Min)

---

## ⚡ Quick Reference

### Schnell-Rollback (< 5 Min)

```bash
# Option 1: GitHub Actions Re-run (empfohlen)
1. GitHub → Actions → Workflows
2. Finde letztes erfolgreiches Deployment
3. "Re-run all jobs"

# Option 2: Git Revert
git revert HEAD
git push origin main

# Option 3: Manual Rollback (falls CI/CD down)
cd infrastructure/terraform/environments/production
git checkout <last-good-commit>
terraform apply
```

---

## 🔍 Severity Levels

### P1 - Critical (Sofortiger Rollback)
- Production komplett down
- Data Loss möglich
- Security Breach
- **SLA:** Rollback innerhalb 15 Min

### P2 - High (Rollback innerhalb 1h)
- Major Feature broken
- Performance-Degradation >50%
- Viele User betroffen (>50%)
- **SLA:** Rollback innerhalb 1 Stunde

### P3 - Medium (Rollback optional)
- Minor Feature broken
- Wenige User betroffen (<10%)
- Workaround verfügbar
- **Entscheidung:** Product Owner

### P4 - Low (Forward Fix)
- UI Bug
- Typo
- Non-critical Issue
- **Empfehlung:** Forward Fix statt Rollback

---

## 📝 Rollback Procedure

### Phase 1: Incident Detection (0-5 Min)

#### 1.1 Verify Incident

**Checks:**
- [ ] Sentry: Sudden spike in errors?
- [ ] CloudWatch: Metrics abnormal?
- [ ] UptimeRobot: Downtime alert?
- [ ] User Reports: Support-Tickets?

**Command:**
```bash
# Check Sentry
open https://sentry.io/organizations/stackvertex/issues/

# Check CloudWatch
aws cloudwatch get-metric-statistics \
    --namespace AWS/ECS \
    --metric-name CPUUtilization \
    --start-time $(date -u -d '30 minutes ago' +%Y-%m-%dT%H:%M:%S) \
    --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
    --period 300 \
    --statistics Average

# Check health endpoint
curl -i https://api.stackvertex.io/health
```

#### 1.2 Determine Severity

**Fragen:**
1. Wie viele User betroffen? (1, 10, 100, alle?)
2. Welche Funktionalität? (Core, Nice-to-Have?)
3. Data Loss möglich? (Ja/Nein)
4. Workaround verfügbar? (Ja/Nein)

**Entscheidung:**
- **P1/P2:** Sofort rollback
- **P3:** Product Owner fragen
- **P4:** Forward fix planen

### Phase 2: Rollback Execution (5-15 Min)

#### 2.1 Notify Team

```bash
# Slack Nachricht (anpassen an euer Setup)
# Channel: #stackvertex-incidents

**INCIDENT: Production Rollback**
Severity: P1
Reason: [kurze Beschreibung]
Action: Rolling back to last good deployment
ETA: 15 minutes
Owner: [dein Name]
```

#### 2.2 Execute Rollback

**Option A: GitHub Actions Re-run (empfohlen)**

1. **Gehe zu GitHub Actions:**
   - https://github.com/andyschwarz/stackvertex/actions
   
2. **Finde letztes erfolgreiches Deployment:**
   - Filter: Workflows → "Deploy to Production"
   - Status: ✅ Success
   - Timestamp: Vor dem Problem

3. **Re-run Workflow:**
   - Click auf Workflow
   - Button: "Re-run all jobs"
   - Warten (~5-10 Min)

4. **Monitor Deployment:**
   ```bash
   # Watch GitHub Actions
   gh run watch
   
   # Watch ECS Service
   watch -n 5 'aws ecs describe-services \
       --cluster stackvertex-production \
       --services stackvertex-backend \
       --query "services[0].deployments"'
   ```

**Option B: Git Revert (bei CI/CD Problemen)**

```bash
# 1. Identifiziere bad commit
git log --oneline -10

# 2. Revert commit
git revert <bad-commit-sha>

# 3. Push to main (triggert CI/CD)
git push origin main

# 4. Monitor deployment (siehe oben)
```

**Option C: Manual Terraform (falls CI/CD down)**

```bash
# 1. Checkout last good commit
cd infrastructure/terraform/environments/production
git log --oneline -10
git checkout <last-good-commit>

# 2. Plan rollback
terraform plan -out=rollback.tfplan

# 3. Review plan (WICHTIG!)
less rollback.tfplan

# 4. Apply rollback
terraform apply rollback.tfplan

# 5. Verify
curl https://api.stackvertex.io/health
```

#### 2.3 Verify Rollback

**Health Checks:**
```bash
# 1. Health Endpoint
curl -i https://api.stackvertex.io/health
# Expected: 200 OK

# 2. Check Sentry (neue Errors?)
# Expected: Error rate zurück auf normal

# 3. Check Deployment Status
aws ecs describe-services \
    --cluster stackvertex-production \
    --services stackvertex-backend \
    --query 'services[0].deployments[0].status'
# Expected: PRIMARY

# 4. Smoke Tests
curl https://api.stackvertex.io/api/v1/auth/health
curl https://api.stackvertex.io/api/v1/architectures
```

**Success Criteria:**
- [ ] Health endpoint returns 200
- [ ] Error rate < 1% (normal baseline)
- [ ] Response times < 500ms (p95)
- [ ] No new Sentry alerts (15 Min window)

### Phase 3: Post-Rollback (15-30 Min)

#### 3.1 Update Status Page

```
Title: Service Restored
Status: Resolved
Message: "The issue has been resolved by rolling back 
         to a previous stable version. Service is 
         operating normally. We will investigate 
         the root cause and communicate findings."
```

#### 3.2 Notify Stakeholders

**Email Template:**
```
Subject: [RESOLVED] Production Incident - Rollback Completed

Hi Team,

The production incident has been resolved.

What happened:
- Time: [HH:MM - HH:MM UTC]
- Issue: [Beschreibung]
- Impact: [Anzahl User, Features]

Resolution:
- Rolled back to previous stable deployment
- Service restored at [HH:MM UTC]
- Total downtime: [X] minutes

Next steps:
- Root cause analysis (due: [Date])
- Fix will be deployed after thorough testing
- Post-mortem meeting: [Date, Time]

Questions? Reply to this email or ping in #stackvertex-incidents

[Dein Name]
DevOps Team
```

#### 3.3 Create Post-Mortem Task

```bash
# Create GitHub Issue für Post-Mortem
gh issue create \
    --title "Post-Mortem: Production Rollback [DATE]" \
    --body "
**Incident Summary**
- Date: $(date)
- Severity: P1
- Duration: X minutes
- Root Cause: TBD

**Action Items**
- [ ] Root cause analysis
- [ ] Fix implementation
- [ ] Additional tests
- [ ] Prevention measures
- [ ] Documentation update

**Timeline**
- HH:MM - Incident detected
- HH:MM - Rollback initiated
- HH:MM - Service restored

**Lessons Learned**
(to be filled during post-mortem meeting)
" \
    --label "incident,post-mortem"
```

---

## 🔧 Rollback Scenarios

### Scenario 1: Database Migration Failed

**Symptoms:**
- 500 Errors on all endpoints
- Logs: "DatabaseError: column X does not exist"

**Rollback:**
```bash
# 1. Rollback code (siehe Phase 2)
# 2. Rollback DB migration
cd backend
poetry run alembic downgrade -1

# 3. Verify
poetry run alembic current
```

### Scenario 2: Broken API Endpoint

**Symptoms:**
- Specific endpoint returns 500
- Sentry: "AttributeError in /api/v1/billing"

**Rollback:**
```bash
# Option 1: Full rollback (empfohlen bei P1)
# → Siehe Phase 2

# Option 2: Feature Flag (wenn vorhanden)
# Disable broken feature via admin panel oder env var
ENABLE_NEW_BILLING=false
```

### Scenario 3: Performance Degradation

**Symptoms:**
- Response times >5s (normal: <500ms)
- CloudWatch: CPU 90%+

**Rollback:**
```bash
# 1. Identify cause
# - Inefficient query?
# - Memory leak?
# - DDoS?

# 2. If code-related: Full rollback
# → Siehe Phase 2

# 3. If infrastructure: Scale up (temporary)
aws ecs update-service \
    --cluster stackvertex-production \
    --service stackvertex-backend \
    --desired-count 10  # Double capacity

# 4. Monitor
watch -n 5 'aws cloudwatch get-metric-statistics ...'
```

### Scenario 4: Security Incident

**Symptoms:**
- Sentry: "Unauthorized access detected"
- AWS GuardDuty Alert

**Rollback:**
```bash
# 1. IMMEDIATELY rollback
# → Siehe Phase 2 (Priority P1!)

# 2. Rotate secrets
aws secretsmanager update-secret \
    --secret-id stackvertex/production/jwt-secret \
    --secret-string "$(openssl rand -base64 32)"

# 3. Invalidate all sessions
redis-cli FLUSHDB

# 4. Security audit
# → Separate runbook: RUNBOOK_SECURITY_INCIDENT.md
```

---

## 📊 Monitoring Post-Rollback

### Metrics to Watch (30 Min)

```bash
# 1. Error Rate
# Sentry Dashboard → Last 30 minutes
# Expected: < 1%

# 2. Response Times
# CloudWatch → ECS Metrics → ResponseTime
# Expected: p95 < 500ms

# 3. CPU/Memory
# CloudWatch → ECS Metrics → CPU/Memory
# Expected: CPU < 50%, Memory < 70%

# 4. Request Count
# CloudWatch → ALB Metrics → RequestCount
# Expected: Back to normal traffic pattern
```

---

## 🚨 Escalation Path

### Level 1: On-Call Engineer (You)
- Execute rollback
- Monitor metrics
- Update status page

**Escalate wenn:**
- Rollback schlägt fehl
- Issue persistiert nach rollback
- Unsicher über Severity

### Level 2: Senior DevOps / Tech Lead
- Alternative rollback strategies
- Infrastructure debugging
- Kommunikation mit Management

**Contact:**
- Slack: @tech-lead
- Phone: [Number]

### Level 3: CTO / Management
- Business impact decisions
- Customer communication
- Post-mortem coordination

**Contact:**
- Email: cto@stackvertex.io

---

## ✅ Rollback Checklist

### Pre-Rollback
- [ ] Incident verified (not false alarm)
- [ ] Severity determined (P1-P4)
- [ ] Team notified (#stackvertex-incidents)
- [ ] Last good commit identified

### During Rollback
- [ ] Rollback method chosen (GitHub/Git/Manual)
- [ ] Rollback executed
- [ ] Deployment monitored
- [ ] Health checks passed

### Post-Rollback
- [ ] Metrics verified (30 Min window)
- [ ] Status page updated
- [ ] Stakeholders notified
- [ ] Post-mortem issue created
- [ ] Runbook updated (lessons learned)

---

## 📚 Related Runbooks

- **RUNBOOK_DEPLOYMENT.md** - Standard deployment procedure
- **RUNBOOK_SECURITY_INCIDENT.md** - Security-specific rollback
- **RUNBOOK_DATABASE_RESTORE.md** - DB-specific recovery
- **RUNBOOK_HOTFIX.md** - Emergency bug fix deployment

---

## 📖 Appendix

### A. Common Error Codes

| Code | Meaning | Action |
|------|---------|--------|
| 500 | Internal Server Error | Check Sentry, likely code bug |
| 502 | Bad Gateway | Check ECS service health |
| 503 | Service Unavailable | Check if deployment in progress |
| 504 | Gateway Timeout | Check backend response times |

### B. Useful Commands

```bash
# Check last 5 deployments
gh run list --workflow=deploy-production --limit 5

# Get ECS task logs
aws logs tail /ecs/stackvertex-production/backend --follow

# Check Terraform state
cd infrastructure/terraform/environments/production
terraform show

# Force new ECS deployment (without code change)
aws ecs update-service \
    --cluster stackvertex-production \
    --service stackvertex-backend \
    --force-new-deployment
```

### C. Contact List

| Role | Name | Slack | Phone | Timezone |
|------|------|-------|-------|----------|
| On-Call | Rotating | @oncall | - | CET |
| Tech Lead | Andy | @andy | - | CET |
| CTO | - | @cto | - | CET |

---

**Version History:**
- 1.0.0 (2026-05-17) - Initial version

**Next Review:** 2026-06-17
