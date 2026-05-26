# SOC 2 Type II Readiness Assessment

## Trust Services Criteria Compliance

**Document Version:** 1.0  
**Assessment Date:** 2026-05-15  
**Next Review:** 2026-08-15  
**Assessor:** Andy Schwarz (CISO)  
**Classification:** Internal

---

## 1. Executive Summary

Dieses Dokument bewertet die Bereitschaft von StackVertex für eine SOC 2 Type II Zertifizierung gemäß den Trust Services Criteria (TSC) des American Institute of CPAs (AICPA).

### 1.1 SOC 2 Overview

**SOC 2 Type II Requirements:**
- **Operating Effectiveness Period:** 12 Monate dokumentierte Compliance
- **Audit:** External auditor verifies controls
- **Report:** Confidential report für Kunden (NDA)

**Trust Services Categories:**
- **Security (CC):** Common Criteria (mandatory)
- **Availability (A):** 99.9% uptime commitment
- **Confidentiality (C):** Optional (wenn vertrauliche Daten)
- **Processing Integrity (PI):** Optional (nicht relevant für SaaS)
- **Privacy (P):** Optional (überschneidet mit DSGVO)

**StackVertex Focus:** Security (CC) + Availability (A)

### 1.2 Readiness Summary

| Category | Total Controls | Implemented | Partial | Missing | Status |
|----------|----------------|-------------|---------|---------|--------|
| **CC1-CC5** (Common Criteria) | 32 | 24 | 6 | 2 | 75% Ready |
| **CC6** (Logical Access) | 8 | 6 | 1 | 1 | 75% Ready |
| **CC7** (System Operations) | 12 | 9 | 2 | 1 | 75% Ready |
| **CC8** (Change Management) | 6 | 5 | 1 | 0 | 83% Ready |
| **CC9** (Risk Mitigation) | 4 | 3 | 1 | 0 | 75% Ready |
| **A1** (Availability) | 6 | 4 | 2 | 0 | 67% Ready |
| **Total** | **68** | **51** | **13** | **4** | **75% Ready** |

**Target for Audit:** 95% implemented (all controls fully operational)

**Timeline:**
- **Q2 2026:** Complete missing controls (gap remediation)
- **Q3 2026:** Internal audit / readiness assessment
- **Q4 2026:** Start 12-month operating period
- **Q4 2027:** External SOC 2 Type II audit

---

## 2. Trust Services Criteria Assessment

### CC1: Control Environment

**Principle:** The entity demonstrates a commitment to integrity and ethical values.

| Control | Description | Status | Evidence | Gap |
|---------|-------------|--------|----------|-----|
| **CC1.1** | Management philosophy, operating style, integrity | ✅ Implemented | ISMS Policy, Code of Conduct | None |
| **CC1.2** | Board oversight (independent directors) | ❌ Not Applicable | Solo founder (no board yet) | Not required until Series A |
| **CC1.3** | Organizational structure, reporting lines | ✅ Implemented | Org chart (solo → team growth plan) | None |
| **CC1.4** | Authority and responsibility assignment | ✅ Implemented | ISMS Policy (CISO role) | None |
| **CC1.5** | Attracts, develops, and retains competent individuals | ⏳ Partial | Hiring plan documented | No formal training program yet |

**Gap Summary:**
- ⏳ **CC1.5:** Formal training program needed when team grows
- ✅ Overall: COMPLIANT (acceptable for early-stage startup)

---

### CC2: Communication and Information

**Principle:** The entity obtains or generates and uses relevant, quality information.

| Control | Description | Status | Evidence | Gap |
|---------|-------------|--------|----------|-----|
| **CC2.1** | Quality information obtained/generated | ✅ Implemented | Monitoring (CloudWatch, Sentry) | None |
| **CC2.2** | Information communicated internally | ✅ Implemented | Slack, Email, Documentation | None |
| **CC2.3** | Information communicated externally | ✅ Implemented | Status Page, Customer Support | None |
| **CC2.4** | Communication channels for concerns | ✅ Implemented | security@stackvertex.io, Support | None |

**Gap Summary:** ✅ COMPLIANT

---

### CC3: Risk Assessment

**Principle:** The entity identifies, analyzes, and responds to risks.

| Control | Description | Status | Evidence | Gap |
|---------|-------------|--------|----------|-----|
| **CC3.1** | Entity specifies objectives | ✅ Implemented | ISMS Policy (Security Objectives) | None |
| **CC3.2** | Identify and analyze risks | ✅ Implemented | Risk Assessment (9 risks identified) | None |
| **CC3.3** | Assess fraud risk | ⏳ Partial | Covered in Risk Assessment | Not detailed enough |
| **CC3.4** | Identify and assess changes | ✅ Implemented | Change Management (GitHub, Terraform) | None |

**Gap Summary:**
- ⏳ **CC3.3:** Fraud risk assessment needs more detail (payment fraud, account takeover)
- ✅ Overall: MOSTLY COMPLIANT

---

### CC4: Monitoring Activities

**Principle:** The entity selects, develops, and performs ongoing monitoring.

| Control | Description | Status | Evidence | Gap |
|---------|-------------|--------|----------|-----|
| **CC4.1** | Ongoing and separate evaluations | ✅ Implemented | Weekly security scans, Quarterly access review | None |
| **CC4.2** | Evaluates and communicates deficiencies | ✅ Implemented | Incident Response Plan, Post-mortems | None |

**Gap Summary:** ✅ COMPLIANT

---

### CC5: Control Activities

**Principle:** The entity selects and develops control activities.

| Control | Description | Status | Evidence | Gap |
|---------|-------------|--------|----------|-----|
| **CC5.1** | Selects and develops control activities | ✅ Implemented | Security controls (WAF, MFA, Encryption) | None |
| **CC5.2** | Technology controls | ✅ Implemented | Automated security scans, IaC | None |
| **CC5.3** | Policies and procedures | ✅ Implemented | ISMS Policy, Runbooks | None |

**Gap Summary:** ✅ COMPLIANT

---

### CC6: Logical and Physical Access Controls

**Principle:** The entity restricts logical and physical access.

| Control | Description | Status | Evidence | Gap |
|---------|-------------|--------|----------|-----|
| **CC6.1** | Logical access controls | ✅ Implemented | AWS IAM, GitHub 2FA, RBAC | None |
| **CC6.2** | New internal users authorized | ✅ Implemented | Onboarding checklist (when team grows) | None |
| **CC6.3** | Modifications to access authorized | ✅ Implemented | Quarterly access review | None |
| **CC6.4** | Physical access controls | ❌ Not Applicable | Fully cloud-based (no physical datacenter) | AWS responsibility |
| **CC6.5** | Terminated users removed | ⏳ Partial | Offboarding checklist prepared | Not yet tested (no departures) |
| **CC6.6** | Privileged access management | ✅ Implemented | MFA mandatory, Session Manager | None |
| **CC6.7** | Credentials managed | ✅ Implemented | Secrets Manager, Password Manager | None |
| **CC6.8** | Network security | ✅ Implemented | VPC, Security Groups, WAF | None |

**Gap Summary:**
- ⏳ **CC6.5:** Offboarding process needs real-world validation
- ✅ Overall: MOSTLY COMPLIANT

---

### CC7: System Operations

**Principle:** The entity manages system operations to meet objectives.

| Control | Description | Status | Evidence | Gap |
|---------|-------------|--------|----------|-----|
| **CC7.1** | Detect and mitigate processing deviations | ✅ Implemented | CloudWatch Alarms, Sentry, Runbooks | None |
| **CC7.2** | Monitor system capacity | ✅ Implemented | Auto-scaling (Lambda, Aurora), Monitoring | None |
| **CC7.3** | Evaluate actual/potential environmental threats | ⏳ Partial | AWS region selection, DR plan | No climate risk assessment |
| **CC7.4** | Manage environmental threats | ✅ Implemented | DR in separate region (eu-west-1) | None |
| **CC7.5** | Anti-virus/malware protection | ❌ Limited | Container scanning (Trivy), WAF | No endpoint protection (serverless) |

**Gap Summary:**
- ⏳ **CC7.3:** Environmental threat assessment (natural disasters, power outages) - relies on AWS
- ❌ **CC7.5:** Limited for serverless (acceptable for Lambda-based architecture)
- ✅ Overall: MOSTLY COMPLIANT

---

### CC8: Change Management

**Principle:** The entity authorizes, designs, develops, and tests changes.

| Control | Description | Status | Evidence | Gap |
|---------|-------------|--------|----------|-----|
| **CC8.1** | Manage changes throughout lifecycle | ✅ Implemented | Git, GitHub PR reviews, CI/CD | None |
| **CC8.2** | Authorize changes | ✅ Implemented | PR approvals (manual for prod) | None |
| **CC8.3** | Design and develop changes | ✅ Implemented | Development workflow (branching, testing) | None |
| **CC8.4** | Test changes | ✅ Implemented | Automated tests (pytest), Security scans | None |
| **CC8.5** | Approve changes before implementation | ✅ Implemented | GitHub Environments (manual approval) | None |
| **CC8.6** | Deploy changes and manage deployments | ⏳ Partial | GitHub Actions (automated), Rollback capability | No blue/green deployment |

**Gap Summary:**
- ⏳ **CC8.6:** Blue/green deployment would be nice-to-have (not mandatory)
- ✅ Overall: COMPLIANT

---

### CC9: Risk Mitigation

**Principle:** The entity identifies, selects, and develops risk mitigation activities.

| Control | Description | Status | Evidence | Gap |
|---------|-------------|--------|----------|-----|
| **CC9.1** | Identify and assess risks | ✅ Implemented | Risk Assessment (9 risks, treatment plans) | None |
| **CC9.2** | Design/implement risk mitigation activities | ✅ Implemented | Security controls (WAF, MFA, Backup, Encryption) | None |
| **CC9.3** | Conduct vendor risk assessments | ⏳ Partial | AWS (SOC 2), GitHub (SOC 2), Stripe (PCI DSS) | No formal vendor assessment process |
| **CC9.4** | Manage vendor relationships | ✅ Implemented | DPA with critical vendors (planned) | None |

**Gap Summary:**
- ⏳ **CC9.3:** Formal vendor risk assessment process needed (documented checklist)
- ✅ Overall: MOSTLY COMPLIANT

---

### A1: Availability

**Principle:** The entity maintains availability commitments.

| Control | Description | Status | Evidence | Gap |
|---------|-------------|--------|----------|-----|
| **A1.1** | Define availability SLA | ✅ Implemented | 99.9% uptime SLA (43 min/month) | None |
| **A1.2** | Monitor infrastructure capacity | ✅ Implemented | Auto-scaling, CloudWatch metrics | None |
| **A1.3** | Maintain availability commitments | ⏳ Partial | Monitoring, DR plan | Not yet proven (new platform) |
| **A1.4** | Backup and recovery procedures | ✅ Implemented | Daily backups, PITR, DR plan | None |
| **A1.5** | Test backup restores | ⏳ Partial | Process documented | Not yet performed regularly |
| **A1.6** | Incident response for availability | ✅ Implemented | Incident Response Plan, Runbooks | None |

**Gap Summary:**
- ⏳ **A1.3:** Needs 12-month operating history to prove SLA
- ⏳ **A1.5:** Monthly backup restore tests not yet started
- ✅ Overall: GOOD (67% - will improve over time)

---

## 3. Gap Remediation Plan

### 3.1 Critical Gaps (Must-Have for Audit)

| Gap ID | Control | Description | Action | Owner | Deadline | Status |
|--------|---------|-------------|--------|-------|----------|--------|
| **GAP-001** | CC3.3 | Fraud risk assessment incomplete | Document payment fraud, account takeover scenarios | CISO | 2026-06-30 | ⏳ Planned |
| **GAP-002** | CC6.5 | Offboarding process untested | Create test user, perform mock offboarding | CISO | 2026-07-15 | ⏳ Planned |
| **GAP-003** | CC9.3 | Vendor risk assessment process missing | Create vendor assessment checklist, assess top 5 vendors | CISO | 2026-06-30 | ⏳ Planned |
| **GAP-004** | A1.5 | Backup restore testing not regular | Perform first monthly restore test, schedule recurring | CISO | 2026-06-01 | ⏳ Planned |

### 3.2 Important Gaps (Nice-to-Have)

| Gap ID | Control | Description | Action | Deadline |
|--------|---------|-------------|--------|----------|
| **GAP-005** | CC1.5 | No formal training program | Create security awareness training (when team >2) | 2027-Q1 |
| **GAP-006** | CC7.3 | Environmental threat assessment | Document reliance on AWS (shared responsibility) | 2026-Q3 |
| **GAP-007** | CC8.6 | No blue/green deployment | Evaluate AWS Lambda aliases for canary deployments | 2026-Q4 |

---

## 4. Evidence Collection

### 4.1 Control Evidence Requirements

**For each control, auditor will request:**
1. **Policies & Procedures** (design evidence)
2. **Operational Artifacts** (operating effectiveness evidence)
3. **Sampling Period:** 12 months (Type II)

### 4.2 Evidence Repository Structure

```
evidence/
├── CC1-Control-Environment/
│   ├── ISMS_Policy_v1.0.pdf
│   ├── Code_of_Conduct.pdf
│   ├── Org_Chart_2026.pdf
│   └── Hiring_Plan.pdf
├── CC2-Communication/
│   ├── Status_Page_Screenshots/
│   ├── Customer_Communication_Samples/
│   └── Internal_Incident_Notifications/
├── CC3-Risk-Assessment/
│   ├── Risk_Assessment_2026.pdf
│   ├── Risk_Treatment_Plans/
│   └── Quarterly_Risk_Reviews/
├── CC4-Monitoring/
│   ├── Security_Scan_Reports/ (weekly)
│   ├── Access_Review_Reports/ (quarterly)
│   └── Vulnerability_Remediation_Evidence/
├── CC5-Control-Activities/
│   ├── WAF_Configuration/
│   ├── MFA_Enforcement_Screenshots/
│   └── Encryption_Configuration/
├── CC6-Access-Control/
│   ├── AWS_IAM_Policies/
│   ├── GitHub_2FA_Enforcement/
│   ├── Access_Request_Forms/
│   ├── Access_Review_Reports/
│   └── Offboarding_Checklists/ (when applicable)
├── CC7-System-Operations/
│   ├── CloudWatch_Dashboards/
│   ├── Incident_Reports/ (with timestamps)
│   ├── Capacity_Planning_Reports/
│   └── DR_Test_Reports/
├── CC8-Change-Management/
│   ├── GitHub_PR_Examples/ (sample 25 PRs)
│   ├── Deployment_Logs/ (CI/CD)
│   ├── Rollback_Evidence/
│   └── Change_Approval_Evidence/ (staging → prod)
├── CC9-Risk-Mitigation/
│   ├── Vendor_Assessment_Reports/
│   ├── DPAs/ (AWS, GitHub, Stripe)
│   └── Insurance_Policies/
└── A1-Availability/
    ├── Uptime_Reports/ (monthly)
    ├── Backup_Restore_Test_Reports/ (monthly)
    ├── Incident_Post-Mortems/
    └── SLA_Compliance_Reports/
```

### 4.3 Evidence Collection Automation

**Automated Evidence:**
- ✅ Security scan reports (GitHub Actions artifacts)
- ✅ Git commit history (change management)
- ✅ CloudWatch metrics (uptime, performance)
- ✅ CloudTrail logs (access logs)
- ⏳ Access review reports (script to export IAM users/policies)

**Manual Evidence:**
- Incident post-mortems
- Backup restore test results
- Vendor assessments
- Risk assessment updates

**Evidence Retention:** Minimum 3 years (per SOC 2 requirement)

---

## 5. Operating Effectiveness Period

### 5.1 12-Month Observation Period

**Start Date:** 2026-10-01 (Q4 2026)  
**End Date:** 2027-09-30 (Q3 2027)  
**Audit Date:** 2027-10-01 (Q4 2027)

**During this period, auditor will sample:**
- **Access Reviews:** 4 samples (quarterly)
- **Security Scans:** 52 samples (weekly)
- **Incident Responses:** All incidents (hopefully 0 P1/P2)
- **Backup Restores:** 12 samples (monthly)
- **Change Management:** 25 PRs (random sampling)
- **Vendor Assessments:** All critical vendors

### 5.2 Control Testing Matrix

| Control | Test Type | Frequency | Sample Size | Evidence |
|---------|-----------|-----------|-------------|----------|
| **CC1-CC5** | Inquiry + Inspection | Once | N/A | Policies, procedures |
| **CC6** (Access Control) | Inquiry + Inspection + Reperformance | Quarterly | 4 | IAM reports, access logs |
| **CC7** (Operations) | Inquiry + Inspection | Monthly | 12 | Monitoring dashboards, incident logs |
| **CC8** (Change Mgmt) | Inquiry + Inspection + Reperformance | Random | 25 PRs | GitHub PRs, deployment logs |
| **CC9** (Risk) | Inquiry + Inspection | Annually | 1 | Risk assessment, vendor reports |
| **A1** (Availability) | Inquiry + Inspection + Observation | Monthly | 12 | Uptime reports, backup tests |

---

## 6. Audit Process

### 6.1 Pre-Audit Preparation

**Internal Readiness Assessment (Q3 2026):**
1. Self-assess all 68 controls
2. Identify and remediate gaps
3. Collect 3 months of evidence (trial run)
4. Mock audit with consultant (optional)

**Auditor Selection (Q3 2026):**
- Tier 1: Big 4 (Deloitte, PwC, EY, KPMG) - $50-100k
- Tier 2: Mid-size firms (A-LIGN, Schellman, Prescient) - $20-40k
- **Recommendation:** Tier 2 for first audit (cost-effective)

### 6.2 Audit Timeline

**Week 1-2: Planning & Scoping**
- Kick-off meeting
- System walkthrough
- Risk assessment by auditor
- Evidence request list

**Week 3-10: Operating Effectiveness Period Review**
- Auditor samples evidence (remote)
- Interviews with key personnel
- Control testing
- Exception identification

**Week 11-12: Fieldwork & Final Testing**
- Follow-up questions
- Additional evidence requests
- Management representation letter

**Week 13-14: Reporting**
- Draft report review
- Management response to findings
- Final report issuance

**Total Duration:** 3-4 months (concurrent with operations)

### 6.3 Expected Audit Outcomes

**Best Case:** ✅ Unqualified opinion (clean report, no exceptions)

**Likely Case:** ⚠️ Qualified opinion with minor exceptions
- Example: "Control X was not operating effectively for 1 week due to Y"
- Remediation: Document corrective action, re-test after 3 months

**Worst Case:** ❌ Adverse opinion (major control failures)
- Not expected if proper preparation
- Would require significant remediation + re-audit

---

## 7. Cost Estimate

### 7.1 Audit Costs

| Item | Cost (EUR) | Notes |
|------|-----------|-------|
| **External Auditor** | €20,000 - €40,000 | Tier 2 firm, first-time audit |
| **Readiness Assessment** | €5,000 - €10,000 | Optional consultant |
| **Control Implementation** | €0 (internal) | Andy's time (already budgeted) |
| **Evidence Collection Tool** | €500 - €2,000/year | Compliance automation (Drata, Vanta) |
| **Total (First Year)** | **€25,500 - €52,000** | One-time + recurring |
| **Recurring (Annual)** | €20,000 - €30,000 | Annual surveillance audit |

### 7.2 ROI Justification

**Without SOC 2:**
- ❌ Cannot sell to Enterprise customers (Fortune 500)
- ❌ Long sales cycles (custom security questionnaires)
- ❌ Lower deal sizes (<$10k ARR)

**With SOC 2:**
- ✅ Enterprise deals (>$50k ARR)
- ✅ Shorter sales cycles (SOC 2 report = trust)
- ✅ Higher valuations (M&A, fundraising)

**Break-Even:** 1-2 Enterprise deals (€50k-100k ARR) pays for audit

---

## 8. Alternatives to SOC 2

### 8.1 ISO 27001 vs. SOC 2

| Aspect | ISO 27001 | SOC 2 |
|--------|-----------|-------|
| **Recognition** | Global (EU strong) | USA strong |
| **Cost** | €10k-50k | €20k-40k |
| **Duration** | 6-12 months | 12-18 months |
| **Recurring** | Annual surveillance | Annual audit |
| **Report** | Public certificate | Confidential report |
| **Target** | GDPR compliance | Enterprise SaaS |

**Recommendation:** 
- **ISO 27001 first** (DSGVO-relevant, cheaper, faster)
- **SOC 2 later** (when targeting US enterprises)

### 8.2 Security Questionnaires (Alternative)

**Instead of SOC 2, respond to:**
- CAIQ (Consensus Assessments Initiative Questionnaire)
- SIG (Standardized Information Gathering)
- VSA (Vendor Security Alliance)

**Pros:** Free, flexible  
**Cons:** Repetitive (each customer asks separately), not trusted

---

## 9. Action Plan Summary

### 9.1 Q2 2026 (Apr-Jun)
- ✅ Complete ISMS documentation (COMPLETED - Phase 2)
- ⏳ Implement missing controls (GAP-001 to GAP-004)
- ⏳ Start monthly backup restore tests
- ⏳ Create vendor assessment process

### 9.2 Q3 2026 (Jul-Sep)
- ⏳ Internal readiness assessment
- ⏳ Select auditor (RFP to 3 firms)
- ⏳ Collect 3 months of evidence (trial run)
- ⏳ Fix any identified gaps

### 9.3 Q4 2026 (Oct-Dec)
- ⏳ Start 12-month operating period (evidence collection)
- ⏳ Kick-off meeting with auditor
- ⏳ Ongoing evidence collection

### 9.4 2027
- ⏳ Continue operating period (12 months)
- ⏳ Q3 2027: Audit fieldwork
- ⏳ Q4 2027: Receive SOC 2 Type II report

**Total Timeline:** 18 months from now to SOC 2 report

---

## 10. References

**AICPA Standards:**
- TSC 2017 (Trust Services Criteria)
- AT-C Section 105 & 205 (SOC 2 framework)

**Helpful Resources:**
- https://us.aicpa.org/soc2 (Official guidance)
- https://www.vanta.com/products/soc-2 (Automation tool)
- https://secureframe.com/ (Alternative automation)

**External Auditors (Shortlist):**
- A-LIGN (https://a-lign.com)
- Schellman (https://schellman.com)
- Prescient Assurance (https://prescientassurance.com)

---

**Document Owner:** Andy Schwarz (CISO)  
**Last Updated:** 2026-05-15  
**Next Review:** 2026-08-15 (Quarterly until audit)
