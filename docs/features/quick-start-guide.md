# Quick Start Guide - Data Upload & Deployment

## Für User

### 1. AWS Credentials hinzufügen

**Browser:** `https://app.stackvertex.io/aws-credentials.html`

**Option A: AssumeRole (Empfohlen)**

1. Erstelle IAM Role in deinem AWS Account:
   ```bash
   aws iam create-role --role-name StackVertexDeploymentRole \
     --assume-role-policy-document file://trust-policy.json
   ```

2. Trust Policy (`trust-policy.json`):
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [{
       "Effect": "Allow",
       "Principal": {"AWS": "arn:aws:iam::OVERCLOUD_ACCOUNT_ID:root"},
       "Action": "sts:AssumeRole",
       "Condition": {
         "StringEquals": {"sts:ExternalId": "YOUR_UNIQUE_EXTERNAL_ID"}
       }
     }]
   }
   ```

3. Permissions anhängen:
   ```bash
   aws iam attach-role-policy --role-name StackVertexDeploymentRole \
     --policy-arn arn:aws:iam::aws:policy/AmazonEC2FullAccess
   
   aws iam attach-role-policy --role-name StackVertexDeploymentRole \
     --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess
   ```

4. In StackVertex eintragen:
   - Role ARN: `arn:aws:iam::YOUR_ACCOUNT_ID:role/StackVertexDeploymentRole`
   - External ID: `YOUR_UNIQUE_EXTERNAL_ID`

**Option B: Access Keys**

```bash
aws iam create-user --user-name stackvertex-deployer
aws iam create-access-key --user-name stackvertex-deployer
# Kopiere Access Key ID und Secret Access Key
```

### 2. Application Data hochladen

**Browser:** `https://app.stackvertex.io/deployment-data.html?id=DEPLOYMENT_ID`

**Docker Image:**
- Lokale `.tar.gz` Datei uploaden
- Oder von DockerHub importieren: `nginx:latest`

**Static Files:**
- Drag & Drop in Browser
- Mehrere Dateien gleichzeitig möglich

### 3. Deployment starten

Click "Deploy to AWS" Button → Deployment läuft automatisch

---

## Für Entwickler

### Backend Setup

1. **Dependencies installieren:**
   ```bash
   cd backend
   poetry install
   ```

2. **Environment Variables:**
   ```bash
   # .env
   USER_DATA_BUCKET=stackvertex-user-data-dev
   AWS_REGION=us-east-1
   SECRET_KEY=your-secret-key-min-32-chars
   ```

3. **Backend starten:**
   ```bash
   poetry run python -m app.main
   # oder
   poetry run uvicorn app.main:app --reload
   ```

### Frontend Setup

1. **Dependencies installieren:**
   ```bash
   cd frontend
   npm install
   ```

2. **Dev Server starten:**
   ```bash
   npm run dev
   # Läuft auf http://localhost:5173
   ```

### Terraform Module deployen

```bash
cd infrastructure/terraform/environments/dev

# User Data Storage Module
terraform init
terraform plan
terraform apply

# Outputs:
# - bucket_name: stackvertex-user-data-dev
# - kms_key_arn: arn:aws:kms:...
```

### Tests ausführen

```bash
cd backend

# Alle Tests
poetry run pytest

# Spezifische Tests
poetry run pytest tests/repositories/test_aws_credential.py
poetry run pytest tests/services/test_aws_session.py

# Mit Coverage
poetry run pytest --cov=app --cov-report=html
```

### API Testen

**AWS Credentials erstellen:**
```bash
curl -X POST http://localhost:8000/api/v1/aws-credentials \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Credential",
    "credential_type": "assume_role",
    "role_arn": "arn:aws:iam::123456789012:role/TestRole",
    "external_id": "test-external-id",
    "region": "us-east-1"
  }'
```

**Credentials verifizieren:**
```bash
curl -X POST http://localhost:8000/api/v1/aws-credentials/CRED_ID/verify \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Docker Image uploaden:**
```bash
curl -X POST "http://localhost:8000/api/v1/data-upload/docker-image?deployment_id=dep_123" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@app.tar.gz"
```

**Hochgeladene Files auflisten:**
```bash
curl http://localhost:8000/api/v1/data-upload/list/dep_123 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Troubleshooting

### "Credentials ungültig"

```bash
# Teste Credentials manuell
aws sts assume-role \
  --role-arn arn:aws:iam::123456789012:role/TestRole \
  --role-session-name test \
  --external-id your-external-id

# Prüfe Trust Relationship
aws iam get-role --role-name StackVertexDeploymentRole
```

### "Upload fehlgeschlagen"

```bash
# Prüfe S3 Bucket
aws s3 ls s3://stackvertex-user-data-dev/

# Prüfe KMS Key
aws kms describe-key --key-id alias/stackvertex-user-data-dev
```

### "Terraform Apply fehlgeschlagen"

```bash
# Lokaler Test
cd /tmp/terraform-test
terraform validate
terraform plan

# Prüfe AWS Permissions
aws ec2 describe-regions
aws s3 ls
```

---

## Nützliche Commands

### User Data Storage

```bash
# Liste alle Uploads
aws s3 ls s3://stackvertex-user-data-dev/ --recursive

# Lösche altes Deployment
aws s3 rm s3://stackvertex-user-data-dev/org_123/dep_456/ --recursive

# Prüfe Encryption
aws s3api head-object \
  --bucket stackvertex-user-data-dev \
  --key org_123/dep_456/docker-images/app.tar.gz
```

### Secrets Manager

```bash
# Liste alle Secrets
aws secretsmanager list-secrets

# Hole Secret (für Debugging)
aws secretsmanager get-secret-value \
  --secret-id stackvertex/aws-credentials/cred_123

# Lösche Secret (7 Tage Recovery Window)
aws secretsmanager delete-secret \
  --secret-id stackvertex/aws-credentials/cred_123
```

### CloudWatch Logs

```bash
# Tail Deployment Logs
aws logs tail /aws/lambda/stackvertex-deployment --follow

# Filter für Errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/stackvertex-deployment \
  --filter-pattern "ERROR"
```

---

## Next Steps

1. Teste kompletten Deployment Flow
2. Implementiere Docker Image Copy (S3 → ECR)
3. Füge Deployment Status Updates hinzu (WebSocket)
4. Implementiere Rollback Funktion
5. Füge Cost Estimation vor Deploy hinzu
6. Multi-Cloud Support (Azure, GCP)
