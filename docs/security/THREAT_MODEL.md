# StackVertex Threat Model

**Version:** 1.0  
**Last Updated:** 2026-05-16  
**Framework:** STRIDE (Microsoft Threat Modeling)

---

## Executive Summary

Dieses Dokument identifiziert potenzielle Bedrohungen für die StackVertex Plattform und dokumentiert Mitigations. Threat Modeling ist ein kontinuierlicher Prozess und wird quartalsweise aktualisiert.

**Methodology:** STRIDE
- **S**poofing (Identity Fälschung)
- **T**ampering (Datenmanipulation)
- **R**epudiation (Nicht-Nachvollziehbarkeit)
- **I**nformation Disclosure (Datenleck)
- **D**enial of Service (Verfügbarkeit)
- **E**levation of Privilege (Rechte-Eskalation)

---

## System Overview

### Architecture Diagram

```
┌──────────────────────────────────────────────────────────┐
│                      Internet                             │
└────────────────────────┬─────────────────────────────────┘
                         │
                    ┌────▼────┐
                    │  User   │
                    └────┬────┘
                         │ HTTPS
                    ┌────▼────────────────┐
                    │   CloudFront + WAF  │ (Trust Boundary 1)
                    └────┬────────────────┘
                         │
                    ┌────▼────────────┐
                    │      ALB        │
                    └────┬────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
   ┌────▼─────┐   ┌─────▼──────┐   ┌────▼─────┐
   │ Frontend │   │  Backend   │   │   API    │ (Trust Boundary 2)
   │ (Static) │   │  (FastAPI) │   │  Gateway │
   └──────────┘   └─────┬──────┘   └──────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
   ┌────▼────┐   ┌─────▼──────┐  ┌────▼──────┐
   │DynamoDB │   │  Secrets   │  │    S3     │ (Trust Boundary 3)
   │  (Data) │   │  Manager   │  │(Terraform)│
   └─────────┘   └────────────┘  └───────────┘
                        │
                   ┌────▼──────┐
                   │ Customer  │ (Trust Boundary 4)
                   │   AWS     │
                   │ Account   │
                   └───────────┘
```

### Trust Boundaries

1. **Internet → CloudFront** - Externe Angreifer
2. **CloudFront → Backend** - Authentifizierte User
3. **Backend → AWS Services** - StackVertex Platform
4. **StackVertex → Customer AWS** - Cross-Account Access

---

## Assets (Was schützen wir?)

### Critical Assets

| Asset | Value | Confidentiality | Integrity | Availability |
|-------|-------|----------------|-----------|--------------|
| User Credentials (Passwords) | HIGH | CRITICAL | CRITICAL | HIGH |
| JWT Tokens | HIGH | CRITICAL | CRITICAL | MEDIUM |
| AWS Customer Credentials (Role ARNs) | CRITICAL | CRITICAL | CRITICAL | HIGH |
| Customer Architecture Data | HIGH | HIGH | CRITICAL | HIGH |
| Terraform State Files | HIGH | HIGH | CRITICAL | HIGH |
| Audit Logs | MEDIUM | HIGH | CRITICAL | MEDIUM |
| Source Code | MEDIUM | MEDIUM | HIGH | MEDIUM |
| Database (DynamoDB) | HIGH | HIGH | CRITICAL | CRITICAL |

### Asset Classification

- **CRITICAL:** Kompromittierung = Customer AWS Accounts gefährdet
- **HIGH:** Kompromittierung = Customer Data Leak oder Service Ausfall
- **MEDIUM:** Kompromittierung = Reputationsschaden oder Wiederherstellung nötig
- **LOW:** Kompromittierung = Minimaler Impact

---

## Threat Analysis (STRIDE)

### 1. Spoofing (Identity)

#### Threat 1.1: JWT Token Fälschung

**Description:**  
Angreifer erstellt gültigen JWT Token ohne Authentifizierung.

**Attack Scenario:**
1. Angreifer kennt SECRET_KEY (leaked in Git, hardcoded, schwach)
2. Angreifer erstellt JWT mit beliebiger User ID
3. Angreifer greift auf fremde User-Daten zu

**Impact:** CRITICAL  
**Likelihood:** LOW (nach Fix)  
**Risk Score:** HIGH

**Mitigations:**
- ✅ Starker SECRET_KEY (256-bit, cryptographically random)
- ✅ SECRET_KEY Validation (min 32 chars, keine defaults)
- ✅ SECRET_KEY in AWS Secrets Manager (Production)
- ✅ detect-secrets scan (Pre-commit hook)
- ✅ Token Signature Verification (jwt.decode)

**Residual Risk:** LOW

---

#### Threat 1.2: Session Hijacking

**Description:**  
Angreifer stiehlt JWT Token eines legitimen Users.

**Attack Scenario:**
1. XSS Attack → Token aus localStorage gestohlen
2. Man-in-the-Middle (MITM) → Token abgefangen
3. Malware auf User Device → Token ausgelesen

**Impact:** HIGH  
**Likelihood:** MEDIUM  
**Risk Score:** HIGH

**Mitigations:**
- ✅ HTTPS enforced (kein HTTP)
- ✅ Content-Security-Policy (XSS Prevention)
- ✅ Token Expiration (30 min)
- ✅ HSTS Header (prevents MITM downgrade)
- ⚠️ HTTPOnly Cookies (NOT IMPLEMENTED - using localStorage)

**Residual Risk:** MEDIUM

**Recommendation:**  
Migrate von localStorage zu HTTPOnly Cookies (v1.1)

---

#### Threat 1.3: Phishing

**Description:**  
Angreifer erstellt fake Login-Seite, stiehlt Credentials.

**Attack Scenario:**
1. User erhält Email mit Link zu `overc1oud.io` (Typosquatting)
2. User gibt Credentials ein
3. Angreifer nutzt Credentials auf echter Platform

**Impact:** HIGH  
**Likelihood:** MEDIUM  
**Risk Score:** HIGH

**Mitigations:**
- ⚠️ Email Verification (NOT IMPLEMENTED)
- ⚠️ 2FA (NOT IMPLEMENTED)
- ✅ Rate Limiting auf Login (verhindert Brute Force mit gestohlenen Passwörtern)
- ❌ Security Awareness Training

**Residual Risk:** HIGH

**Recommendation:**  
1. Email Verification implementieren (v1.0)
2. 2FA für Admin Accounts (v1.1)
3. User Education (Phishing Awareness)

---

### 2. Tampering (Data Manipulation)

#### Threat 2.1: Architecture JSON Manipulation

**Description:**  
Angreifer modifiziert Architecture JSON zwischen Save und Deploy.

**Attack Scenario:**
1. User speichert Architecture JSON in DynamoDB
2. Angreifer (mit DB Access) modifiziert JSON
3. User deployed manipulierte Architecture → unerwartete AWS Resources

**Impact:** HIGH  
**Likelihood:** LOW  
**Risk Score:** MEDIUM

**Mitigations:**
- ✅ DynamoDB Encryption at Rest
- ✅ IAM Least Privilege (nur Backend kann DB schreiben)
- ✅ Audit Logging (alle Änderungen geloggt)
- ⚠️ HMAC Signature (NOT IMPLEMENTED - empfohlen)

**Residual Risk:** MEDIUM

**Recommendation:**  
HMAC Signature für Architecture JSON implementieren (v1.1)

```python
signature = hmac.new(SECRET_KEY, json.dumps(architecture_json), sha256).hexdigest()
# Store signature with JSON
# Verify signature before deployment
```

---

#### Threat 2.2: Terraform State Tampering

**Description:**  
Angreifer modifiziert Terraform State File in S3.

**Attack Scenario:**
1. Angreifer erhält Zugriff zu S3 Bucket
2. Angreifer modifiziert State File
3. Nächster `terraform apply` führt zu falschen Changes

**Impact:** CRITICAL  
**Likelihood:** LOW  
**Risk Score:** HIGH

**Mitigations:**
- ✅ S3 Encryption (SSE-S3)
- ✅ S3 Versioning (Rollback möglich)
- ✅ S3 Access Logs
- ✅ IAM Least Privilege (nur Backend kann schreiben)
- ✅ State Locking (DynamoDB)

**Residual Risk:** LOW

---

#### Threat 2.3: SQL/NoSQL Injection

**Description:**  
Angreifer injiziert malicious Code in DynamoDB Queries.

**Attack Scenario:**
1. User Input: `email = "test@example.com' OR '1'='1"`
2. Query: `filter(email == user_input)` → alle Users returned

**Impact:** CRITICAL  
**Likelihood:** VERY LOW  
**Risk Score:** MEDIUM

**Mitigations:**
- ✅ DynamoDB boto3 SDK (parameterized queries)
- ✅ Pydantic Input Validation
- ✅ No string concatenation in queries
- ✅ Keine `eval()` oder `exec()` mit User Input

**Residual Risk:** VERY LOW

---

### 3. Repudiation (Non-Repudiation)

#### Threat 3.1: User bestreitet Aktion

**Description:**  
User deployed kritische Changes, bestreitet es später.

**Attack Scenario:**
1. User deployed Architecture mit falscher Config
2. Kostenexplosion oder Security Issue
3. User: "Das war ich nicht!"

**Impact:** MEDIUM  
**Likelihood:** LOW  
**Risk Score:** LOW

**Mitigations:**
- ✅ Audit Logging (user_id, timestamp, IP, User-Agent)
- ✅ Immutable Logs (DynamoDB + S3 Archive)
- ✅ Time-partitioning (AUDIT#{YYYYMM})
- ✅ Architecture Versioning (alle Änderungen nachvollziehbar)

**Residual Risk:** VERY LOW

---

### 4. Information Disclosure (Datenleck)

#### Threat 4.1: AWS Credentials Leak

**Description:**  
AWS Customer Credentials (Role ARNs) werden geleaked.

**Attack Scenario:**
1. DynamoDB Breach → alle Customer AWS Role ARNs im Klartext
2. Angreifer nutzt AssumeRole → Zugriff auf Customer AWS Accounts

**Impact:** CRITICAL  
**Likelihood:** LOW (nach Fix)  
**Risk Score:** CRITICAL

**Mitigations:**
- ✅ AWS Secrets Manager (KMS encrypted)
- ✅ SecretsManager Service implementiert
- 🟡 Integration pending (OrganisationRepository)
- ✅ DynamoDB speichert nur Secret Reference (nicht ARN selbst)
- ✅ DynamoDB Encryption at Rest

**Residual Risk:** LOW (nach Integration)

**Status:** 🚨 **HIGH PRIORITY** - Integration vor Production

---

#### Threat 4.2: Error Messages Leak Internal Info

**Description:**  
Stack Traces oder Error Messages enthalten sensible Daten.

**Attack Scenario:**
1. User sendet malformed request
2. Backend Error: `File "/app/config.py", line 42: SECRET_KEY=xyz123`
3. Angreifer sieht SECRET_KEY oder Filesystem-Struktur

**Impact:** HIGH  
**Likelihood:** MEDIUM (vor Fix)  
**Risk Score:** HIGH

**Mitigations:**
- ✅ Environment-aware Error Handling
- ✅ Production: Generic errors nur
- ✅ Development: Full stack traces
- ✅ Exception Handlers (app/main.py)

**Residual Risk:** LOW

---

#### Threat 4.3: Audit Logs enthalten sensible Daten

**Description:**  
Audit Logs loggen Passwords, Tokens, oder AWS Credentials.

**Attack Scenario:**
1. Developer loggt: `logger.info(f"User login: {email} with {password}")`
2. Logs in CloudWatch
3. Attacker mit CloudWatch Access sieht Passwords

**Impact:** CRITICAL  
**Likelihood:** LOW  
**Risk Score:** HIGH

**Mitigations:**
- ✅ Code Review Checklist (keine sensiblen Daten in Logs)
- ✅ Logging Guidelines (SECURITY_BEST_PRACTICES.md)
- ✅ Audit Log Service (keine Passwords/Tokens)
- ⚠️ Automated Log Scanning (NOT IMPLEMENTED)

**Residual Risk:** MEDIUM

**Recommendation:**  
Automated scan für sensible Daten in Logs (regex patterns)

---

#### Threat 4.4: IDOR (Insecure Direct Object Reference)

**Description:**  
User A kann User B's Daten abrufen durch ID Manipulation.

**Attack Scenario:**
1. User A: GET `/api/architectures/123` (eigene)
2. User A: GET `/api/architectures/456` (fremde) → 200 OK
3. User A sieht fremde Architecture

**Impact:** HIGH  
**Likelihood:** LOW  
**Risk Score:** MEDIUM

**Mitigations:**
- ✅ Organisation Membership Check (jeder Endpoint)
- ✅ Resource Ownership Validation
- ✅ RBAC Permission Checks
- ✅ Unit Tests (test_update_other_user_forbidden)

**Residual Risk:** LOW

---

### 5. Denial of Service (DoS)

#### Threat 5.1: Brute Force Login Attacks

**Description:**  
Angreifer versucht tausende Passwords pro Sekunde.

**Attack Scenario:**
1. Angreifer: POST `/auth/login` mit 10000 requests/sec
2. Backend überlastet
3. Legitimate Users können nicht einloggen

**Impact:** HIGH  
**Likelihood:** HIGH  
**Risk Score:** HIGH

**Mitigations:**
- ⚠️ Rate Limiting (NOT IMPLEMENTED - CRITICAL!)
- ⚠️ Account Lockout (NOT IMPLEMENTED)
- ✅ CloudFront Rate Limiting (basic)
- ✅ AWS Shield Standard (DDoS)

**Residual Risk:** HIGH

**Status:** 🚨 **CRITICAL** - Rate Limiting vor Public Beta

**Recommendation:**  
SlowAPI implementieren:
```python
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

@router.post("/auth/login")
@limiter.limit("5/minute")  # Max 5 logins/minute
async def login(...):
    ...
```

---

#### Threat 5.2: Resource Exhaustion (Quota Bypass)

**Description:**  
User deployed mehr Resources als Plan erlaubt.

**Attack Scenario:**
1. User: Free Plan (Max 3 Architectures)
2. User erstellt 100 Architectures via API
3. DynamoDB/S3 Costs explodieren

**Impact:** MEDIUM  
**Likelihood:** LOW  
**Risk Score:** MEDIUM

**Mitigations:**
- ✅ Quota Management (Plan-based limits)
- ✅ Quota Check vor jedem Create
- ✅ API Rate Limiting (CloudFront)
- ⚠️ Cost Monitoring & Alerts (NOT IMPLEMENTED)

**Residual Risk:** LOW

---

#### Threat 5.3: DynamoDB Throttling

**Description:**  
High traffic → DynamoDB throttles requests → Service unavailable.

**Attack Scenario:**
1. Black Friday → 1000x normale Traffic
2. DynamoDB Read/Write Capacity exceeded
3. User sehen Errors

**Impact:** HIGH  
**Likelihood:** MEDIUM  
**Risk Score:** MEDIUM

**Mitigations:**
- ✅ DynamoDB On-Demand Pricing (auto-scaling)
- ⚠️ Reserved Capacity (NOT CONFIGURED)
- ⚠️ CloudWatch Alarms (NOT CONFIGURED)
- ✅ Exponential Backoff (boto3 default)

**Residual Risk:** MEDIUM

**Recommendation:**  
CloudWatch Alarm: DynamoDB Throttling > 0 → SNS Alert

---

### 6. Elevation of Privilege

#### Threat 6.1: Horizontal Privilege Escalation (VIEWER → ADMIN)

**Description:**  
VIEWER manipuliert Request → erhält ADMIN Permissions.

**Attack Scenario:**
1. User: VIEWER Role
2. User sendet: `POST /organisations/123/users/456/role` mit `{"role": "ADMIN"}`
3. Backend validated nicht → User ist jetzt ADMIN

**Impact:** CRITICAL  
**Likelihood:** LOW  
**Risk Score:** HIGH

**Mitigations:**
- ✅ RBAC Permission Checks (alle Endpoints)
- ✅ check_org_permission() Funktion
- ✅ User Role validation
- ✅ Unit Tests (test_member_cannot_change_roles)

**Residual Risk:** LOW

---

#### Threat 6.2: Vertical Privilege Escalation (User → SuperAdmin)

**Description:**  
User erhält SuperAdmin Access auf Platform-Ebene.

**Attack Scenario:**
1. User findet Admin Panel Endpoint: `/admin/users`
2. Keine SuperAdmin Check → User sieht alle Platform Users
3. User modified andere User Accounts

**Impact:** CRITICAL  
**Likelihood:** LOW  
**Risk Score:** HIGH

**Mitigations:**
- ⚠️ SuperAdmin System (NOT IMPLEMENTED)
- ⚠️ Separate Admin Endpoints (NOT IMPLEMENTED)
- ⚠️ SuperAdmin RBAC (NOT IMPLEMENTED)

**Residual Risk:** HIGH

**Status:** Planned for v1.1

---

#### Threat 6.3: IAM Role Compromise (Customer AWS)

**Description:**  
StackVertex IAM Role in Customer Account wird kompromittiert.

**Attack Scenario:**
1. Customer erstellt StackVertex Role mit zu vielen Permissions
2. StackVertex Account compromised
3. Angreifer nutzt AssumeRole → Full Access zu Customer AWS

**Impact:** CRITICAL  
**Likelihood:** LOW  
**Risk Score:** HIGH

**Mitigations:**
- ✅ Least Privilege IAM Policies (dokumentiert in AWS_SETUP.md)
- ✅ AssumeRole mit ExternalId (Cross-Account Security)
- ✅ Role Session Duration (1 Stunde max)
- ✅ CloudTrail Logging (alle AssumeRole Calls)
- ⚠️ Automated Policy Validation (NOT IMPLEMENTED)

**Residual Risk:** MEDIUM

**Recommendation:**  
Validate Customer IAM Policies vor Onboarding (Policy Scanner)

---

## Attack Vectors

### External Attackers

**Motivation:** Financial gain, Data theft, Reputational damage  
**Capabilities:** Advanced (APT), Script Kiddies, Bot Networks

**Entry Points:**
1. Web Application (Frontend + Backend APIs)
2. DNS (Subdomain takeover, DNS poisoning)
3. SSL Certificate (Expired, mis-issued)
4. Social Engineering (Phishing, Pretexting)

**Defense:**
- ✅ WAF (CloudFront)
- ✅ DDoS Protection (AWS Shield)
- ✅ Security Headers
- ✅ Input Validation
- ⚠️ Security Awareness Training (NOT IMPLEMENTED)

---

### Malicious Insiders

**Motivation:** Financial gain, Sabotage, Revenge  
**Capabilities:** High (Code Access, AWS Console Access)

**Entry Points:**
1. AWS Console (Root Account, IAM Users)
2. Source Code (GitHub)
3. Database (DynamoDB Console)
4. Secrets Manager (AWS Secrets)

**Defense:**
- ✅ MFA für AWS Accounts
- ✅ IAM Least Privilege
- ✅ Audit Logging (CloudTrail, DynamoDB)
- ✅ Code Review (4-eyes principle)
- ⚠️ Background Checks (NOT IMPLEMENTED)

---

### Compromised Dependencies

**Motivation:** Supply Chain Attack  
**Capabilities:** Code Injection via npm/pip packages

**Entry Points:**
1. npm packages (Frontend)
2. pip packages (Backend)
3. Docker Images
4. GitHub Actions

**Defense:**
- ✅ Automated Dependency Scanning (Trivy, Safety)
- ✅ Dependabot (GitHub)
- ✅ Poetry Lock File (reproducible builds)
- ✅ npm package-lock.json
- ⚠️ Package Signature Verification (NOT IMPLEMENTED)

---

### Customer Misconfiguration

**Motivation:** Accidental (No malicious intent)  
**Capabilities:** Low (Limited AWS knowledge)

**Entry Points:**
1. AWS IAM Role (zu viele Permissions)
2. Architecture Configuration (insecure defaults)
3. Terraform State Bucket (public accessible)

**Defense:**
- ✅ Documentation (AWS_SETUP.md)
- ✅ Policy Templates (secure defaults)
- ⚠️ Automated Policy Validation (NOT IMPLEMENTED)
- ⚠️ Configuration Linting (NOT IMPLEMENTED)

---

## Risk Matrix

| Threat | Impact | Likelihood | Risk Score | Mitigation Status | Residual Risk |
|--------|--------|------------|------------|-------------------|---------------|
| JWT Token Fälschung | CRITICAL | LOW | HIGH | ✅ Mitigated | LOW |
| Session Hijacking | HIGH | MEDIUM | HIGH | ✅ Mitigated | MEDIUM |
| Phishing | HIGH | MEDIUM | HIGH | ⚠️ Partial | HIGH |
| Architecture Tampering | HIGH | LOW | MEDIUM | ✅ Mitigated | MEDIUM |
| Terraform State Tampering | CRITICAL | LOW | HIGH | ✅ Mitigated | LOW |
| SQL/NoSQL Injection | CRITICAL | VERY LOW | MEDIUM | ✅ Mitigated | VERY LOW |
| AWS Credentials Leak | CRITICAL | LOW | CRITICAL | 🟡 In Progress | LOW (after fix) |
| Error Messages Leak | HIGH | MEDIUM | HIGH | ✅ Mitigated | LOW |
| Audit Logs Leak Secrets | CRITICAL | LOW | HIGH | ✅ Mitigated | MEDIUM |
| IDOR | HIGH | LOW | MEDIUM | ✅ Mitigated | LOW |
| Brute Force Login | HIGH | HIGH | HIGH | ⚠️ NOT MITIGATED | HIGH |
| Resource Exhaustion | MEDIUM | LOW | MEDIUM | ✅ Mitigated | LOW |
| DynamoDB Throttling | HIGH | MEDIUM | MEDIUM | ⚠️ Partial | MEDIUM |
| Horizontal Privilege Escalation | CRITICAL | LOW | HIGH | ✅ Mitigated | LOW |
| Vertical Privilege Escalation | CRITICAL | LOW | HIGH | ⚠️ NOT MITIGATED | HIGH |
| IAM Role Compromise | CRITICAL | LOW | HIGH | ✅ Mitigated | MEDIUM |

**Risk Score Calculation:** Impact × Likelihood  
**Legend:**  
- ✅ Fully Mitigated  
- 🟡 In Progress  
- ⚠️ Partially Mitigated  
- ❌ Not Mitigated

---

## Mitigation Roadmap

### Immediate (Before Production)
1. 🚨 **AWS Credentials Integration** (SecretsManager → OrganisationRepository)
2. 🚨 **Rate Limiting** (SlowAPI auf /auth/*)
3. 🚨 **Account Lockout** (5 failed attempts)
4. 🚨 **Internal Penetration Test**

### Short-term (Within 1 Month)
5. Email Verification Flow
6. CloudWatch Alarms (DynamoDB, Errors, Failed Logins)
7. HMAC Signature für Architecture JSON
8. HTTPOnly Cookies (statt localStorage)

### Medium-term (Within 3 Months)
9. 2FA für Admin Accounts
10. SuperAdmin System
11. Automated Policy Validation (Customer IAM)
12. Security Awareness Training

### Long-term (Roadmap)
13. Bug Bounty Program
14. SOC 2 Audit
15. External Penetration Testing (quarterly)
16. ISO 27001 Certification

---

## Incident Response Triggers

### Trigger Conditions

| Event | Severity | Response Time | Action |
|-------|----------|---------------|--------|
| AWS Credentials leaked | P0 | Immediate | Rotate all secrets, notify customers |
| JWT SECRET_KEY leaked | P0 | Immediate | Rotate key, invalidate all tokens |
| DynamoDB Breach | P0 | Immediate | Isolate DB, forensics, customer notification |
| Brute Force Attack detected | P1 | <1h | Enable rate limiting, block IPs |
| DDoS Attack | P1 | <1h | Activate AWS Shield Advanced |
| Failed login spike | P2 | <4h | Investigate, potential credential stuffing |
| Dependency vulnerability (CRITICAL) | P1 | <24h | Patch, test, deploy |

---

## Security Testing Plan

### Static Analysis (SAST)
- [x] Bandit (Python)
- [ ] SonarQube (planned)
- [x] detect-secrets (Pre-commit)

### Dynamic Analysis (DAST)
- [ ] OWASP ZAP Baseline Scan (staging)
- [ ] OWASP ZAP Full Scan (pre-production)
- [ ] Burp Suite (manual testing)

### Penetration Testing
- [ ] Internal Pen Test (vor Go-Live)
- [ ] External Pen Test (quarterly nach Launch)

### Bug Bounty Scope
- Web Application (Frontend + Backend)
- API Endpoints
- Infrastructure (AWS)
- **Out of Scope:** Social Engineering, Physical, DoS

---

## References

### Internal
- [SECURITY_OVERVIEW.md](./SECURITY_OVERVIEW.md)
- [SECURITY_BEST_PRACTICES.md](./SECURITY_BEST_PRACTICES.md)
- [SECURITY_CHECKLIST.md](./SECURITY_CHECKLIST.md)
- [SECURITY_AUDIT.md](../backend/SECURITY_AUDIT.md)

### External
- [OWASP Threat Modeling](https://owasp.org/www-community/Threat_Modeling)
- [Microsoft STRIDE](https://learn.microsoft.com/en-us/azure/security/develop/threat-modeling-tool-threats)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [AWS Well-Architected Framework - Security Pillar](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/welcome.html)

---

**Document Owner:** Andy Schwarz  
**Review Frequency:** Quarterly  
**Next Review:** 2026-08-16  
**Version:** 1.0
