# Data Upload & Deployment System

## Übersicht

Das Data Upload & Deployment System ermöglicht es Usern, ihre Application Data (Docker Images, Static Files) zu OverCloud hochzuladen und anschließend in ihren eigenen AWS Accounts zu deployen.

## Architektur

```
┌─────────────┐      ┌──────────────┐      ┌─────────────────┐
│   Browser   │─────>│  OverCloud   │─────>│  Customer AWS   │
│             │      │   Backend    │      │    Account      │
│  Upload UI  │      │  (FastAPI)   │      │  (Deployment)   │
└─────────────┘      └──────────────┘      └─────────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │ OverCloud S3 │
                    │ (User Data)  │
                    └──────────────┘
```

### Komponenten

1. **User Data Storage (S3)**
   - S3 Bucket für temporäre Speicherung
   - KMS-verschlüsselt
   - Lifecycle Rules für Auto-Cleanup

2. **AWS Credentials Management**
   - Speichert Kunden AWS Credentials in Secrets Manager
   - Unterstützt AssumeRole (bevorzugt) und Access Keys
   - Credential Verification via STS

3. **Deployment Executor**
   - Generiert Terraform Code
   - Führt Terraform in Kunden-Account aus
   - Kopiert Daten von OverCloud S3 → Kunden ECR/S3

## Workflow

### 1. AWS Credentials hinzufügen

User fügt AWS Credentials für seinen Account hinzu:

**Option A: AssumeRole (Empfohlen)**
```bash
# User erstellt IAM Role in seinem AWS Account
aws iam create-role --role-name OverCloudDeploymentRole \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"AWS": "arn:aws:iam::{OverCloudAccountID}:root"},
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {"sts:ExternalId": "unique-external-id"}
      }
    }]
  }'

# Policies anhängen
aws iam attach-role-policy --role-name OverCloudDeploymentRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonEC2FullAccess
```

**Option B: Access Keys (Fallback)**
```bash
aws iam create-user --user-name overcloud-deployer
aws iam create-access-key --user-name overcloud-deployer
```

### 2. Application Data hochladen

User uploaded seine Daten zu OverCloud S3:

**Docker Image:**
- Upload `.tar.gz` File (max 5GB)
- Oder Import von DockerHub

**Static Files:**
- Upload via Drag & Drop
- Beliebige Dateitypen

**Storage Structure:**
```
overcloud-user-data-{env}/
├── {org_id}/
│   ├── {deployment_id}/
│   │   ├── docker-images/
│   │   │   └── app.tar.gz
│   │   └── static-files/
│   │       ├── build/
│   │       └── config.json
```

### 3. Deployment starten

User klickt auf "Deploy to AWS":

1. **Terraform Generation**
   - Architecture JSON → Terraform HCL
   - Provider: AWS (vorerst)

2. **Credential Retrieval**
   - Hole AWS Credentials aus Secrets Manager
   - Erstelle boto3 Session (AssumeRole oder Access Keys)

3. **Terraform Execution**
   ```bash
   terraform init
   terraform plan -out=plan.tfplan
   terraform apply -auto-approve plan.tfplan
   ```

4. **Data Copy**
   - Docker Images: OverCloud S3 → Kunden ECR
   - Static Files: OverCloud S3 → Kunden S3

5. **Verification**
   - Teste Deployment (Health Check)
   - Speichere Terraform State

## API Endpoints

### AWS Credentials

```http
POST /api/v1/aws-credentials
Content-Type: application/json

{
  "name": "Production AWS Account",
  "credential_type": "assume_role",
  "role_arn": "arn:aws:iam::123456789012:role/OverCloudDeploymentRole",
  "external_id": "unique-external-id",
  "region": "us-east-1"
}
```

**Response:**
```json
{
  "id": "cred_abc123",
  "org_id": "org_xyz789",
  "name": "Production AWS Account",
  "credential_type": "assume_role",
  "region": "us-east-1",
  "status": "active",
  "created_at": "2026-05-17T10:00:00Z"
}
```

### Data Upload

**Docker Image Upload:**
```http
POST /api/v1/data-upload/docker-image?deployment_id=dep_123
Content-Type: multipart/form-data

file: app.tar.gz
```

**Static Files Upload:**
```http
POST /api/v1/data-upload/files?deployment_id=dep_123
Content-Type: multipart/form-data

files: [build/index.html, config.json, ...]
```

**DockerHub Import:**
```http
POST /api/v1/data-upload/from-dockerhub
Content-Type: application/json

{
  "deployment_id": "dep_123",
  "image": "nginx:latest",
  "dockerhub_username": "user",
  "dockerhub_token": "token"
}
```

**List Uploaded Files:**
```http
GET /api/v1/data-upload/list/dep_123
```

## Security

### Credentials Management

- **Secrets Manager**: Alle sensitive Daten werden in AWS Secrets Manager gespeichert
- **KMS Encryption**: Encryption at Rest mit Customer Managed Key
- **No Plaintext**: Credentials werden NIEMALS im Klartext in Logs/DB gespeichert

### AssumeRole Best Practices

1. **External ID verwenden**: Verhindert Confused Deputy Problem
2. **Least Privilege**: Nur notwendige Permissions vergeben
3. **Session Duration**: Max 1 Stunde (default)
4. **CloudTrail**: Alle AssumeRole Calls werden geloggt

### S3 Security

- **Private Bucket**: Public Access komplett blockiert
- **KMS Encryption**: Server-Side Encryption für alle Objekte
- **Bucket Key**: Reduziert KMS Costs (~99%)
- **Versioning**: Aktiviert für Rollback-Fähigkeit

## Cost Optimization

### Storage Costs

- **Lifecycle Rules**: Alte Versionen nach 90 Tagen gelöscht
- **Incomplete Uploads**: Abgebrochen nach 7 Tagen
- **Glacier Transition**: Optional nach 365 Tagen (deaktiviert per Default)

### Compute Costs

- **Terraform Timeout**: Max 10 Minuten pro Deployment
- **Concurrent Deployments**: Max 5 parallel (konfigurierbar)

## Monitoring & Logging

### Audit Logs

Alle kritischen Aktionen werden geloggt:
- Credential Creation/Deletion
- Data Upload
- Deployment Start/Finish
- Credential Verification

### CloudWatch Logs

- Terraform Output
- Deployment Progress
- Error Messages

## Error Handling

### Deployment Fehler

**Terraform Init/Plan/Apply Failed:**
- Log Error Details
- Update Deployment Status: `failed`
- Sende Notification an User

**Credential Verification Failed:**
- Markiere Credential als `failed`
- User kann Re-Verification triggern

**Data Copy Failed:**
- Retry 3x mit Exponential Backoff
- Falls weiterhin fehlschlägt: Deployment rollback

## Rollback Strategy

### Terraform State

- State wird nach jedem Success in DynamoDB gespeichert
- Bei Rollback: `terraform destroy` mit altem State

### User Data

- Versioning in S3 aktiviert
- Alte Versionen für 90 Tage verfügbar

## Testing

### Unit Tests

```bash
pytest backend/tests/repositories/test_aws_credential.py
pytest backend/tests/services/test_aws_session.py
pytest backend/tests/services/test_deployment_executor.py
```

### Integration Tests

```bash
pytest backend/tests/integration/test_data_upload_flow.py
```

### E2E Test

1. Add AWS Credentials (Mock)
2. Upload Docker Image
3. Upload Static Files
4. Trigger Deployment
5. Verify Terraform Execution
6. Verify Data Copy

## Deployment

### Terraform Module

```hcl
module "user_data_storage" {
  source = "../../modules/user-data-storage"

  environment = "dev"
  
  version_retention_days = 90
  log_retention_days = 30
  
  allowed_cors_origins = [
    "https://app.overcloud.io",
    "http://localhost:5173"
  ]
}
```

### Environment Variables

```bash
# .env
USER_DATA_BUCKET=overcloud-user-data-dev
AWS_REGION=us-east-1
TERRAFORM_TIMEOUT=600
MAX_CONCURRENT_DEPLOYMENTS=5
```

## Future Enhancements

### Phase 2
- [ ] Multi-Cloud Support (Azure, GCP)
- [ ] Docker Compose Support
- [ ] Kubernetes Manifests Support
- [ ] Private Container Registry Integration

### Phase 3
- [ ] Automated Rollback on Failure
- [ ] Blue/Green Deployments
- [ ] Canary Deployments
- [ ] Cost Alerts (Budget Threshold)

## Troubleshooting

### "Credentials ungültig"

**Ursache:** AssumeRole oder Access Keys fehlgeschlagen

**Lösung:**
1. Prüfe Role ARN / Access Key ID
2. Prüfe External ID (bei AssumeRole)
3. Prüfe IAM Policies (Permissions)
4. Prüfe Trust Relationship (AssumeRole)

### "Docker Image Upload fehlgeschlagen"

**Ursache:** File zu groß oder falsches Format

**Lösung:**
1. Max 5GB Limit
2. Nur `.tar` oder `.tar.gz` erlaubt
3. Prüfe Netzwerk-Verbindung

### "Terraform Apply fehlgeschlagen"

**Ursache:** Ungültige Terraform Config oder fehlende Permissions

**Lösung:**
1. Prüfe Terraform Logs (CloudWatch)
2. Prüfe AWS Permissions (IAM)
3. Teste Terraform lokal (`terraform validate`)

## Support

Bei Fragen oder Problemen:
- GitHub Issues: https://github.com/overcloud/issues
- Docs: https://docs.overcloud.io
- Email: support@overcloud.io
