# Testing Documentation

Dieses Verzeichnis enthält alle Dokumentationen zum Testing des Infrastructure Designers.

---

## Dateien

### [TESTING.md](./TESTING.md)
**Hauptdokumentation für Testing**

Enthält:
- Wie man Backend Tests ausführt
- Wie man Frontend Tests ausführt
- Wie man E2E Tests ausführt
- Test-Coverage Ziele
- CI/CD Integration
- Troubleshooting
- Performance Tests
- Best Practices

**→ Start hier wenn du Tests ausführen möchtest!**

---

## Weitere Test-Dokumentationen

### Test-Reports
- **[TEST_REPORT_INFRASTRUCTURE_DESIGNER.md](../../TEST_REPORT_INFRASTRUCTURE_DESIGNER.md)** - Aktuelle Test-Ergebnisse

### Bug-Tracking
- **[INFRASTRUCTURE_DESIGNER_BUGS.md](../../INFRASTRUCTURE_DESIGNER_BUGS.md)** - Gefundene Bugs & Issues

### Status-Reports
- **[INFRASTRUCTURE_DESIGNER_STATUS.md](../../INFRASTRUCTURE_DESIGNER_STATUS.md)** - Projekt-Status & Fortschritt

---

## Quick Start

### Backend Tests
```bash
cd /Users/andyschwarz/Documents/Privat/StackVertex/backend
./test_designer_api.sh
```

### Frontend Tests
```bash
cd /Users/andyschwarz/Documents/Privat/StackVertex/frontend
./test_infrastructure_designer.sh
```

### E2E Tests
```bash
cd /Users/andyschwarz/Documents/Privat/StackVertex/frontend
npx playwright test
```

---

## Test-Scripts

### Backend
- `/Users/andyschwarz/Documents/Privat/StackVertex/backend/test_designer_api.sh`
- `/Users/andyschwarz/Documents/Privat/StackVertex/backend/tests/test_terraform_api.py`
- `/Users/andyschwarz/Documents/Privat/StackVertex/backend/tests/test_cidr_api.py`

### Frontend
- `/Users/andyschwarz/Documents/Privat/StackVertex/frontend/test_infrastructure_designer.sh`
- `/Users/andyschwarz/Documents/Privat/StackVertex/frontend/tests/` (geplant)

---

**Mehr Details:** Siehe [TESTING.md](./TESTING.md)
