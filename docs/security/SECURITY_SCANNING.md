# Security Scanning - Automated Security Audits

## Übersicht

OverCloud führt automatisierte Security Scans bei jedem Push und wöchentlich durch. Dies erfüllt ISO 27001 und SOC 2 Anforderungen für regelmäßige Sicherheitsüberprüfungen.

## Scan-Tools

### 1. Trivy - Container & IaC Security Scanner

**Was wird gescannt:**
- ✅ Dateisystem (Dependencies, Config-Files)
- ✅ Infrastructure-as-Code (Terraform)
- ✅ Docker Images (später)
- ✅ Known Vulnerabilities (CVE Database)

**Severity Levels:**
- 🔴 **CRITICAL** - Sofort beheben (RCE, Auth Bypass, etc.)
- 🟠 **HIGH** - Innerhalb 7 Tage beheben
- 🟡 **MEDIUM** - Innerhalb 30 Tage beheben
- 🔵 **LOW** - Bei Gelegenheit beheben

**GitHub Integration:**
- Ergebnisse erscheinen in: **Security → Code scanning**
- Automatische PRs via Dependabot möglich

**Beispiel-Findings:**
```
CVE-2024-12345 (CRITICAL)
Package: fastapi
Version: 0.95.0
Fixed in: 0.100.0
Impact: Remote Code Execution

Action: Update fastapi in pyproject.toml
```

### 2. Safety - Python Dependency Security

**Was wird gescannt:**
- Python Dependencies aus `pyproject.toml`
- Bekannte Vulnerabilities in PyPI Packages
- Outdated Packages mit Security Issues

**Database:**
- PyUp.io Vulnerability Database
- CVE Database
- GitHub Security Advisories

**Output:**
```json
{
  "vulnerabilities": [
    {
      "package": "requests",
      "installed_version": "2.25.0",
      "vulnerability_id": "CVE-2023-32681",
      "fixed_version": "2.31.0"
    }
  ]
}
```

### 3. Gitleaks - Secret Scanning

**Was wird gescannt:**
- Git History (alle Commits)
- Staged Files
- Committed Files

**Erkannte Secrets:**
- AWS Access Keys
- API Tokens
- Private Keys (RSA, SSH)
- Passwords in Code
- Database Connection Strings
- Slack Webhooks

**⚠️ KRITISCH:** Wenn Secrets gefunden werden:
1. **Sofort rotieren** (altes Secret deaktivieren)
2. Aus Git History entfernen: `git filter-repo` oder BFG Repo Cleaner
3. `.gitignore` updaten
4. Pre-commit Hook aktivieren (verhindert zukünftige Leaks)

### 4. OWASP ZAP - Dynamic Application Security Testing (DAST)

**Was wird getestet:**
- Laufende API Endpoints
- Authentication & Authorization
- Common Web Vulnerabilities (OWASP Top 10)

**OWASP Top 10 (2021):**
1. Broken Access Control
2. Cryptographic Failures
3. Injection (SQL, XSS, etc.)
4. Insecure Design
5. Security Misconfiguration
6. Vulnerable Components
7. Authentication Failures
8. Data Integrity Failures
9. Logging & Monitoring Failures
10. Server-Side Request Forgery (SSRF)

**ZAP Scan Modi:**
- **Baseline Scan** - Passiv, keine Angriffe (CI/CD safe)
- **Full Scan** - Aktiv, echte Angriffe (nur in Staging!)
- **API Scan** - Spezialisiert auf REST APIs

**Hinweis:** ZAP läuft nur auf deployed Environments (dev/staging/prod), nicht auf PRs.

## Workflow

### Automatische Scans

**Bei jedem Push:**
```yaml
on:
  push:
    branches: [main, staging, develop]
  pull_request:
    branches: [main, staging, develop]
```

**Wöchentlich (Montag 3 Uhr UTC):**
```yaml
on:
  schedule:
    - cron: '0 3 * * 1'
```

**Manuell:**
```bash
# In GitHub UI:
Actions → Security Scanning → Run workflow
```

### Scan-Ablauf

```
┌─────────────────────────────────────────┐
│  1. Trivy Scan                          │
│     ├── Filesystem                      │
│     ├── IaC (Terraform)                 │
│     └── Docker Image                    │
├─────────────────────────────────────────┤
│  2. Python Security                     │
│     └── Safety Check (Dependencies)     │
├─────────────────────────────────────────┤
│  3. Secret Scanning                     │
│     └── Gitleaks (Git History)          │
├─────────────────────────────────────────┤
│  4. OWASP ZAP (wenn deployed)           │
│     └── Dynamic API Testing             │
├─────────────────────────────────────────┤
│  5. Security Summary                    │
│     └── Aggregated Report               │
└─────────────────────────────────────────┘
```

## Ergebnisse ansehen

### GitHub Security Tab
```
https://github.com/AndySchw/OverCloud/security
```

**Code Scanning Alerts:**
- Security → Code scanning
- Filtert nach: Branch, Severity, Tool

**Dependabot Alerts:**
- Security → Dependabot
- Automatische PR-Vorschläge für Updates

### Artifacts (Detaillierte Reports)
```
Actions → Security Scanning → [Latest Run] → Artifacts
```

**Download:**
- `trivy-security-report` - Trivy Scan Ergebnisse
- `python-security-report` - Safety Check Ergebnisse
- `secret-scan-report` - Gitleaks Ergebnisse
- `zap-scan-report-*` - OWASP ZAP Ergebnisse (per Environment)
- `security-summary` - Aggregierter Gesamt-Report

## Remediation Workflow

### 1. Finding identifizieren
```
GitHub Security → Code scanning → [Alert öffnen]
```

### 2. Severity bewerten
- **CRITICAL/HIGH:** Sofort beheben (heute)
- **MEDIUM:** Innerhalb Sprint beheben
- **LOW:** In Backlog aufnehmen

### 3. Fix implementieren

**Dependency Update:**
```bash
# Python
cd backend
poetry update <package>
poetry lock

# Verify fix
poetry run safety check
```

**Code Fix:**
```bash
# Create fix branch
git checkout -b fix/security-cve-2024-12345

# Implement fix
# ...

# Commit
git commit -m "security: Fix CVE-2024-12345 in <package>"

# Push + PR
git push origin fix/security-cve-2024-12345
gh pr create --title "Fix CVE-2024-12345" --body "Fixes security vulnerability..."
```

### 4. Verify Fix
```bash
# Re-run security scans
gh workflow run security-scan.yml

# Check results
gh run list --workflow=security-scan.yml
```

### 5. Close Alert
- GitHub Security → Code scanning → [Alert]
- "Dismiss alert" → "Fixed" → Save

## False Positives

### ZAP False Positives
Konfiguriert in `.github/workflows/zap-rules.tsv`:

```tsv
# Ignore X-Content-Type-Options for API endpoints
10021	IGNORE
```

### Trivy False Positives
Erstelle `.trivyignore`:
```
# Ignore specific CVE (with reason)
CVE-2024-12345  # False positive: not exploitable in our use case
```

### Safety False Positives
Erstelle `backend/.safety-policy.yml`:
```yaml
security:
  ignore-vulnerabilities:
    - id: 12345
      reason: "Not exploitable - only affects Windows"
      expires: "2026-12-31"
```

## Compliance Mapping

### ISO 27001
- **A.12.6.1** - Kontrolle technischer Schwachstellen
- **A.14.2.1** - Sichere Entwicklungsrichtlinien

✅ Automatisierte Scans erfüllen diese Anforderungen

### SOC 2 Trust Services Criteria
- **CC7.1** - System wird auf Schwachstellen überwacht
- **CC7.2** - Schwachstellen werden identifiziert und behoben

✅ Wöchentliche Scans + Remediation-Prozess erfüllen CC7

### DSGVO
- **Art. 32** - Sicherheit der Verarbeitung

✅ Regelmäßige Security Audits demonstrieren "Stand der Technik"

## Best Practices

### 1. Dependency Updates
```bash
# Wöchentlich ausführen
cd backend
poetry update --dry-run  # Preview
poetry update            # Apply updates
poetry run pytest        # Verify
```

### 2. Security Monitoring
- ✅ GitHub Security Alerts aktiviert
- ✅ Dependabot aktiviert (Auto-PRs)
- ✅ Email-Benachrichtigungen für Critical Findings

### 3. Pre-Commit Hooks
```bash
# Install pre-commit
pip install pre-commit

# .pre-commit-config.yaml erstellen
cat > .pre-commit-config.yaml <<EOF
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.0
    hooks:
      - id: gitleaks
EOF

# Aktivieren
pre-commit install
```

### 4. Security Champions
- **Verantwortlich:** Andy
- **Review Frequenz:** Wöchentlich
- **Escalation:** Bei CRITICAL sofort

## Troubleshooting

### ZAP Scan schlägt fehl
**Problem:** API Endpoint nicht erreichbar  
**Lösung:**
```bash
# Check API health
curl https://staging-api.overcloud.io/health

# Wenn down: Skip ZAP für diesen Run
# ZAP läuft nur wenn Environment deployed ist
```

### Trivy findet 100+ Vulnerabilities
**Problem:** Viele LOW/MEDIUM Findings  
**Lösung:**
```bash
# Fokus auf CRITICAL/HIGH
trivy fs . --severity CRITICAL,HIGH

# Ignore unfixed vulnerabilities
trivy fs . --ignore-unfixed
```

### Safety findet veraltete Packages
**Problem:** Dependencies sind outdated aber nicht vulnerable  
**Lösung:**
```bash
# Nur echte Vulnerabilities
poetry run safety check --json

# Update alle Dependencies
poetry update
```

## Weitere Tools (Optional)

### Snyk
- Commercial alternative zu Trivy/Safety
- Bessere Vulnerability Database
- Kostenpflichtig (Free Tier: 200 Tests/Monat)

### SonarQube
- Code Quality + Security
- SAST (Static Application Security Testing)
- Self-Hosted oder SonarCloud

### GitHub Advanced Security
- CodeQL (Semantic Analysis)
- Secret Scanning (GitHub Native)
- Kostenpflichtig für Private Repos

## Metrics & KPIs

**Security Posture Metrics:**
- 🎯 **Mean Time to Remediate (MTTR):** <7 Tage für HIGH, <1 Tag für CRITICAL
- 🎯 **Vulnerability Density:** <5 HIGH/CRITICAL pro 1000 LOC
- 🎯 **Security Scan Coverage:** 100% (jeder Push)
- 🎯 **Dependency Freshness:** <90 Tage outdated

**Dashboards:**
- GitHub Security Overview
- Custom Grafana Dashboard (später)

---

**Maintainer:** Andy Schwarz  
**Last Updated:** 2026-05-15  
**Review Frequency:** Monatlich
