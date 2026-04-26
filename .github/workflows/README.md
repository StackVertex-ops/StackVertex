# GitHub Actions Workflows

Dieses Verzeichnis enthält alle CI/CD und Security Workflows für OverCloud.

## 📋 Workflows Übersicht

### 1. `test.yml` - Tests & Code Quality
**Trigger:** Push/PR auf main/master/develop

**Was wird geprüft:**
- ✅ pytest Unit Tests (alle Repositories)
- ✅ Test Coverage (Minimum: 80%)
- ✅ Code Linting (ruff)
- ✅ Type Checking (mypy)
- 📊 Coverage Report als PR Comment
- 📦 Coverage HTML Report als Artifact

**Matrix:** Python 3.11 + 3.12

### 2. `security.yml` - Security Scanning
**Trigger:** Push/PR auf main/master/develop + Wöchentlich (Montags 9:00 UTC)

**Security Checks:**
1. **Secret Scanning (GitGuardian)** - Erkennt AWS Keys, API Tokens, Passwörter
2. **Bandit** - Python Security Linter (SQL Injection, Unsafe Code)
3. **Safety** - Dependency Vulnerabilities (CVEs)
4. **Semgrep** - SAST (Static Application Security Testing)
5. **CodeQL** - GitHub Code Analysis (Deep semantic analysis)

### 3. `dependency-review.yml` - Dependency Security (PR only)
**Trigger:** Pull Requests auf main/master

**Prüft:** Neue Dependencies auf Vulnerabilities + License Compliance

## 🔧 Lokale Nutzung

### Tests
\`\`\`bash
cd backend
poetry run pytest tests/unit/ --cov=app/repositories --cov-report=term-missing
\`\`\`

### Security Scans
\`\`\`bash
poetry run bandit -r app
poetry run safety check
poetry run ruff check .
poetry run mypy app
\`\`\`

## 🔐 Erforderliche Secrets (Optional)

- `GITGUARDIAN_API_KEY` - GitGuardian Secret Scanning
- `CODECOV_TOKEN` - Coverage Reports

Beide optional, Workflows laufen auch ohne (`continue-on-error: true`).

## 📊 Status Badges

\`\`\`markdown
[![Tests](https://github.com/AndySchw/OverCloud/actions/workflows/test.yml/badge.svg)](https://github.com/AndySchw/OverCloud/actions/workflows/test.yml)
[![Security](https://github.com/AndySchw/OverCloud/actions/workflows/security.yml/badge.svg)](https://github.com/AndySchw/OverCloud/actions/workflows/security.yml)
\`\`\`

## 🚨 Bei Failures

**Coverage < 80%:** Siehe `htmlcov/index.html` Artifact  
**Secrets gefunden:** Secret rotieren (NIEMALS aus History löschen!)  
**Vulnerable Dependency:** \`poetry update <package>\`  
**Security Issue:** Artifact Reports anschauen

Details: Siehe Workflow Logs
