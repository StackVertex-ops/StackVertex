# Information Security Risk Assessment

## ISO 27001:2022 Clause 6.1.2 - Risk Assessment

**Document Version:** 1.0  
**Assessment Date:** 2026-05-15  
**Next Review:** 2027-05-15  
**Assessor:** Andy Schwarz (CISO)  
**Classification:** Internal

---

## 1. Risk Assessment Methodology

### 1.1 Risk Scoring Formula

```
Risk Score = Impact × Likelihood
```

### 1.2 Impact Scale (1-5)

| Level | Description | Business Impact |
|-------|-------------|-----------------|
| **5 - Catastrophic** | Business-ending | Data breach, total outage >24h, bankruptcy |
| **4 - Major** | Severe disruption | Revenue loss >€50k, compliance violation, customer churn |
| **3 - Moderate** | Significant impact | Revenue loss €10-50k, reputation damage, service degradation |
| **2 - Minor** | Limited impact | Revenue loss <€10k, minor customer complaints |
| **1 - Negligible** | Minimal impact | Internal inconvenience, no customer impact |

### 1.3 Likelihood Scale (1-5)

| Level | Description | Probability | Frequency |
|-------|-------------|-------------|-----------|
| **5 - Almost Certain** | Will occur | >80% | Monthly |
| **4 - Likely** | Probable | 60-80% | Quarterly |
| **3 - Possible** | Could happen | 40-60% | Yearly |
| **2 - Unlikely** | Improbable | 20-40% | Every 2-5 years |
| **1 - Rare** | Very unlikely | <20% | Every 5+ years |

### 1.4 Risk Levels

```
Risk Matrix:
Likelihood
5 │  5   10   15   20   25  ← CRITICAL
4 │  4    8   12   16   20  ← HIGH
3 │  3    6    9   12   15  ← MEDIUM
2 │  2    4    6    8   10  ← LOW
1 │  1    2    3    4    5  ← LOW
  └─────────────────────────
    1    2    3    4    5
         Impact
```

**Risk Treatment Thresholds:**
- **25-16 (CRITICAL):** Immediate action required (within 7 days)
- **15-11 (HIGH):** Mitigate within 30 days
- **10-6 (MEDIUM):** Mitigate within 90 days or monitor
- **5-1 (LOW):** Accept or monitor

---

## 2. Risk Register

### Risk ID Format
`RISK-[CATEGORY]-[NUMBER]` (e.g., RISK-SEC-001)

**Categories:**
- **SEC:** Security
- **OPS:** Operations
- **COMP:** Compliance
- **BUS:** Business
- **TECH:** Technical

---

## 3. Identified Risks

### RISK-SEC-001: Unauthorized Access to Production Systems

**Asset:** Production AWS Account, Database, S3 Buckets  
**Threat:** External Attacker, Insider Threat  
**Vulnerability:** Weak credentials, missing MFA  

**Impact:** 5 (Catastrophic - Data Breach, DSGVO Violation)  
**Likelihood:** 3 (Possible - Common attack vector)  
**Risk Score:** **15 (HIGH)**

**Current Controls:**
- AWS IAM with password policy (16+ chars)
- GitHub 2FA enabled
- Secrets Manager for credentials

**Gaps:**
- ❌ MFA not enforced on AWS root account
- ❌ No hardware tokens (YubiKey)
- ❌ No privileged access management (PAM)

**Treatment Plan:**
- ✅ **Action:** Enable MFA on all AWS accounts (root + IAM users)
- ✅ **Action:** Enforce 2FA on GitHub Organization
- ⏳ **Action:** Implement Session Manager instead of SSH (Deadline: Q3 2026)
- ⏳ **Action:** Hardware tokens for production access (Deadline: Q4 2026)

**Residual Risk (after treatment):** 6 (MEDIUM - Impact 5, Likelihood 1-2)

---

### RISK-SEC-002: DDoS Attack on Production API

**Asset:** API Gateway, Lambda Functions, CloudFront  
**Threat:** DDoS Attacker (motivated competitor, botnet)  
**Vulnerability:** No rate limiting (before WAF implementation)

**Impact:** 4 (Major - Revenue loss, SLA breach)  
**Likelihood:** 4 (Likely - Common for SaaS)  
**Risk Score:** **16 (CRITICAL)**

**Current Controls:**
- ✅ AWS Shield Standard (automatic, Layer 3/4)
- ✅ CloudFront WAF with rate limiting (2000 req/5min)
- ✅ AWS Auto-Scaling (Lambda, Aurora Serverless)

**Gaps:**
- ⏳ Shield Advanced not enabled (expensive: $3000/month)
- ⏳ No DDoS response playbook

**Treatment Plan:**
- ✅ **Action:** WAF enabled with rate limiting (COMPLETED - Phase 1.3)
- ✅ **Action:** Bot Control enabled in prod (COMPLETED - Phase 1.3)
- ⏳ **Action:** DDoS response playbook (Deadline: Q2 2026)
- ❌ **Decision:** Shield Advanced NOT implemented (cost > benefit for startup)

**Residual Risk (after treatment):** 8 (MEDIUM - Impact 4, Likelihood 2)

---

### RISK-SEC-003: SQL Injection or Code Injection

**Asset:** Backend API, Database  
**Threat:** External Attacker  
**Vulnerability:** Missing input validation, unsafe database queries

**Impact:** 5 (Catastrophic - Data breach, data manipulation)  
**Likelihood:** 2 (Unlikely - Mitigated by ORM, WAF)  
**Risk Score:** **10 (MEDIUM)**

**Current Controls:**
- ✅ SQLAlchemy ORM (parameterized queries)
- ✅ Pydantic input validation
- ✅ WAF SQL Injection Rules
- ✅ OWASP ZAP scanning (weekly)

**Gaps:**
- ⏳ No static code analysis (SAST)
- ⏳ No manual penetration testing

**Treatment Plan:**
- ✅ **Action:** WAF SQLi protection (COMPLETED - Phase 1.3)
- ⏳ **Action:** SAST integration (SonarQube or Snyk) (Deadline: Q3 2026)
- ⏳ **Action:** Annual penetration test (Deadline: Q4 2026)

**Residual Risk (after treatment):** 5 (LOW - Impact 5, Likelihood 1)

---

### RISK-SEC-004: Secrets Leak in Git Repository

**Asset:** AWS Keys, Database Passwords, API Tokens  
**Threat:** Accidental commit to public repo  
**Vulnerability:** Developers commit secrets by mistake

**Impact:** 5 (Catastrophic - Full AWS account compromise)  
**Likelihood:** 3 (Possible - Common developer mistake)  
**Risk Score:** **15 (HIGH)**

**Current Controls:**
- ✅ Gitleaks scanning (CI/CD + pre-commit hook available)
- ✅ .gitignore for .env files
- ✅ GitHub Secret Scanning (automatic)

**Gaps:**
- ⏳ Pre-commit hooks not mandatory (developers must install)
- ⏳ No automated secret rotation

**Treatment Plan:**
- ✅ **Action:** Gitleaks in CI/CD (COMPLETED - Phase 2.1)
- ⏳ **Action:** Enforce pre-commit hooks (Deadline: Q2 2026)
- ⏳ **Action:** Automated secret rotation (AWS Secrets Manager) (Deadline: Q3 2026)
- ⏳ **Action:** Security awareness training (Deadline: Q2 2026)

**Residual Risk (after treatment):** 5 (LOW - Impact 5, Likelihood 1)

---

### RISK-OPS-001: Production Database Failure / Data Loss

**Asset:** Aurora PostgreSQL Database  
**Threat:** Hardware failure, human error (DROP TABLE), ransomware  
**Vulnerability:** No backups or insufficient backup testing

**Impact:** 5 (Catastrophic - Complete data loss, business shutdown)  
**Likelihood:** 2 (Unlikely - AWS reliability + backups)  
**Risk Score:** **10 (MEDIUM)**

**Current Controls:**
- ✅ Aurora automated backups (30 days retention)
- ✅ PITR (Point-in-Time Recovery)
- ✅ Cross-region backups (eu-west-1)
- ✅ AWS Backup Vault

**Gaps:**
- ⏳ Backup restore testing not performed
- ⏳ No chaos engineering (failure simulation)

**Treatment Plan:**
- ✅ **Action:** Automated backups (COMPLETED - Phase 1.2)
- ⏳ **Action:** Monthly backup restore test (Deadline: Q2 2026)
- ⏳ **Action:** DR drill (full region failover) (Deadline: Q3 2026)

**Residual Risk (after treatment):** 5 (LOW - Impact 5, Likelihood 1)

---

### RISK-OPS-002: Deployment Pipeline Compromise

**Asset:** GitHub Actions, Docker Images, Terraform State  
**Threat:** Supply chain attack, compromised dependency  
**Vulnerability:** Unverified dependencies, no image scanning

**Impact:** 4 (Major - Malicious code in production)  
**Likelihood:** 2 (Unlikely - but increasing trend)  
**Risk Score:** **8 (MEDIUM)**

**Current Controls:**
- ✅ Trivy container scanning
- ✅ Safety Python dependency scanning
- ✅ GitHub Dependabot alerts

**Gaps:**
- ⏳ No signed commits (GPG)
- ⏳ No container image signing (Cosign)
- ⏳ No SBOM (Software Bill of Materials)

**Treatment Plan:**
- ✅ **Action:** Dependency scanning (COMPLETED - Phase 2.1)
- ⏳ **Action:** Enforce signed commits (Deadline: Q3 2026)
- ⏳ **Action:** Container image signing with Cosign (Deadline: Q4 2026)

**Residual Risk (after treatment):** 4 (LOW - Impact 4, Likelihood 1)

---

### RISK-COMP-001: DSGVO Compliance Violation

**Asset:** Customer Personal Data (Email, IP, Logs)  
**Threat:** Non-compliance → Regulatory Fine (up to €20M or 4% revenue)  
**Vulnerability:** Missing DSGVO rights implementation

**Impact:** 4 (Major - Fines, reputation damage, customer loss)  
**Likelihood:** 3 (Possible - Complex regulation, easy to miss)  
**Risk Score:** **12 (HIGH)**

**Current Controls:**
- ✅ DSGVO API endpoints (Art. 15-22)
- ✅ Encryption at rest (S3, RDS)
- ✅ Data Processing Agreements (DPAs)
- ✅ Privacy Policy

**Gaps:**
- ⏳ DPO (Data Protection Officer) not appointed (required if >250 employees)
- ⏳ DSGVO API not fully implemented (missing DB models)
- ⏳ Cookie Consent not implemented (if website tracks users)

**Treatment Plan:**
- ✅ **Action:** DSGVO API skeleton (COMPLETED - Phase 2.2)
- ⏳ **Action:** Implement DB models + full DSGVO logic (Deadline: Q2 2026)
- ⏳ **Action:** Cookie Consent Banner (if needed) (Deadline: Q3 2026)
- ⏳ **Action:** DPO appointment (when team grows) (Deadline: When >10 employees)

**Residual Risk (after treatment):** 6 (MEDIUM - Impact 4, Likelihood 1-2)

---

### RISK-COMP-002: SOC 2 Audit Failure

**Asset:** SOC 2 Type II Report (required for Enterprise customers)  
**Threat:** Failed audit → Loss of enterprise deals  
**Vulnerability:** Missing controls, insufficient documentation

**Impact:** 3 (Moderate - Lost revenue, sales delays)  
**Likelihood:** 4 (Likely - First audit, complex requirements)  
**Risk Score:** **12 (HIGH)**

**Current Controls:**
- ✅ Security scanning (automated)
- ✅ ISMS documentation (in progress)
- ✅ Incident response plan
- ⏳ 12-month operating effectiveness period not started

**Gaps:**
- ⏳ Trust Services Criteria not fully mapped
- ⏳ No internal audit performed
- ⏳ No evidence collection system

**Treatment Plan:**
- ⏳ **Action:** Complete SOC 2 readiness docs (Deadline: Q2 2026)
- ⏳ **Action:** Internal audit / pre-assessment (Deadline: Q3 2026)
- ⏳ **Action:** External SOC 2 Type II audit (Deadline: Q4 2026 - Q1 2027)

**Residual Risk (after treatment):** 6 (MEDIUM - Impact 3, Likelihood 2)

---

### RISK-BUS-001: Key Person Dependency (Solo Founder)

**Asset:** Platform Knowledge, Infrastructure Access  
**Threat:** Andy unavailable (illness, accident)  
**Vulnerability:** No knowledge transfer, no backup

**Impact:** 4 (Major - Business cannot operate)  
**Likelihood:** 2 (Unlikely - but possible)  
**Risk Score:** **8 (MEDIUM)**

**Current Controls:**
- ✅ Documentation (Infrastructure, Runbooks)
- ✅ Automated deployments (GitHub Actions)
- ✅ Monitoring & alerts

**Gaps:**
- ❌ No backup admin (nobody else has access)
- ❌ No knowledge transfer plan
- ❌ No business continuity insurance

**Treatment Plan:**
- ⏳ **Action:** Hire second engineer (when revenue allows) (Deadline: 2027)
- ⏳ **Action:** Emergency access plan (sealed envelope with credentials) (Deadline: Q2 2026)
- ⏳ **Action:** Business continuity insurance (Deadline: When profitable)

**Residual Risk (after treatment):** 6 (MEDIUM - Impact 4, Likelihood 1-2)  
**Acceptance:** Risk accepted until team grows

---

### RISK-TECH-001: Dependency Vulnerabilities (Supply Chain)

**Asset:** Python/JavaScript dependencies (>200 packages)  
**Threat:** Vulnerable dependencies (CVE)  
**Vulnerability:** Outdated packages

**Impact:** 3 (Moderate - Exploitable vulnerability)  
**Likelihood:** 4 (Likely - New CVEs daily)  
**Risk Score:** **12 (HIGH)**

**Current Controls:**
- ✅ Dependabot alerts (GitHub)
- ✅ Safety scanning (Python)
- ✅ Trivy scanning (all dependencies)
- ✅ Weekly security scans

**Gaps:**
- ⏳ No automated dependency updates (Dependabot PRs not auto-merged)
- ⏳ No SLA for vulnerability remediation

**Treatment Plan:**
- ✅ **Action:** Security scanning automation (COMPLETED - Phase 2.1)
- ⏳ **Action:** Automated PR merge for LOW/MEDIUM (with tests) (Deadline: Q3 2026)
- ⏳ **Action:** SLA: HIGH within 7d, CRITICAL within 24h (Deadline: Q2 2026)

**Residual Risk (after treatment):** 6 (MEDIUM - Impact 3, Likelihood 2)

---

### RISK-TECH-002: Insufficient Monitoring & Alerting

**Asset:** Production Systems  
**Threat:** Undetected outages, security incidents  
**Vulnerability:** No monitoring, delayed detection

**Impact:** 3 (Moderate - Customer impact, SLA breach)  
**Likelihood:** 3 (Possible - Incidents will happen)  
**Risk Score:** **9 (MEDIUM)**

**Current Controls:**
- ✅ CloudWatch metrics & logs
- ✅ Monitoring module (Terraform)
- ⏳ Sentry not fully configured

**Gaps:**
- ⏳ No uptime monitoring (external)
- ⏳ No APM (Application Performance Monitoring)
- ⏳ No centralized log aggregation

**Treatment Plan:**
- ⏳ **Action:** Enable Sentry (error tracking) (Deadline: Q2 2026)
- ⏳ **Action:** UptimeRobot / Better Uptime (external monitoring) (Deadline: Q2 2026)
- ⏳ **Action:** APM evaluation (Datadog, New Relic, or open-source) (Deadline: Q3 2026)

**Residual Risk (after treatment):** 4 (LOW - Impact 3, Likelihood 1-2)

---

## 4. Risk Treatment Summary

### By Risk Level (Before Treatment)

| Level | Count | Risks |
|-------|-------|-------|
| **CRITICAL (16-25)** | 1 | RISK-SEC-002 |
| **HIGH (11-15)** | 4 | RISK-SEC-001, RISK-SEC-004, RISK-COMP-001, RISK-COMP-002, RISK-TECH-001 |
| **MEDIUM (6-10)** | 4 | RISK-SEC-003, RISK-OPS-001, RISK-OPS-002, RISK-BUS-001, RISK-TECH-002 |
| **LOW (1-5)** | 0 | - |

**Total Risks:** 9

### By Risk Level (After Treatment - Target)

| Level | Count | Risks |
|-------|-------|-------|
| **CRITICAL (16-25)** | 0 | - |
| **HIGH (11-15)** | 0 | - |
| **MEDIUM (6-10)** | 5 | RISK-SEC-002, RISK-COMP-001, RISK-COMP-002, RISK-BUS-001, RISK-TECH-001 |
| **LOW (1-5)** | 4 | RISK-SEC-001, RISK-SEC-003, RISK-SEC-004, RISK-OPS-001, RISK-OPS-002, RISK-TECH-002 |

**Mitigation Progress:** 100% of CRITICAL/HIGH risks mitigated to MEDIUM/LOW

---

## 5. Risk Treatment Plan Timeline

### Q2 2026 (Apr-Jun)
- ✅ Enable MFA on all AWS accounts (RISK-SEC-001)
- ⏳ Enforce pre-commit hooks (RISK-SEC-004)
- ⏳ Monthly backup restore tests (RISK-OPS-001)
- ⏳ DDoS response playbook (RISK-SEC-002)
- ⏳ Implement DSGVO DB models (RISK-COMP-001)
- ⏳ Enable Sentry + UptimeRobot (RISK-TECH-002)
- ⏳ SLA for vulnerability remediation (RISK-TECH-001)
- ⏳ Emergency access plan (RISK-BUS-001)
- ⏳ Complete SOC 2 readiness docs (RISK-COMP-002)

### Q3 2026 (Jul-Sep)
- ⏳ AWS Session Manager instead of SSH (RISK-SEC-001)
- ⏳ SAST integration (RISK-SEC-003)
- ⏳ Automated secret rotation (RISK-SEC-004)
- ⏳ DR drill (region failover) (RISK-OPS-001)
- ⏳ Enforce signed commits (RISK-OPS-002)
- ⏳ Automated dependency updates (RISK-TECH-001)
- ⏳ Cookie Consent (if needed) (RISK-COMP-001)
- ⏳ Internal SOC 2 audit (RISK-COMP-002)
- ⏳ APM evaluation (RISK-TECH-002)

### Q4 2026 (Oct-Dec)
- ⏳ Hardware tokens (YubiKey) (RISK-SEC-001)
- ⏳ Annual penetration test (RISK-SEC-003)
- ⏳ Container image signing (RISK-OPS-002)
- ⏳ External SOC 2 Type II audit start (RISK-COMP-002)

---

## 6. Residual Risk Acceptance

**Accepted Risks (with justification):**

### RISK-BUS-001: Key Person Dependency
- **Residual Risk:** MEDIUM (6)
- **Justification:** Acceptable until revenue allows hiring
- **Mitigation:** Emergency access plan, documentation
- **Review:** When first hire

### RISK-SEC-002: DDoS (Shield Advanced not implemented)
- **Residual Risk:** MEDIUM (8)
- **Justification:** $3000/month cost not justified for startup
- **Mitigation:** WAF + Bot Control + Auto-Scaling sufficient
- **Review:** When revenue >$50k/month

**Approved by:** Andy Schwarz (CISO)  
**Date:** 2026-05-15

---

## 7. Next Review

**Scheduled Review:** 2027-05-15 (Annual)

**Triggers for Ad-Hoc Review:**
- Major security incident
- Significant architecture changes
- New compliance requirements
- Audit findings
- Team growth (>2 people)

---

## 8. References

- ISO 27001:2022 Clause 6.1.2 (Information Security Risk Assessment)
- ISO 27001:2022 Clause 6.1.3 (Information Security Risk Treatment)
- ISO 31000:2018 (Risk Management Guidelines)
- NIST SP 800-30 (Guide for Conducting Risk Assessments)

---

**Document Owner:** Andy Schwarz (CISO)  
**Approval Date:** 2026-05-15  
**Next Review:** 2027-05-15
