# Incident Response Plan

## Security Incident Management

**Document Version:** 1.0  
**Effective Date:** 2026-05-15  
**Review Date:** 2027-05-15  
**Owner:** Andy Schwarz (CISO)  
**Classification:** Internal

---

## 1. Purpose & Scope

### 1.1 Purpose

Dieser Plan definiert Prozesse zur schnellen und effektiven Reaktion auf Security Incidents, um:
- Schaden zu minimieren
- Recovery-Zeit zu reduzieren
- Lessons Learned zu dokumentieren
- Compliance-Anforderungen zu erfüllen (ISO 27001, SOC 2, DSGVO)

### 1.2 Scope

**In Scope:**
- Security Incidents (Unauthorized Access, Data Breach, DDoS, etc.)
- Availability Incidents (Production Outages, Database Failures)
- Data Incidents (Data Loss, Data Corruption)
- Compliance Incidents (DSGVO Violations)

**Out of Scope:**
- Software Bugs (handled by normal development process)
- Feature Requests
- Performance Tuning (unless critical degradation)

---

## 2. Incident Classification

### 2.1 Severity Levels

#### P1 - CRITICAL

**Definition:** Sofortige Bedrohung für Business Continuity oder kritischer Security Breach

**Examples:**
- Data Breach (PII exfiltration)
- Production complete outage (all users affected)
- RCE (Remote Code Execution) exploit
- Ransomware attack
- AWS account compromise

**Response Time:** <15 minutes  
**Resolution Target:** <4 hours  
**Escalation:** CISO + Management + External (if needed)  
**Communication:** Customer notification required (binnen 24h per DSGVO)

#### P2 - HIGH

**Definition:** Significant security risk or major service degradation

**Examples:**
- Authentication bypass
- Partial outage (>50% users affected)
- SQL Injection confirmed
- Sensitive data exposure (non-PII)
- Critical vulnerability (CVSS >9)

**Response Time:** <1 hour  
**Resolution Target:** <24 hours  
**Escalation:** CISO  
**Communication:** Internal + Status Page

#### P3 - MEDIUM

**Definition:** Security vulnerability or moderate service impact

**Examples:**
- Non-critical vulnerability (CVSS 7-9)
- Service degradation (<50% users)
- Failed security scan (multiple findings)
- Suspicious activity (potential attack)
- Minor data inconsistency

**Response Time:** <4 hours  
**Resolution Target:** <5 days  
**Escalation:** On-Duty Engineer  
**Communication:** Internal

#### P4 - LOW

**Definition:** Minor security concern or minimal impact

**Examples:**
- Low-severity vulnerability (CVSS <7)
- Cosmetic bugs
- Configuration issues (non-production)
- Security policy violation (minor)

**Response Time:** Best effort  
**Resolution Target:** <30 days  
**Escalation:** None  
**Communication:** Ticket system

### 2.2 Incident Categories

| Category | Description | Examples |
|----------|-------------|----------|
| **SEC** | Security Breach | Unauthorized access, data breach, malware |
| **OPS** | Operational | Outages, performance, infrastructure |
| **DATA** | Data Integrity | Data loss, corruption, backup failure |
| **COMP** | Compliance | DSGVO violation, audit finding |

---

## 3. Incident Response Team

### 3.1 Roles & Responsibilities

#### Incident Commander (IC)
- **Current:** Andy Schwarz (CISO)
- **Future:** Rotates among senior engineers

**Responsibilities:**
- Overall coordination
- Severity assessment
- Escalation decisions
- External communication
- Post-mortem ownership

#### Technical Lead
- **Current:** Andy Schwarz
- **Future:** Relevant team lead (Backend, DevOps, etc.)

**Responsibilities:**
- Technical investigation
- Root cause analysis
- Mitigation implementation
- Recovery verification

#### Communications Lead
- **Current:** Andy Schwarz
- **Future:** Customer Success / Marketing

**Responsibilities:**
- Customer communication (Status Page, Email)
- Internal stakeholder updates
- Social media (if needed)
- Press response (major incidents)

#### Scribe
- **Optional:** Dedicated person for large incidents

**Responsibilities:**
- Timeline documentation
- Action items tracking
- Slack thread summarization
- Post-mortem drafting

---

## 4. Incident Response Process

### 4.1 Phase 1: Detection & Triage

**Detection Sources:**
- Monitoring alerts (CloudWatch, Sentry)
- Security scans (Trivy, OWASP ZAP)
- User reports (Support tickets, email)
- External reports (Security researchers, customers)
- Manual discovery (Code review, testing)

**Triage Steps:**

1. **Initial Assessment** (<5 min)
   - What happened? (Symptom description)
   - When did it start? (Timestamp)
   - Impact: How many users affected?
   - Scope: Which systems/data involved?

2. **Severity Classification** (<5 min)
   - Use severity matrix (Section 2.1)
   - Err on side of caution (higher severity if uncertain)

3. **Incident Declaration** (<5 min)
   - Create incident ticket: `INC-{DATE}-{NUMBER}` (e.g., INC-20260515-001)
   - Notify IC (if not self)
   - Start Slack incident channel: `#incident-{number}`

4. **Initial Response** (<15 min for P1, <1h for P2)
   - Assemble response team
   - Begin investigation
   - Implement immediate containment (if needed)

### 4.2 Phase 2: Containment

**Goal:** Stop the incident from spreading or causing more damage

**Short-Term Containment:**

**For Security Breaches:**
- Isolate compromised systems (security group changes, Lambda concurrency=0)
- Rotate compromised credentials immediately
- Block attacker IP addresses (WAF rules)
- Disable compromised user accounts
- Snapshot systems for forensics (before changes)

**For Outages:**
- Switch to maintenance mode (if graceful degradation not possible)
- Route traffic to backup region (if DR configured)
- Scale up resources (Lambda concurrency, Aurora capacity)
- Rollback recent deployment (if suspected cause)

**For Data Incidents:**
- Stop writes to affected data (read-only mode)
- Identify last known good state
- Prevent backup overwriting (pause automated backups)

**Long-Term Containment:**
- Patch vulnerabilities
- Apply permanent fixes (not just workarounds)
- Harden systems
- Update WAF rules

### 4.3 Phase 3: Eradication

**Goal:** Remove root cause of incident

**Steps:**

1. **Root Cause Analysis** (Preliminary)
   - Analyze logs (CloudTrail, Application Logs, WAF Logs)
   - Review recent changes (Git commits, deployments, config changes)
   - Identify attack vector or failure mode

2. **Develop Fix**
   - Create fix branch: `hotfix/inc-{number}-{description}`
   - Implement fix (code, config, infrastructure)
   - Test in staging (or isolated environment)
   - Security review (if breach)

3. **Deploy Fix**
   - Deploy to affected environment(s)
   - Verify fix resolves issue
   - Monitor for recurrence

**For Security Breaches:**
- Remove backdoors, malware, unauthorized access
- Scan all systems for indicators of compromise (IOC)
- Verify no persistence mechanisms

**For Data Corruption:**
- Identify root cause (bug, hardware failure, corruption)
- Fix data integrity issues
- Validate data consistency

### 4.4 Phase 4: Recovery

**Goal:** Restore normal operations

**Steps:**

1. **System Restoration**
   - Restore from backup (if needed)
   - Bring systems back online (gradual rollout)
   - Re-enable disabled features
   - Verify functionality (smoke tests)

2. **Data Restoration**
   - Restore from last known good backup
   - Apply PITR (Point-in-Time Recovery) if available
   - Validate data integrity
   - Replay missed transactions (if possible)

3. **Service Verification**
   - Run health checks
   - Monitor error rates
   - Check key user flows
   - Verify no degradation

4. **Communications**
   - Update Status Page ("Incident Resolved")
   - Notify affected customers
   - Internal announcement (all-hands or email)

### 4.5 Phase 5: Post-Mortem

**Goal:** Learn from incident and prevent recurrence

**Timeline:** Within 5 business days after incident resolution

**Post-Mortem Meeting:**
- **Attendees:** Incident team + stakeholders
- **Duration:** 1-2 hours
- **Facilitator:** Incident Commander
- **Blameless:** Focus on process, not individuals

**Post-Mortem Document Structure:**

```markdown
# Incident Post-Mortem: INC-{NUMBER}

## Incident Summary
- **Date:** {incident date}
- **Duration:** {start - end}
- **Severity:** P1/P2/P3/P4
- **Impact:** {users affected, revenue impact, data loss}

## Timeline
| Time | Event |
|------|-------|
| 14:23 | First alert received (CloudWatch alarm) |
| 14:25 | Incident declared, IC notified |
| 14:30 | Root cause identified (bug in deployment) |
| 14:45 | Rollback initiated |
| 15:00 | Service restored, monitoring |
| 15:30 | Incident resolved |

## Root Cause
{Technical explanation of what went wrong}

## What Went Well
- Fast detection (2 minutes after symptom)
- Quick rollback decision
- Good communication

## What Went Wrong
- Missing test coverage for edge case
- No automated rollback
- Delayed customer communication (15 min)

## Action Items
| Action | Owner | Deadline | Priority |
|--------|-------|----------|----------|
| Add test for X | Andy | 2026-05-20 | P1 |
| Implement auto-rollback | Andy | 2026-06-01 | P2 |
| Update status page automation | Andy | 2026-05-25 | P1 |

## Lessons Learned
- Deploy smaller changes to reduce blast radius
- Always test edge cases before production
- Update status page immediately (don't wait for resolution)
```

**Post-Mortem Distribution:**
- Internal: All team members
- External: Customers (if requested or major impact)
- Public: Public Status Page (optional, for transparency)

---

## 5. Communication Templates

### 5.1 Status Page Update (Incident Start)

```
🔴 Investigating - {SERVICE NAME}

We are currently investigating reports of {symptom}.
Our team is working to identify the issue and will provide
updates as we have them.

Time: {TIMESTAMP} UTC
```

### 5.2 Status Page Update (Incident Progress)

```
🟡 Identified - {SERVICE NAME}

We have identified the cause: {brief description}.
Our team is working on a fix. Estimated resolution: {ETA}.

Time: {TIMESTAMP} UTC
```

### 5.3 Status Page Update (Incident Resolved)

```
🟢 Resolved - {SERVICE NAME}

This incident has been resolved. All systems are operational.
A post-mortem will be shared within 5 business days.

We apologize for the inconvenience.

Duration: {DURATION}
Time: {TIMESTAMP} UTC
```

### 5.4 Customer Email (P1 Incident)

**Subject:** [OverCloud] Incident Resolution - {DATE}

```
Dear OverCloud Customer,

We want to inform you about a service incident that occurred on {DATE}.

WHAT HAPPENED:
{Brief description of incident}

IMPACT:
- Duration: {DURATION}
- Affected users: {NUMBER} or {PERCENTAGE}
- Data loss: {YES/NO - details if yes}

RESOLUTION:
{Brief description of fix}

NEXT STEPS:
- We have implemented additional monitoring to prevent recurrence
- A detailed post-mortem will be shared within 5 business days
- If you were affected, please contact support@overcloud.io

We sincerely apologize for the disruption and are committed to
preventing similar incidents in the future.

Best regards,
The OverCloud Team
```

### 5.5 DSGVO Data Breach Notification (wenn erforderlich)

**Subject:** [URGENT] Data Breach Notification - DSGVO Art. 33/34

```
Dear {CUSTOMER / SUPERVISORY AUTHORITY},

We are writing to inform you of a data breach that occurred on {DATE}
as required under DSGVO Articles 33 and 34.

BREACH DETAILS:
- Date of breach: {DATE}
- Date of discovery: {DATE}
- Type of breach: {Confidentiality / Integrity / Availability}

DATA AFFECTED:
- Categories: {Email addresses, names, etc.}
- Number of individuals: {NUMBER}
- Severity: {HIGH / MEDIUM / LOW}

LIKELY CONSEQUENCES:
{Description of potential impact to individuals}

MEASURES TAKEN:
- Immediate: {Containment actions}
- Long-term: {Preventive measures}

MEASURES RECOMMENDED FOR INDIVIDUALS:
{Steps individuals should take, e.g., password reset}

CONTACT:
For questions, please contact: dpo@overcloud.io

Sincerely,
Andy Schwarz
CISO & Data Protection Officer (DPO)
OverCloud
```

**Timeline:**
- **Supervisory Authority (Datenschutzbehörde):** Within 72 hours of discovery
- **Affected Individuals:** Without undue delay (if high risk)

---

## 6. Runbooks

### 6.1 Runbook: Production API Down

**Symptoms:**
- Health check failing
- 5XX errors
- No response from API

**Diagnosis:**
```bash
# Check API Gateway
aws apigatewayv2 get-api --api-id {API_ID}

# Check Lambda
aws lambda get-function --function-name overcloud-prod-lambda

# Check Lambda errors
aws logs tail /aws/lambda/overcloud-prod-lambda --follow

# Check Database
aws rds describe-db-clusters --db-cluster-identifier overcloud-prod
```

**Resolution:**
```bash
# Option 1: Restart Lambda (update environment variable)
aws lambda update-function-configuration \
  --function-name overcloud-prod-lambda \
  --environment Variables={RESTART=true}

# Option 2: Rollback deployment
git revert HEAD
git push origin main
# Wait for GitHub Actions deployment

# Option 3: Scale up Aurora
aws rds modify-db-cluster \
  --db-cluster-identifier overcloud-prod \
  --serverless-v2-scaling-configuration MinCapacity=2,MaxCapacity=16
```

### 6.2 Runbook: Suspected Data Breach

**Symptoms:**
- Unusual CloudTrail activity
- GuardDuty findings
- Unauthorized API calls
- Customer reports unauthorized access

**Immediate Actions (within 15 minutes):**

1. **Contain:**
   ```bash
   # Rotate all credentials immediately
   aws secretsmanager rotate-secret --secret-id prod/db/password
   
   # Disable compromised IAM user
   aws iam delete-login-profile --user-name {USERNAME}
   aws iam delete-access-key --access-key-id {KEY} --user-name {USERNAME}
   
   # Block attacker IP in WAF
   # (Add to WAF IP block list)
   ```

2. **Investigate:**
   ```bash
   # Review CloudTrail logs (last 24h)
   aws cloudtrail lookup-events \
     --lookup-attributes AttributeKey=Username,AttributeValue={USER} \
     --max-results 100
   
   # Review GuardDuty findings
   aws guardduty list-findings --detector-id {DETECTOR_ID}
   
   # Check for data exfiltration (S3, Database)
   aws cloudtrail lookup-events \
     --lookup-attributes AttributeKey=EventName,AttributeValue=GetObject
   ```

3. **Assess:**
   - What data was accessed?
   - Was data exfiltrated?
   - How many accounts compromised?
   - DSGVO notification required? (PII breach → yes)

4. **Notify:**
   - CISO immediately
   - Datenschutzbehörde within 72h (if PII breach)
   - Affected customers (if high risk)

### 6.3 Runbook: Database Restore from Backup

**When to use:**
- Data corruption
- Accidental deletion
- Ransomware

**Steps:**

1. **Identify restore point:**
   ```bash
   # List available snapshots
   aws rds describe-db-cluster-snapshots \
     --db-cluster-identifier overcloud-prod
   
   # For PITR, use timestamp: 2026-05-15T14:30:00Z
   ```

2. **Create new cluster from snapshot:**
   ```bash
   aws rds restore-db-cluster-from-snapshot \
     --db-cluster-identifier overcloud-prod-restore \
     --snapshot-identifier {SNAPSHOT_ID} \
     --engine aurora-postgresql
   ```

3. **Or use PITR:**
   ```bash
   aws rds restore-db-cluster-to-point-in-time \
     --source-db-cluster-identifier overcloud-prod \
     --db-cluster-identifier overcloud-prod-restore \
     --restore-to-time 2026-05-15T14:30:00Z
   ```

4. **Validate restored data:**
   ```bash
   # Connect to restored cluster
   psql -h {RESTORE_CLUSTER_ENDPOINT} -U overcloud_admin -d overcloud
   
   # Verify data integrity
   SELECT COUNT(*) FROM users;
   SELECT * FROM users WHERE created_at > '2026-05-15';
   ```

5. **Switch application to restored cluster:**
   ```bash
   # Update Secrets Manager with new endpoint
   aws secretsmanager update-secret \
     --secret-id prod/db/endpoint \
     --secret-string '{"endpoint": "{NEW_ENDPOINT}"}'
   
   # Restart Lambda to pick up new config
   # (or wait for automatic refresh)
   ```

---

## 7. Metrics & Monitoring

### 7.1 Incident Metrics

Track monthly:
- **Incident Count** (by severity)
- **MTTR** (Mean Time to Resolve) - Target: <4h for P1, <24h for P2
- **MTTD** (Mean Time to Detect) - Target: <5min for P1
- **False Positives** (alerts that weren't incidents)
- **Recurrence Rate** (same incident within 30 days)

### 7.2 SLA Compliance

| Metric | Target | Measurement |
|--------|--------|-------------|
| P1 Response Time | <15 min | 95th percentile |
| P1 Resolution Time | <4 hours | 90th percentile |
| P2 Response Time | <1 hour | 95th percentile |
| P2 Resolution Time | <24 hours | 90th percentile |
| Uptime | 99.9% | Monthly |

---

## 8. Training & Drills

### 8.1 Incident Response Training

**Onboarding (new team members):**
- Incident Response Plan overview
- Severity classification
- Communication protocols
- Tool access (Slack, AWS, GitHub)

**Annual Refresher:**
- Plan updates
- New tools
- Lessons from recent incidents

### 8.2 Incident Drills

**Frequency:** Quartalsweise

**Drill Types:**
- **Tabletop Exercise:** Walk through scenario (no actual systems)
- **Simulation:** Execute in staging environment
- **Red Team Exercise:** External security team attacks (annual)

**Example Scenarios:**
- Data breach (credentials leaked)
- DDoS attack (WAF overwhelmed)
- Database failure (restore from backup)
- Ransomware (containment + recovery)

**Drill Outcomes:**
- Drill report (what went well / wrong)
- Action items for plan improvement
- Team feedback

---

## 9. Appendices

### Appendix A: Contact List

| Role | Name | Phone | Email | Slack |
|------|------|-------|-------|-------|
| CISO | Andy Schwarz | +49 XXX | andy@overcloud.io | @andy |
| AWS Support | - | - | - | Enterprise Support Portal |
| External Security | - | - | security@example.com | - |

### Appendix B: Tool Access

| Tool | Purpose | Access |
|------|---------|--------|
| AWS Console | Infrastructure | andy@overcloud.io (MFA) |
| GitHub | Code, CI/CD | github.com/AndySchw |
| Slack | Communication | overcloud.slack.com |
| Status Page | Customer comms | status.overcloud.io |
| Sentry | Error tracking | sentry.io/overcloud |

### Appendix C: Compliance Requirements

**DSGVO (Art. 33/34):**
- Data breach notification to authority: 72 hours
- Data breach notification to individuals: Without undue delay (if high risk)

**ISO 27001 (Clause 16):**
- Incident management process documented
- Incidents categorized and logged
- Post-mortem for learning

**SOC 2 (CC7.3, CC7.4):**
- Incident detection mechanisms
- Incident response procedures
- Incident tracking and resolution

---

**Document Owner:** Andy Schwarz (CISO)  
**Last Updated:** 2026-05-15  
**Next Review:** 2027-05-15
