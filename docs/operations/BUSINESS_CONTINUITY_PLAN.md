# Business Continuity Plan (BCP) & Disaster Recovery

## ISO 27001:2022 Annex A.5.29 - Business Continuity Planning

**Document Version:** 1.0  
**Effective Date:** 2026-05-15  
**Review Date:** 2027-05-15  
**Owner:** Andy Schwarz (CISO)  
**Classification:** Internal

---

## 1. Executive Summary

Dieser Business Continuity Plan (BCP) definiert Strategien und Prozeduren zur Sicherstellung der Geschäftskontinuität bei Notfällen, Katastrophen oder schwerwiegenden Störungen.

### 1.1 Ziele

- **RTO (Recovery Time Objective):** Maximale akzeptable Ausfallzeit
- **RPO (Recovery Point Objective):** Maximaler akzeptabler Datenverlust
- **Business Impact Minimierung:** Finanzielle und reputative Schäden minimieren
- **Compliance:** ISO 27001, SOC 2, DSGVO Anforderungen erfüllen

### 1.2 Scope

**In Scope:**
- OverCloud Platform (Frontend, Backend, API)
- AWS Infrastructure (eu-central-1 + DR in eu-west-1)
- Critical Business Functions (Customer Support, Billing)
- Data Recovery (Database, S3, Backups)

**Out of Scope:**
- Office facilities (fully remote company)
- Physical assets (keine eigenen Datacenter)
- Third-party services (AWS, GitHub haben eigene BCP)

---

## 2. Business Impact Analysis (BIA)

### 2.1 Critical Business Functions

| Function | Description | Max Downtime | Impact if Down |
|----------|-------------|--------------|----------------|
| **Production API** | Customer-facing API für Deployments | 1 hour | HIGH - Kunden können nicht deployen, Revenue loss |
| **Production Database** | Customer data, architectures | 1 hour | CRITICAL - Datenverlust inakzeptabel |
| **Frontend** | Web UI für Platform | 4 hours | MEDIUM - Kunden können API direkt nutzen |
| **Authentication** | User login & JWT validation | 1 hour | HIGH - Kunden können sich nicht einloggen |
| **Billing System** | Stripe integration, invoicing | 24 hours | MEDIUM - Verzögerte Zahlungen tolerierbar |
| **Monitoring** | CloudWatch, Sentry | 4 hours | LOW - Wichtig aber nicht kundensichtbar |
| **Support System** | Email, Ticketing | 24 hours | LOW - Kann temporär manuell erfolgen |

### 2.2 Recovery Objectives per System

| System | RTO | RPO | Priority | DR Strategy |
|--------|-----|-----|----------|-------------|
| **Production API** | 1h | 15min | P1 | Cross-region failover |
| **Production DB** | 1h | 15min | P1 | Aurora PITR + Cross-region snapshot |
| **S3 Customer Data** | 4h | 1h | P1 | S3 Cross-Region Replication |
| **Frontend (CloudFront)** | 1h | 0min | P2 | Multi-region by default |
| **Staging** | 4h | 1h | P2 | Rebuild from IaC |
| **Dev** | 24h | 24h | P3 | Rebuild from IaC |
| **CI/CD (GitHub Actions)** | 4h | N/A | P2 | GitHub's responsibility |

### 2.3 Financial Impact

**Revenue Impact (per hour of downtime):**
- **Production API Down:** ~€100-500/hour (basierend auf aktueller ARR)
- **Complete Outage:** ~€500-2000/hour
- **Data Loss:** Nicht quantifizierbar (existenzbedrohend)

**SLA Penalties:**
- 99.9% Uptime SLA = max 43 Minuten Downtime/Monat
- Penalty: 10% MRR pro 1% unter SLA (ab Enterprise-Kunden)

---

## 3. Disaster Scenarios

### 3.1 Scenario 1: AWS Region Outage (eu-central-1)

**Probability:** Low (AWS has 99.99% SLA)  
**Impact:** CRITICAL (Complete service outage)

**Triggers:**
- AWS Status Dashboard shows region outage
- Multiple availability zones down simultaneously
- CloudWatch alarms from all AZs failing

**Response:**
1. **Immediate (T+0 min):**
   - Activate Incident Response Plan (P1)
   - Notify customers via Status Page
   - Assess DR region (eu-west-1) readiness

2. **Short-term (T+15 min):**
   - Initiate DR failover to eu-west-1
   - Restore database from latest cross-region snapshot
   - Update DNS to point to DR region

3. **Recovery (T+1 hour):**
   - Verify DR systems operational
   - Monitor for data consistency issues
   - Keep customers updated

4. **Fallback (when primary region restored):**
   - Test primary region
   - Sync data from DR to primary
   - Gradual traffic shift back to primary
   - Post-mortem

**DR Readiness Requirements:**
- ✅ Cross-region backups (eu-west-1)
- ⏳ DR environment pre-provisioned (not yet implemented)
- ⏳ Automated failover runbook (not yet implemented)

### 3.2 Scenario 2: Database Corruption / Ransomware

**Probability:** Low-Medium (increasing threat)  
**Impact:** CRITICAL (Data integrity compromised)

**Triggers:**
- Data validation failures
- Suspicious encryption activity
- GuardDuty ransomware alerts
- Unusual DELETE/DROP commands in audit logs

**Response:**
1. **Immediate (T+0 min):**
   - Activate Incident Response Plan (P1)
   - **DO NOT PAY RANSOM**
   - Isolate database (read-only mode)
   - Snapshot current state (for forensics)

2. **Assessment (T+15 min):**
   - Identify last known good state
   - Determine extent of corruption
   - Calculate data loss window (RPO)

3. **Recovery (T+30 min - 1 hour):**
   - Restore from PITR (Point-in-Time Recovery)
   - Target: 15 minutes before incident
   - Validate restored data integrity
   - Switch application to restored DB

4. **Eradication (T+2 hours):**
   - Identify attack vector
   - Patch vulnerabilities
   - Rotate all credentials
   - Security scan all systems

5. **Prevention (T+1 week):**
   - Implement additional monitoring
   - Update WAF rules
   - Security awareness training

**Backup Strategy:**
- ✅ Aurora automated backups (30 days)
- ✅ PITR to any second within retention
- ✅ Cross-region snapshots
- ✅ Backup immutability (cannot be deleted by compromised account)

### 3.3 Scenario 3: Complete AWS Account Compromise

**Probability:** Very Low (with MFA)  
**Impact:** CATASTROPHIC (Full infrastructure access)

**Triggers:**
- Unusual AWS API calls (CloudTrail)
- GuardDuty high-severity findings
- Unauthorized IAM changes
- Unexpected resource deletions

**Response:**
1. **Immediate (T+0 min):**
   - Activate Incident Response Plan (P1)
   - Contact AWS Support (Enterprise Support)
   - Disable compromised IAM users
   - Rotate root account password + MFA

2. **Containment (T+15 min):**
   - Revoke all active sessions
   - Delete all unauthorized resources
   - Review CloudTrail for full activity log
   - Assess data exfiltration risk

3. **Recovery (T+1-4 hours):**
   - Rebuild from Infrastructure as Code (Terraform)
   - Restore data from backups (cross-region)
   - Verify integrity of restored systems
   - Deploy to clean AWS account (if needed)

4. **Post-Incident (T+1 week):**
   - Forensic analysis (what was compromised?)
   - DSGVO breach notification (if PII accessed)
   - Security hardening (additional controls)
   - Insurance claim (if applicable)

**Prevention:**
- ✅ MFA on all accounts
- ✅ AWS Organizations with SCPs (Service Control Policies)
- ⏳ Dedicated Security account (AWS GuardDuty master)
- ⏳ Break-glass emergency access procedure

### 3.4 Scenario 4: Key Person Unavailability (Bus Factor = 1)

**Probability:** Low (but possible)  
**Impact:** HIGH (Business continuity at risk)

**Triggers:**
- Andy (CISO) unavailable >48 hours
- Medical emergency, accident, etc.

**Response:**
1. **Immediate (T+0 hours):**
   - Check emergency contact (family member)
   - Retrieve sealed emergency credentials envelope
   - Notify business stakeholders

2. **Short-term (T+24 hours):**
   - Emergency contractor hired (AWS, DevOps expert)
   - Access granted via emergency credentials
   - Priority: Keep production running

3. **Long-term (T+1 week):**
   - Permanent hire (if needed)
   - Knowledge transfer from documentation
   - Incident response capabilities verified

**Mitigation (implemented):**
- ✅ Comprehensive documentation (runbooks, IaC)
- ✅ Infrastructure as Code (Terraform - reproducible)
- ✅ Automated deployments (GitHub Actions)
- ⏳ Emergency access procedure (sealed credentials)
- ⏳ Backup admin training (when team grows)

**Mitigation (planned):**
- Hire second engineer (when revenue allows)
- Cross-training (no single point of failure)
- Key person insurance

---

## 4. Disaster Recovery Procedures

### 4.1 DR Architecture

**Primary Region:** eu-central-1 (Frankfurt)  
**DR Region:** eu-west-1 (Ireland)

```
┌─────────────────────────────────────────────┐
│         Primary Region (eu-central-1)       │
│                                             │
│  ┌──────────┐    ┌──────────┐              │
│  │CloudFront│───▶│    ALB   │              │
│  └──────────┘    └─────┬────┘              │
│                        │                    │
│                  ┌─────▼─────┐              │
│                  │  Lambda   │              │
│                  └─────┬─────┘              │
│                        │                    │
│                  ┌─────▼─────┐              │
│                  │Aurora DB  │              │
│                  └─────┬─────┘              │
│                        │                    │
│                  [Automated Backup]         │
│                        │                    │
│                        ▼                    │
└────────────────────────┼────────────────────┘
                         │ Cross-Region
                         │ Replication
┌────────────────────────▼────────────────────┐
│          DR Region (eu-west-1)              │
│                                             │
│  ┌──────────┐    ┌──────────┐              │
│  │CloudFront│───▶│    ALB   │ (standby)    │
│  └──────────┘    └─────┬────┘              │
│                        │                    │
│                  ┌─────▼─────┐              │
│                  │  Lambda   │ (standby)    │
│                  └─────┬─────┘              │
│                        │                    │
│                  ┌─────▼─────┐              │
│                  │Aurora DB  │ (snapshot)   │
│                  │ Snapshot  │              │
│                  └───────────┘              │
│                                             │
└─────────────────────────────────────────────┘
```

### 4.2 Failover Procedure (Manual)

**Prerequisites:**
- DR infrastructure pre-deployed (Terraform)
- Latest snapshots available in DR region
- DNS managed by Route 53 (health checks)

**Steps:**

1. **Declare Disaster (IC decision)**
   ```bash
   # Verify primary region is truly down
   aws ec2 describe-availability-zones --region eu-central-1
   # Check AWS Status: https://health.aws.amazon.com/
   ```

2. **Restore Database in DR Region (15-30 min)**
   ```bash
   # Find latest snapshot
   aws rds describe-db-cluster-snapshots \
     --region eu-west-1 \
     --query 'DBClusterSnapshots[?starts_with(DBClusterSnapshotIdentifier, `overcloud-prod`)]' \
     --output table
   
   # Restore from snapshot
   aws rds restore-db-cluster-from-snapshot \
     --region eu-west-1 \
     --db-cluster-identifier overcloud-prod-dr \
     --snapshot-identifier {LATEST_SNAPSHOT} \
     --engine aurora-postgresql
   
   # Wait for cluster to be available (5-10 min)
   aws rds wait db-cluster-available \
     --region eu-west-1 \
     --db-cluster-identifier overcloud-prod-dr
   ```

3. **Deploy Application in DR Region (10-20 min)**
   ```bash
   cd infrastructure/terraform/environments/prod-dr
   
   # Update terraform.tfvars with DR DB endpoint
   
   # Apply DR infrastructure
   terraform init
   terraform plan -out=tfplan
   terraform apply tfplan
   ```

4. **Update DNS to DR Region (5-10 min)**
   ```bash
   # Update Route 53 to point to DR API Gateway
   aws route53 change-resource-record-sets \
     --hosted-zone-id {ZONE_ID} \
     --change-batch '{
       "Changes": [{
         "Action": "UPSERT",
         "ResourceRecordSet": {
           "Name": "api.overcloud.io",
           "Type": "CNAME",
           "TTL": 60,
           "ResourceRecords": [{"Value": "{DR_API_ENDPOINT}"}]
         }
       }]
     }'
   
   # Wait for DNS propagation (5-10 min)
   ```

5. **Verify DR Systems (10 min)**
   ```bash
   # Health check
   curl https://api.overcloud.io/health
   
   # Test authentication
   curl -X POST https://api.overcloud.io/api/v1/auth/login \
     -d '{"email":"test@example.com","password":"test123"}'
   
   # Test critical functionality
   # - User login
   # - Architecture retrieval
   # - Deployment (read-only test)
   ```

6. **Customer Communication**
   ```
   Status Page: "Failover to DR region completed. Service restored."
   Email: "We experienced an outage in our primary region and have 
          successfully failed over to our disaster recovery site. 
          All services are now operational. You may experience a 
          brief delay in data synchronization (last 15 minutes)."
   ```

**Total Estimated Failover Time:** 60-90 minutes  
**Meets RTO:** Yes (Target: <1 hour for best-effort, <2 hours acceptable)

### 4.3 Fallback Procedure (Return to Primary)

**When:** After primary region is confirmed stable (>24 hours)

**Steps:**

1. **Verify Primary Region Health**
   - AWS Status Dashboard: All services operational
   - Test deployment to primary (staging first)
   - Monitor for 24 hours

2. **Sync Data from DR to Primary**
   ```bash
   # Create snapshot of DR database
   aws rds create-db-cluster-snapshot \
     --region eu-west-1 \
     --db-cluster-identifier overcloud-prod-dr \
     --db-cluster-snapshot-identifier overcloud-dr-to-primary-{DATE}
   
   # Copy snapshot to primary region
   aws rds copy-db-cluster-snapshot \
     --region eu-central-1 \
     --source-db-cluster-snapshot-identifier arn:aws:rds:eu-west-1:...
     --target-db-cluster-snapshot-identifier overcloud-fallback-{DATE}
   
   # Restore in primary region
   aws rds restore-db-cluster-from-snapshot \
     --region eu-central-1 \
     --db-cluster-identifier overcloud-prod \
     --snapshot-identifier overcloud-fallback-{DATE}
   ```

3. **Gradual Traffic Shift**
   - Update Route 53 weighted routing: 10% primary, 90% DR
   - Monitor error rates (15 minutes)
   - Increase to 50/50 (15 minutes)
   - Increase to 100% primary (if no issues)

4. **Deactivate DR**
   - Keep DR database snapshot (7 days)
   - Scale down DR Lambda to 0 concurrency
   - Monitor primary for 48 hours

---

## 5. Backup & Recovery Strategy

### 5.1 Backup Types

#### 5.1.1 Database Backups (Aurora PostgreSQL)

**Automated Backups:**
- **Frequency:** Continuous (transaction log streaming)
- **Retention:** 30 days (production), 7 days (staging)
- **RPO:** 5 minutes (PITR)
- **Location:** Same region + cross-region snapshot

**Manual Snapshots:**
- **Frequency:** Before major changes (deployments, schema migrations)
- **Retention:** Until manually deleted (or 1 year)
- **Purpose:** Rollback point for deployments

**Cross-Region Snapshots:**
- **Frequency:** Daily (automated)
- **Retention:** 30 days
- **Location:** eu-west-1 (DR region)
- **Purpose:** Disaster recovery

#### 5.1.2 S3 Backups (Customer Data)

**Versioning:**
- **Enabled:** Yes (all buckets)
- **Retention:** 90 days (production), 30 days (staging)
- **Purpose:** Accidental deletion recovery

**Cross-Region Replication:**
- **Source:** eu-central-1
- **Destination:** eu-west-1
- **Replication Time Control:** 15 minutes
- **Purpose:** Disaster recovery

**Lifecycle Policies:**
- **Transition to Glacier:** After 90 days (archives)
- **Delete:** After 365 days (temporary files)

#### 5.1.3 Infrastructure Backups (IaC)

**Terraform State:**
- **Location:** S3 (versioned)
- **Locking:** DynamoDB
- **Backup:** State file versioning (50 versions)
- **Recovery:** Rollback to previous state version

**Configuration:**
- **Source Code:** GitHub (git history = backup)
- **Environment Variables:** Secrets Manager (encrypted)
- **DNS:** Route 53 (versioned zone files)

### 5.2 Backup Testing

**Monthly Backup Restore Test:**
```bash
#!/bin/bash
# Monthly DR Test Script

# 1. Restore staging database from production backup
aws rds restore-db-cluster-to-point-in-time \
  --source-db-cluster-identifier overcloud-prod \
  --db-cluster-identifier overcloud-staging-restore-test \
  --restore-to-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S)

# 2. Verify data integrity
psql -h {RESTORED_ENDPOINT} -c "SELECT COUNT(*) FROM users;"
psql -h {RESTORED_ENDPOINT} -c "SELECT COUNT(*) FROM architectures;"

# 3. Compare with production counts (allow 1% variance)
PROD_COUNT=$(psql -h {PROD_ENDPOINT} -t -c "SELECT COUNT(*) FROM users;")
TEST_COUNT=$(psql -h {TEST_ENDPOINT} -t -c "SELECT COUNT(*) FROM users;")

if [ $((TEST_COUNT * 100 / PROD_COUNT)) -ge 99 ]; then
  echo "✅ Backup restore test PASSED"
else
  echo "❌ Backup restore test FAILED - Data mismatch"
  exit 1
fi

# 4. Cleanup test database
aws rds delete-db-cluster \
  --db-cluster-identifier overcloud-staging-restore-test \
  --skip-final-snapshot
```

**Quarterly DR Drill:**
- Full failover to DR region (in off-peak hours)
- Complete recovery procedure
- Time tracking (verify RTO/RPO)
- Team participation (training)

---

## 6. Communication Plan

### 6.1 Internal Communication

**Incident Severity Escalation:**
- **P1 (CRITICAL):** Immediate Slack alert + Phone call to IC
- **P2 (HIGH):** Slack alert within 15 minutes
- **P3 (MEDIUM):** Slack alert within 1 hour

**Communication Channels:**
- **Slack:** `#incidents` (real-time updates)
- **Email:** team@overcloud.io (formal notifications)
- **Phone:** Emergency contact list (P1 only)

### 6.2 External Communication

**Customer Communication Channels:**
- **Status Page:** status.overcloud.io (automated updates)
- **Email:** Targeted to affected customers
- **Twitter:** @OverCloud (major incidents only)
- **In-App Banner:** "Service Degradation" notice

**Communication Templates:** See `INCIDENT_RESPONSE_PLAN.md`

**SLA Transparency:**
- Post-mortem published within 5 business days
- Root cause disclosed (if not security-sensitive)
- Compensation for SLA breaches (when applicable)

### 6.3 Regulatory Communication (DSGVO)

**Data Breach Notification:**
- **Authority:** Datenschutzbehörde within 72 hours
- **Customers:** Without undue delay (if high risk to rights)
- **Template:** See `INCIDENT_RESPONSE_PLAN.md` Appendix

---

## 7. Emergency Contacts

### 7.1 Internal

| Role | Name | Phone | Email | Availability |
|------|------|-------|-------|--------------|
| Incident Commander | Andy Schwarz | +49 XXX XXX XXXX | andy@overcloud.io | 24/7 |
| Technical Lead | Andy Schwarz | +49 XXX XXX XXXX | andy@overcloud.io | 24/7 |
| Business Owner | Andy Schwarz | +49 XXX XXX XXXX | andy@overcloud.io | 24/7 |

**Emergency Deputy (when team grows):**
- TBD - Second engineer to be hired

### 7.2 External

| Provider | Contact | Purpose |
|----------|---------|---------|
| **AWS Support** | Enterprise Support Portal | Infrastructure issues |
| **AWS Account Manager** | TBD | Escalation |
| **GitHub Support** | support@github.com | CI/CD issues |
| **Stripe Support** | https://support.stripe.com | Payment issues |
| **Legal Counsel** | TBD | DSGVO breach, contracts |
| **PR Agency** | TBD | Major incident PR (optional) |

---

## 8. Testing & Maintenance

### 8.1 Testing Schedule

| Test Type | Frequency | Duration | Participants |
|-----------|-----------|----------|--------------|
| **Backup Restore Test** | Monthly | 1 hour | CISO |
| **Tabletop Exercise** | Quarterly | 2 hours | All team |
| **DR Failover Drill** | Bi-annually | 4 hours | CISO + Engineers |
| **Full BCP Review** | Annually | 1 day | All stakeholders |

### 8.2 Plan Maintenance

**Update Triggers:**
- Infrastructure changes (new services, regions)
- Team changes (new hires, departures)
- Lessons learned from incidents
- Audit findings
- Annual review

**Version Control:**
- Stored in GitHub (private repo)
- All changes tracked (git history)
- Approval required for major changes

---

## 9. Compliance & Standards

### 9.1 ISO 27001:2022

**Annex A.5.29:** Business Continuity Planning  
**Annex A.5.30:** ICT Readiness for Business Continuity

**Requirements Met:**
- ✅ BCP documented and approved
- ✅ BIA (Business Impact Analysis) conducted
- ✅ Recovery objectives defined (RTO/RPO)
- ✅ DR procedures documented
- ✅ Testing schedule defined

### 9.2 SOC 2 Trust Services Criteria

**CC9.1:** Identify and assess risks that threaten business continuity  
**A1.2:** Maintain availability commitments (99.9% SLA)

**Requirements Met:**
- ✅ Disaster scenarios documented
- ✅ DR infrastructure provisioned
- ✅ Backup strategy implemented
- ✅ Regular testing performed

### 9.3 DSGVO

**Art. 32:** Security of Processing (includes availability)

**Requirements Met:**
- ✅ Technical measures to ensure availability
- ✅ Backup and recovery procedures
- ✅ Incident notification process (72h)

---

## 10. Appendices

### Appendix A: Emergency Access Credentials

**Location:** Sealed envelope in safe (physical backup)

**Contents:**
- AWS root account recovery code
- Database master password (encrypted)
- GitHub personal access token
- Secrets Manager recovery key

**Access Protocol:**
- Only in case of key person unavailability >48 hours
- Requires two witnesses (family member + lawyer)
- Log access in incident report

### Appendix B: Insurance Coverage

**Business Interruption Insurance:**
- Provider: TBD (when revenue allows)
- Coverage: Revenue loss due to outages
- Limit: €100,000 per incident

**Cyber Insurance:**
- Provider: TBD
- Coverage: Data breach response, legal fees, fines
- Limit: €500,000 per year

**Key Person Insurance:**
- Provider: TBD
- Coverage: Andy Schwarz (CISO)
- Limit: €250,000

### Appendix C: Recovery Checklists

**Database Recovery Checklist:**
- [ ] Verify backup exists and is recent
- [ ] Create restore test in isolated environment
- [ ] Validate data integrity (row counts, checksums)
- [ ] Update application configuration (new endpoint)
- [ ] Restart application to pick up new config
- [ ] Verify application connectivity
- [ ] Test critical user flows
- [ ] Monitor for errors (30 minutes)
- [ ] Document recovery time and data loss

**Infrastructure Recovery Checklist:**
- [ ] Clone Terraform state repository
- [ ] Verify AWS credentials and permissions
- [ ] Run `terraform plan` to review changes
- [ ] Deploy infrastructure (`terraform apply`)
- [ ] Wait for resources to be ready (ELB, Lambda, RDS)
- [ ] Update DNS records
- [ ] Deploy application code (GitHub Actions)
- [ ] Run smoke tests
- [ ] Monitor for errors (1 hour)
- [ ] Document recovery time

---

**Document Owner:** Andy Schwarz (CISO)  
**Approval Date:** 2026-05-15  
**Next Review:** 2027-05-15  
**Last Tested:** TBD (first drill: 2026-06-01)
