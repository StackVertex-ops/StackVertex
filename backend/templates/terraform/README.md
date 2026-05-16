# OverCloud Terraform Templates

Production-ready Terraform templates (Jinja2) für alle OverCloud Blueprints.

## Übersicht

| Template | Blueprint | Beschreibung |
|----------|-----------|--------------|
| `static_website.tf.j2` | Static Website | S3 + CloudFront für statische Websites |
| `spa.tf.j2` | Single Page Application | S3 Frontend + API Gateway + Lambda + DynamoDB |
| `simple_api.tf.j2` | Simple REST API | API Gateway + Lambda + DynamoDB (CRUD API) |
| `three_tier_web.tf.j2` | Three-Tier Web App | VPC + ALB + EC2 Auto Scaling + RDS |
| `wordpress.tf.j2` | WordPress | EC2 + RDS MySQL + EFS + CloudFront |

## Template-Struktur

Alle Templates folgen dieser Struktur:

```hcl
# 1. Terraform Provider Configuration
terraform {
  required_version = ">= 1.0"
  backend "s3" { ... }
}

# 2. Variables (aus Blueprint form_schema)
variable "app_name" { ... }
variable "..." { ... }

# 3. Data Sources (AMIs, AZs, etc.)
data "aws_ami" "..." { ... }

# 4. Resources (VPC, EC2, RDS, etc.)
resource "aws_vpc" "main" { ... }

# 5. Outputs (URLs, IDs, Deployment Instructions)
output "deployment_instructions" { ... }
```

## Jinja2 Variables

Alle Blueprint `form_schema` Felder werden als Jinja2 Variables übergeben:

```jinja2
variable "app_name" {
  default = "{{ app_name }}"
}

{% if enable_auth %}
# Cognito Configuration
resource "aws_cognito_user_pool" "main" { ... }
{% endif %}
```

### Common Variables (alle Templates)

- `project_name` - Projektname
- `blueprint_id` - Blueprint ID (z.B. "spa", "wordpress")
- `created_at` - Timestamp
- `aws_region` - AWS Region (default: us-east-1)
- `environment` - Environment (dev, staging, prod)
- `state_bucket_name` - S3 Bucket für Terraform State

### Blueprint-spezifische Variables

Siehe jeweilige Blueprint-Definition in `backend/app/data/blueprints/*.py`.

## Lambda Placeholder

Die Templates referenzieren `lambda_placeholder.zip`, das beim ersten `terraform apply` deployed wird.

**Wichtig:** Nutzer müssen diesen Placeholder mit echtem Code ersetzen:

```bash
# Lambda Code deployen
zip function.zip index.js
aws lambda update-function-code \
  --function-name YOUR_FUNCTION_NAME \
  --zip-file fileb://function.zip
```

Placeholder Code:
- `lambda_placeholder.js` - Node.js Placeholder
- `lambda_placeholder.py` - Python Placeholder

## WordPress User Data Script

`wordpress_userdata.sh` wird als Terraform `templatefile()` eingebunden und führt folgende Schritte aus:

1. System Update (Amazon Linux 2023)
2. PHP 8.2 + Nginx Installation
3. WordPress Download & Installation
4. EFS Mount für `/wp-content/uploads`
5. RDS MySQL Verbindung
6. WP-CLI Installation
7. SSL via Let's Encrypt (optional)
8. CloudWatch Agent Setup
9. Empfohlene Plugins (Wordfence, WP Super Cache)

## Remote State Backend

Alle Templates nutzen S3 Remote State:

```hcl
backend "s3" {
  bucket         = "{{ state_bucket_name }}"
  key            = "{{ project_name }}/terraform.tfstate"
  region         = "{{ aws_region }}"
  encrypt        = true
  dynamodb_table = "terraform-locks"
}
```

**Setup:**

```bash
# S3 Bucket für Terraform State erstellen
aws s3 mb s3://overcloud-terraform-state

# DynamoDB Table für State Locking
aws dynamodb create-table \
  --table-name terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
```

## Rendering Prozess

1. **User füllt Blueprint Form aus** (Frontend)
2. **OverCloud Backend rendert Template:**
   ```python
   from jinja2 import Environment, FileSystemLoader
   
   env = Environment(loader=FileSystemLoader('templates/terraform'))
   template = env.get_template(f'{blueprint_id}.tf.j2')
   
   rendered = template.render(
       app_name=form_data['app_name'],
       domain_name=form_data['domain_name'],
       # ... alle anderen form_schema Felder
   )
   ```
3. **Terraform Code wird generiert** und gespeichert
4. **User kann deployen** via `terraform apply`

## Security Best Practices

Alle Templates implementieren:

✅ **Encryption at Rest:**
- S3 Buckets: AES256
- RDS: Storage Encryption
- EBS Volumes: Encrypted

✅ **Encryption in Transit:**
- HTTPS via ACM Certificates
- RDS TLS Connections
- API Gateway HTTPS only

✅ **Least Privilege IAM:**
- IAM Roles (keine Access Keys)
- Service-spezifische Permissions
- AssumeRole für Cross-Account Access

✅ **Network Security:**
- VPC mit Private Subnets
- Security Groups (nicht 0.0.0.0/0 für sensible Services)
- NAT Gateway für outbound traffic

✅ **Secrets Management:**
- AWS Secrets Manager für DB Passwords
- Keine Secrets in Terraform State (wo möglich)
- Random Passwords generiert via Terraform

✅ **Monitoring:**
- CloudWatch Logs für alle Services
- CloudWatch Alarms für kritische Metriken
- CloudWatch Agent auf EC2 Instances

## Cost Optimization

Templates nutzen:

- **Latest Generation Instances:** t3/t4g statt t2
- **gp3 EBS Volumes:** Günstiger als gp2
- **DynamoDB On-Demand:** Pay-per-use für variable Workloads
- **Lifecycle Policies:** S3 Lifecycle Rules für alte Versionen
- **NAT Gateway:** Single NAT statt Multi-AZ (Kosteneinsparung)

**Tipp für Production:**
- Reserved Instances für konstante Workloads (-40% Kosten)
- Savings Plans für EC2/Lambda
- CloudFront Caching für Traffic-Reduktion

## Testing Templates

```bash
# Terraform Syntax Check
terraform fmt -check

# Validate Template
terraform validate

# Plan (Dry-Run)
terraform plan

# Cost Estimation (mit Infracost)
infracost breakdown --path .
```

## Troubleshooting

### Template Rendering Fehler

```python
# Debug Jinja2 Rendering
print(template.render(**context))
```

### Terraform Fehler

```bash
# Enable Debug Logging
export TF_LOG=DEBUG
terraform apply

# State Inspektion
terraform state list
terraform state show aws_instance.main
```

### Lambda Deployment Fehler

```bash
# Lambda Logs anzeigen
aws logs tail /aws/lambda/FUNCTION_NAME --follow

# Lambda testen
aws lambda invoke --function-name FUNCTION_NAME out.json
cat out.json
```

## Weiterentwicklung

Neue Blueprints hinzufügen:

1. **Blueprint Definition:** `backend/app/data/blueprints/my_blueprint.py`
2. **Terraform Template:** `backend/templates/terraform/my_blueprint.tf.j2`
3. **Template registrieren:** In Blueprint `terraform_templates` Liste

Best Practices:
- Verwende bestehende Templates als Basis
- Teste mit `terraform plan` ausgiebig
- Dokumentiere alle Variables
- Implementiere Outputs mit Deployment Instructions
- Security by Default (Encryption, Least Privilege)

## Support

Bei Fragen oder Problemen:
- Prüfe Blueprint Schema: `backend/app/data/blueprints/*.py`
- Validiere Template Syntax: `terraform validate`
- Debug Rendering: Jinja2 Debug Mode aktivieren
