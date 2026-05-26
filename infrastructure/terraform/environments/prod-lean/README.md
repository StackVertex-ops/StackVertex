# Production Lean Environment

**Zweck:** Kostengünstige Production für 0-100 User  
**Kosten:** ~$50-80/Monat  
**Wann nutzen:** MVP, Early Stage, < 100 zahlende User

---

## Unterschied zu `prod/`

| Feature | prod/ | **prod-lean/** |
|---------|-------|----------------|
| **Aurora** | ✅ ($100-200) | **❌ (DynamoDB only)** |
| **NAT Gateway** | ✅ ($40-60) | **❌ (Public Subnets)** |
| **WAF** | ✅ Full ($30) | **❌ (CloudFront Basic)** |
| **GuardDuty** | ✅ ($10) | **❌ (später)** |
| **Security Hub** | ✅ ($5) | **❌** |
| **Cross-Region Backup** | ✅ ($20) | **❌ (PITR only)** |
| **Lambda Memory** | 2048 MB | **512 MB** |
| **Monitoring** | Full | **Basic** |
| **Kosten** | $250-450 | **$50-80** |

---

## Was du BEKOMMST

### ✅ Sicherheit (Basics)
- TLS/HTTPS (CloudFront)
- IAM Roles (no keys)
- DynamoDB Encryption
- CloudFront Basic DDoS Protection
- CloudWatch Alarms (Critical only)

### ✅ High Availability
- Lambda Auto-Scale (Multi-AZ)
- DynamoDB (Multi-AZ automatic)
- CloudFront (Global CDN)
- **99.9% Uptime SLA möglich**

### ✅ Backup
- DynamoDB PITR (35 Tage)
- S3 Versioning (30 Tage)

### ✅ Monitoring
- CloudWatch Basic Alarms
- Sentry (Error Tracking)
- UptimeRobot (Uptime)

---

## Was du NICHT bekommst (aber später hinzufügen kannst)

### ⏳ Advanced Security
- Kein WAF (DDoS bei 50 Usern unrealistisch)
- Kein GuardDuty (Threat Detection nice-to-have)
- Kein Security Hub (Compliance later)

### ⏳ Disaster Recovery
- Kein Cross-Region Backup (35-Tage-PITR reicht)
- Single Region only

### ⏳ Advanced Monitoring
- Kein PagerDuty (Email Alerts reichen)
- Kein X-Ray Tracing

---

## Upgrade-Path

### Wann von prod-lean → prod wechseln?

**Trigger 1: User-Wachstum**
- 100+ zahlende User
- 1000+ Requests/Tag

**Trigger 2: Revenue**
- $5K MRR (Monthly Recurring Revenue)
- Profitabel

**Trigger 3: Security Requirements**
- Enterprise Kunden (brauchen SOC 2)
- Regulierte Industrie (Finance, Healthcare)
- DDoS Attacks (dann WAF nötig)

### Upgrade-Prozess (< 2h Downtime)

```bash
# 1. Backup erstellen
cd environments/prod-lean
terraform output dynamodb_table_name
aws dynamodb create-backup ...

# 2. prod/ konfigurieren
cd ../prod
# variables.tf anpassen

# 3. Import existing resources
terraform import module.database-dynamodb.aws_dynamodb_table.main ...

# 4. Apply
terraform plan
terraform apply

# 5. Verify
curl https://api.stackvertex.io/health
```

---

## Deployment

```bash
cd infrastructure/terraform/environments/prod-lean

# 1. Init
terraform init

# 2. Plan
terraform plan -out=prod-lean.tfplan

# 3. Review
less prod-lean.tfplan

# 4. Apply
terraform apply prod-lean.tfplan

# 5. Verify
terraform output
curl https://api.stackvertex.io/health
```

---

## Kosten-Monitoring

**CloudWatch Budget Alarm:**
```bash
# Alert wenn Kosten > $100/Monat
aws budgets create-budget \
  --budget BudgetName=prod-lean-monthly \
  --budget-limit=100 \
  --time-unit=MONTHLY
```

**Empfohlene Limits:**
- Budget: $100/Monat
- Alert bei $80 (80%)
- Hard Stop bei $120 (120%)

---

## FAQ

**Q: Ist prod-lean wirklich production-ready?**  
A: Ja! Für 0-100 User absolut. Viele erfolgreiche Startups starten so.

**Q: Was wenn ich plötzlich viral gehe?**  
A: Lambda auto-scales bis 1000 concurrent (kostenlos). DynamoDB auch. Du zahlst nur mehr, kaputtgehen kann nichts.

**Q: Kein WAF = unsicher?**  
A: Nein. CloudFront hat Basic DDoS Protection. Bei 50 Usern kein Target für Angreifer.

**Q: Wann muss ich upgraden?**  
A: Wenn Budget erlaubt ODER Security-Anforderungen steigen (Enterprise Kunden).

---

**Erstellt:** 2026-05-18  
**Für:** MVP / Early Stage (0-100 User)  
**Kosten:** ~$50-80/Monat
