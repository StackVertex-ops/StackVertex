# OverCloud - Manuelle Test-Checkliste

**Version:** 1.0.0  
**Datum:** 2026-05-18  
**Zweck:** Vor Go-Live alle kritischen Features manuell testen

---

## 📋 Wie diese Checkliste nutzen

**Format:**
```
- [ ] Test-Name
  **Test:** Was tun?
  **Erwartung:** Was sollte passieren?
  **Ergebnis:** [ ] ✅ Pass / [ ] ❌ Fail
  **Notes:** Deine Notizen hier...
```

**Ausfüllen:**
1. Test durchführen
2. `[x]` wenn erledigt
3. Ergebnis eintragen (✅ oder ❌)
4. Notes bei Problemen

---

## 🔐 1. Authentication & Authorization

### 1.1 User Registration
- [ ] **Neuen User registrieren**
  - **Test:** Gehe zu `/register`, fülle Formular aus
  - **Email:** test-user-1@example.com
  - **Password:** SecurePass123!
  - **Erwartung:** 201 Created, Redirect zu Dashboard
  - **Ergebnis:** [ ] ✅ Pass / [ ] ❌ Fail
  - **Notes:** 

### 1.2 User Login
- [ ] **Login mit registriertem User**
  - **Test:** Gehe zu `/login`, login mit test-user-1
  - **Erwartung:** 200 OK, JWT Token in Cookie, Dashboard sichtbar
  - **Ergebnis:** [ ] ✅ Pass / [ ] ❌ Fail
  - **Notes:** 

### 1.3 Invalid Login
- [ ] **Login mit falschem Passwort**
  - **Test:** Login mit test-user-1, falsches Password
  - **Erwartung:** 401 Unauthorized, Error-Message
  - **Ergebnis:** [ ] ✅ Pass / [ ] ❌ Fail
  - **Notes:** 

### 1.4 Refresh Token
- [ ] **Access Token Refresh**
  - **Test:** Warte 16 Minuten (Token Expiry), mache Request
  - **Erwartung:** Auto-Refresh via Refresh Token, keine Re-Login nötig
  - **Ergebnis:** [ ] ✅ Pass / [ ] ❌ Fail
  - **Notes:** 

### 1.5 Logout
- [ ] **User Logout**
  - **Test:** Klicke Logout Button
  - **Erwartung:** Cookie gelöscht, Redirect zu Login
  - **Ergebnis:** [ ] ✅ Pass / [ ] ❌ Fail
  - **Notes:** 

### 1.6 Protected Routes
- [ ] **Zugriff ohne Login**
  - **Test:** Gehe direkt zu `/dashboard` ohne Login
  - **Erwartung:** Redirect zu `/login`
  - **Ergebnis:** [ ] ✅ Pass / [ ] ❌ Fail
  - **Notes:** 

### 1.7 RBAC - SuperAdmin
- [ ] **SuperAdmin Zugriff**
  - **Test:** Login als SuperAdmin, gehe zu `/admin`
  - **Erwartung:** Admin-Panel sichtbar
  - **Ergebnis:** [ ] ✅ Pass / [ ] ❌ Fail
  - **Notes:** 

### 1.8 RBAC - Normal User
- [ ] **Normal User blocked von Admin**
  - **Test:** Login als Normal User, gehe zu `/admin`
  - **Erwartung:** 403 Forbidden
  - **Ergebnis:** [ ] ✅ Pass / [ ] ❌ Fail
  - **Notes:** 

---

## 🏢 2. Organisation Management

### 2.1 Create Organisation
- [ ] **Neue Organisation erstellen**
  - **Test:** Dashboard → Create Organisation
  - **Name:** "Test Company GmbH"
  - **Type:** "business"
  - **Erwartung:** 201 Created, Org in Liste
  - **Ergebnis:** [ ] ✅ Pass / [ ] ❌ Fail
  - **Notes:** 

### 2.2 List Organisations
- [ ] **Organisationen auflisten**
  - **Test:** Dashboard → Organisations
  - **Erwartung:** Liste mit "Test Company GmbH"
  - **Ergebnis:** [ ] ✅ Pass / [ ] ❌ Fail
  - **Notes:** 

### 2.3 Update Organisation
- [ ] **Organisation bearbeiten**
  - **Test:** Edit "Test Company GmbH", ändere Name zu "Test AG"
  - **Erwartung:** 200 OK, Name aktualisiert
  - **Ergebnis:** [ ] ✅ Pass / [ ] ❌ Fail
  - **Notes:** 

### 2.4 Delete Organisation
- [ ] **Organisation löschen**
  - **Test:** Delete "Test AG"
  - **Erwartung:** 204 No Content, Org verschwunden
  - **Ergebnis:** [ ] ✅ Pass / [ ] ❌ Fail
  - **Notes:** 

---

## 🏗️ 3. Architecture Designer

### 3.1 Create Architecture (Form)
- [ ] **Architektur via Formular erstellen**
  - **Test:** New Architecture → Formular ausfüllen
  - **Name:** "Test Web App"
  - **Type:** "web-application"
  - **Erwartung:** JSON generiert, gespeichert
  - **Ergebnis:** [ ] ✅ Pass / [ ] ❌ Fail
  - **Notes:** 

### 3.2 Create Architecture (Canvas)
- [ ] **Architektur via Canvas erstellen**
  - **Test:** New Architecture → Visual Builder
  - **Action:** Drag VPC, EC2, RDS auf Canvas
  - **Erwartung:** Components sichtbar, Relationships
  - **Ergebnis:** [ ] ✅ Pass / [ ] ❌ Fail
  - **Notes:** 

### 3.3 Load Template
- [ ] **Template laden**
  - **Test:** Load Template "Web App (VPC + EC2 + RDS)"
  - **Erwartung:** Canvas gefüllt mit Components
  - **Ergebnis:** [ ] ✅ Pass / [ ] ❌ Fail
  - **Notes:** 

### 3.4 Edit Architecture
- [ ] **Bestehende Architektur bearbeiten**
  - **Test:** Öffne "Test Web App", ändere EC2 Instance Type
  - **Erwartung:** Änderung gespeichert
  - **Ergebnis:** [ ] ✅ Pass / [ ] ❌ Fail
  - **Notes:** 

### 3.5 Validate Architecture
- [ ] **Architektur validieren**
  - **Test:** Validate Button → API Call
  - **Erwartung:** Validation Results (Errors, Warnings)
  - **Ergebnis:** [ ] ✅ Pass / [ ] ❌ Fail
  - **Notes:** 

### 3.6 Export JSON
- [ ] **JSON exportieren**
  - **Test:** Export JSON Button
  - **Erwartung:** Download `architecture.json`
  - **Ergebnis:** [ ] ✅ Pass / [ ] ❌ Fail
  - **Notes:** 

### 3.7 Delete Architecture
- [ ] **Architektur löschen**
  - **Test:** Delete "Test Web App"
  - **Erwartung:** 204 No Content, verschwindet aus Liste
  - **Ergebnis:** [ ] ✅ Pass / [ ] ❌ Fail
  - **Notes:** 

---

## 🚀 4. Terraform Generation

### 4.1 Generate Terraform
- [ ] **Terraform Code generieren**
  - **Test:** Architecture → Generate Terraform
  - **Erwartung:** HCL Code angezeigt
  - **Ergebnis:** [ ] ✅ Pass / [ ] ❌ Fail
  - **Notes:** 

### 4.2 Download Terraform
- [ ] **Terraform als .zip downloaden**
  - **Test:** Download Terraform Button
  - **Erwartung:** `terraform-<id>.zip` heruntergeladen
  - **Ergebnis:** [ ] ✅ Pass / [ ] ❌ Fail
  - **Notes:** 

### 4.3 Terraform Validation
- [ ] **Terraform lokal validieren**
  - **Test:** Unzip, `terraform init`, `terraform validate`
  - **Erwartung:** "Success! The configuration is valid."
  - **Ergebnis:** [ ] ✅ Pass / [ ] ❌ Fail
  - **Notes:** 

---

## 💰 5. Billing & Pricing

### 5.1 View Pricing Page
- [ ] **Pricing Page öffnen**
  - **Test:** Gehe zu `/pricing`
  - **Erwartung:** 4 Tiers (PAYG, Starter, Pro, Enterprise)
  - **Ergebnis:** [ ] ✅ Pass / [ ] ❌ Fail
  - **Notes:** 

### 5.2 Cost Calculator
- [ ] **Kostenrechner nutzen**
  - **Test:** Eingabe: AWS Costs $100, 5 Deployments
  - **Erwartung:** Total Cost berechnet (Base Fee + Markup)
  - **Ergebnis:** [ ] ✅ Pass / [ ] ❌ Fail
  - **Notes:** 

### 5.3 Apply Voucher
- [ ] **Gutschein anwenden**
  - **Test:** Billing → Voucher Code "TEST2026"
  - **Erwartung:** Discount applied, neue Summe
  - **Ergebnis:** [ ] ✅ Pass / [ ] ❌ Fail
  - **Notes:** 

### 5.4 Remove Voucher
- [ ] **Gutschein entfernen**
  - **Test:** Remove Voucher Button
  - **Erwartung:** Discount entfernt, Summe zurück
  - **Ergebnis:** [ ] ✅ Pass / [ ] ❌ Fail
  - **Notes:** 

### 5.5 Subscription Upgrade
- [ ] **Subscription upgraden**
  - **Test:** Upgrade von PAYG → PRO
  - **Erwartung:** Plan updated, neue Quota
  - **Ergebnis:** [ ] ✅ Pass / [ ] ❌ Fail
  - **Notes:** 

---

## 🔒 6. Security Tests

### 6.1 CSRF Protection
- [ ] **CSRF Token validieren**
  - **Test:** POST Request ohne CSRF Token (via curl)
  - **Erwartung:** 403 Forbidden
  - **Ergebnis:** [ ] ✅ Pass / [ ] ❌ Fail
  - **Notes:** 

### 6.2 Rate Limiting
- [ ] **Rate Limit erreichen**
  - **Test:** 100× Request in 1 Minute zu `/api/v1/auth/login`
  - **Erwartung:** 429 Too Many Requests
  - **Ergebnis:** [ ] ✅ Pass / [ ] ❌ Fail
  - **Notes:** 

### 6.3 SQL Injection (not applicable)
- [ ] **SQL Injection Test**
  - **Test:** Login mit `' OR 1=1--` als Email
  - **Erwartung:** 422 Unprocessable (Pydantic Validation)
  - **Note:** DynamoDB = kein SQL, aber Input Validation testen
  - **Ergebnis:** [ ] ✅ Pass / [ ] ❌ Fail
  - **Notes:** 

### 6.4 XSS Protection
- [ ] **XSS Test**
  - **Test:** Organisation Name = `<script>alert('XSS')</script>`
  - **Erwartung:** Escaped in HTML, kein Alert
  - **Ergebnis:** [ ] ✅ Pass / [ ] ❌ Fail
  - **Notes:** 

### 6.5 HTTPS Redirect
- [ ] **HTTP → HTTPS Redirect**
  - **Test:** Gehe zu `http://overcloud.io`
  - **Erwartung:** 301 Redirect zu `https://overcloud.io`
  - **Ergebnis:** [ ] ✅ Pass / [ ] ❌ Fail
  - **Notes:** 

### 6.6 Security Headers
- [ ] **Security Headers prüfen**
  - **Test:** `curl -I https://api.overcloud.io/health`
  - **Check:**
    - `X-Content-Type-Options: nosniff`
    - `X-Frame-Options: DENY`
    - `Strict-Transport-Security: ...`
  - **Erwartung:** Alle Header vorhanden
  - **Ergebnis:** [ ] ✅ Pass / [ ] ❌ Fail
  - **Notes:** 

---

## 🔔 7. Monitoring & Alerts

### 7.1 Health Endpoint
- [ ] **Health Check**
  - **Test:** `curl https://api.overcloud.io/health`
  - **Erwartung:** `{"status":"healthy","version":"0.1.0"}`
  - **Ergebnis:** [ ] ✅ Pass / [ ] ❌ Fail
  - **Notes:** 

### 7.2 Sentry Error
- [ ] **Sentry Test Error**
  - **Test:** Trigger Test-Error (falls Test-Endpoint vorhanden)
  - **Erwartung:** Error erscheint in Sentry Dashboard
  - **Ergebnis:** [ ] ✅ Pass / [ ] ❌ Fail
  - **Notes:** 

### 7.3 CloudWatch Logs
- [ ] **CloudWatch Logs prüfen**
  - **Test:** AWS Console → CloudWatch → Logs → `/aws/lambda/overcloud-prod-backend`
  - **Erwartung:** Logs von letzten Requests
  - **Ergebnis:** [ ] ✅ Pass / [ ] ❌ Fail
  - **Notes:** 

### 7.4 UptimeRobot Alert
- [ ] **UptimeRobot Test**
  - **Test:** Checke UptimeRobot Dashboard
  - **Erwartung:** Monitor "UP", 99%+ Uptime
  - **Ergebnis:** [ ] ✅ Pass / [ ] ❌ Fail
  - **Notes:** 

---

## 🌐 8. Frontend Tests

### 8.1 Landing Page Load
- [ ] **Landing Page Performance**
  - **Test:** Öffne `https://overcloud.io` (inkognito)
  - **Check:** Chrome DevTools → Network
  - **Erwartung:** Load Time < 2s, Lighthouse Score > 90
  - **Ergebnis:** [ ] ✅ Pass / [ ] ❌ Fail
  - **Notes:** 

### 8.2 Mobile Responsive
- [ ] **Mobile View**
  - **Test:** Chrome DevTools → Device Toolbar → iPhone 12
  - **Erwartung:** Layout responsive, alles lesbar
  - **Ergebnis:** [ ] ✅ Pass / [ ] ❌ Fail
  - **Notes:** 

### 8.3 Browser Compatibility
- [ ] **Chrome**
  - **Test:** Öffne in Chrome
  - **Erwartung:** Funktioniert
  - **Ergebnis:** [ ] ✅ Pass / [ ] ❌ Fail

- [ ] **Firefox**
  - **Test:** Öffne in Firefox
  - **Erwartung:** Funktioniert
  - **Ergebnis:** [ ] ✅ Pass / [ ] ❌ Fail

- [ ] **Safari**
  - **Test:** Öffne in Safari
  - **Erwartung:** Funktioniert
  - **Ergebnis:** [ ] ✅ Pass / [ ] ❌ Fail

---

## 🗄️ 9. Database & Backup

### 9.1 DynamoDB Read/Write
- [ ] **DynamoDB Operationen**
  - **Test:** Create Architecture (schreibt in DynamoDB)
  - **Check:** AWS Console → DynamoDB → Items
  - **Erwartung:** Neues Item sichtbar
  - **Ergebnis:** [ ] ✅ Pass / [ ] ❌ Fail
  - **Notes:** 

### 9.2 Point-in-Time Recovery
- [ ] **PITR aktiviert**
  - **Test:** AWS Console → DynamoDB → Backups → PITR
  - **Erwartung:** "Enabled"
  - **Ergebnis:** [ ] ✅ Pass / [ ] ❌ Fail
  - **Notes:** 

### 9.3 Backup Test
- [ ] **Backup durchführen**
  - **Test:** `./infrastructure/terraform/scripts/test-backup-restore.sh prod`
  - **Erwartung:** ✅ BACKUP RESTORE TEST PASSED
  - **Ergebnis:** [ ] ✅ Pass / [ ] ❌ Fail
  - **Notes:** 

---

## 📊 10. Performance Tests

### 10.1 API Response Time
- [ ] **Latency Check**
  - **Test:** `curl -w "@curl-format.txt" https://api.overcloud.io/health`
  - **Erwartung:** Response Time < 200ms
  - **Ergebnis:** [ ] ✅ Pass / [ ] ❌ Fail
  - **Notes:** 

### 10.2 Concurrent Users
- [ ] **Load Test (optional)**
  - **Test:** 10 User gleichzeitig Architectures erstellen
  - **Tool:** Apache Bench oder Postman Runner
  - **Erwartung:** Keine Errors, < 500ms Response
  - **Ergebnis:** [ ] ✅ Pass / [ ] ❌ Fail
  - **Notes:** 

---

## ✅ Summary

**Total Tests:** 50+
**Passed:** _____ / _____
**Failed:** _____ / _____
**Completion:** _____ %

**Critical Failures (MUST FIX before Go-Live):**
- 

**Minor Issues (can fix later):**
- 

**Notes:**
- 

**Tester:** _______________
**Date:** _______________
**Sign-off:** [ ] Ready for Production

---

**Version History:**
- 1.0.0 (2026-05-18) - Initial Checklist
