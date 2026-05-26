# Terraform Scripts

Dieses Verzeichnis enthält Helper-Scripts für Terraform-Operationen.

## Scripts

### `bootstrap-backend.sh`

Erstellt automatisch die S3 Backend-Infrastruktur für Terraform State Management.

**Was es macht:**
- ✅ Erstellt S3 Bucket für Terraform State (mit Versioning + Encryption)
- ✅ Erstellt DynamoDB Table für State Locking
- ✅ Generiert `backend.tf` für das entsprechende Environment
- ✅ Konfiguriert Security Best Practices (Public Access Block, Encryption)

**Usage:**
```bash
./bootstrap-backend.sh <environment> [region]
```

**Beispiele:**
```bash
# Dev Environment (eu-central-1)
./bootstrap-backend.sh dev

# Staging Environment (custom region)
./bootstrap-backend.sh staging eu-west-1

# Production Environment
./bootstrap-backend.sh prod
```

**Voraussetzungen:**
- AWS CLI installiert
- AWS Credentials konfiguriert (`aws configure`)
- Berechtigungen für S3 + DynamoDB

**Erstellt:**
- S3 Bucket: `stackvertex-<env>-terraform-state`
- DynamoDB Table: `stackvertex-<env>-terraform-lock`
- File: `../environments/<env>/backend.tf`

**Nach dem Bootstrap:**
```bash
cd ../environments/<env>
terraform init
```

## Sicherheitshinweise

### State Files
Terraform State Files enthalten **sensible Daten** (Passwörter, Secrets, IDs). Daher:
- ✅ State wird in S3 encrypted gespeichert (AES256)
- ✅ Versioning ist aktiviert (Rollback möglich)
- ✅ Public Access ist blockiert
- ✅ State Locking via DynamoDB (keine parallel executions)

### Backup
S3 Versioning ermöglicht Rollback:
```bash
# Alle Versionen anzeigen
aws s3api list-object-versions \
  --bucket stackvertex-prod-terraform-state \
  --prefix terraform.tfstate

# Spezifische Version wiederherstellen
aws s3api get-object \
  --bucket stackvertex-prod-terraform-state \
  --key terraform.tfstate \
  --version-id <version-id> \
  terraform.tfstate.backup
```

## Troubleshooting

### Error: "Bucket already exists"
**Problem:** Bucket Name ist global eindeutig und bereits vergeben.  
**Lösung:** Script prüft ob Bucket existiert und überspringt Creation.

### Error: "Access Denied"
**Problem:** AWS Credentials haben keine S3/DynamoDB Berechtigungen.  
**Lösung:** IAM Policy prüfen:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:CreateBucket",
        "s3:PutBucketVersioning",
        "s3:PutBucketEncryption",
        "s3:PutPublicAccessBlock",
        "dynamodb:CreateTable",
        "dynamodb:DescribeTable"
      ],
      "Resource": "*"
    }
  ]
}
```

### Error: "terraform init failed"
**Problem:** backend.tf existiert nicht oder ist falsch konfiguriert.  
**Lösung:** Bootstrap Script nochmal laufen lassen:
```bash
./bootstrap-backend.sh <env>
```

## Weitere Scripts (geplant)

- `migrate-state.sh` - Migriert State zwischen Backends
- `rotate-secrets.sh` - Rotiert Secrets in allen Environments
- `cleanup.sh` - Löscht alte Terraform State Versionen

---

**Maintainer:** Andy Schwarz  
**Last Updated:** 2026-05-15
