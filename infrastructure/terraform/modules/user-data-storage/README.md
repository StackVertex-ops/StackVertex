# User Data Storage Module

Terraform Module für S3-basierte User-Daten-Speicherung in OverCloud.

## Features

- **Encrypted at Rest**: KMS-verschlüsselt mit automatischer Key Rotation
- **Versioning**: Aktiviert für Rollback-Fähigkeit
- **Lifecycle Management**: Auto-Cleanup alter Versionen und Multipart Uploads
- **Security**: Public Access komplett blockiert
- **CORS Support**: Für direkte Browser-Uploads
- **IAM Policies**: Vorkonfigurierte Rollen für Lambda/ECS
- **Audit Logging**: CloudWatch Log Group für Access Logs

## Usage

```hcl
module "user_data_storage" {
  source = "../../modules/user-data-storage"

  environment = "dev"

  # Optional
  version_retention_days    = 90
  enable_glacier_transition = false
  glacier_transition_days   = 365
  log_retention_days       = 30

  allowed_cors_origins = [
    "https://app.overcloud.io",
    "http://localhost:5173"
  ]

  tags = {
    Project = "OverCloud"
    Team    = "Platform"
  }
}
```

## Bucket Structure

```
overcloud-user-data-{env}/
├── {org_id}/
│   ├── {deployment_id}/
│   │   ├── docker-images/
│   │   │   └── app.tar.gz
│   │   ├── static-files/
│   │   │   ├── build/
│   │   │   └── config.json
│   │   └── metadata.json
```

## Outputs

- `bucket_name`: S3 Bucket Name
- `bucket_arn`: S3 Bucket ARN
- `kms_key_arn`: KMS Key ARN
- `lambda_role_arn`: IAM Role für Lambda (mit S3 Access)
- `s3_access_policy_arn`: IAM Policy für S3 Zugriff

## Security

- Alle Objekte werden automatisch KMS-verschlüsselt
- Public Access ist vollständig blockiert
- CORS nur für whitelisted Origins
- IAM Policies folgen Least Privilege Prinzip

## Lifecycle Rules

1. **Old Versions**: Gelöscht nach 90 Tagen (konfigurierbar)
2. **Incomplete Uploads**: Abgebrochen nach 7 Tagen
3. **Glacier Transition**: Optional nach 365 Tagen (deaktiviert per Default)

## Cost Optimization

- Lifecycle Rules reduzieren Storage Costs
- Glacier Transition für Long-Term Storage
- Bucket Key Encryption reduziert KMS Costs (~99%)
