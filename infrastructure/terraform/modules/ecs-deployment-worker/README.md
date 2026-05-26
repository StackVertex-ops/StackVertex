# ECS Deployment Worker Module

Erstellt ECS Fargate Task Definition für **on-demand Terraform Deployments**.

⚠️ **WICHTIG:** Dies ist **KEIN ECS Service**! Tasks werden on-demand via `boto3 ecs.run_task()` gestartet.

## Features

- **Fargate Spot** - 70% günstiger als Fargate Standard
- **On-demand Execution** - Start via boto3, keine permanent laufenden Tasks
- **Terraform Pre-installed** - Container enthält Terraform Binary
- **Full AWS Permissions** - Deploy in Customer AWS Accounts
- **CloudWatch Logs** - Alle Task Logs zentral gespeichert
- **ECR Repository** - Auto-created für Container Images
- **Security Group** - Allow all outbound (Worker needs AWS API access)

## Architektur

```
┌────────────────────────────────────────────────────────┐
│                   Lambda API Handler                   │
│          (Deployment Orchestrator Service)             │
└──────────────────────┬─────────────────────────────────┘
                       │
                       │ boto3.client('ecs').run_task()
                       ▼
┌────────────────────────────────────────────────────────┐
│                  ECS Fargate Spot Task                 │
│                                                         │
│  Container: deployment-worker                          │
│  - Terraform installed                                 │
│  - Python + FastAPI App Code                          │
│  - Environment Variables (injected at runtime)         │
│                                                         │
│  Task Role Permissions:                                │
│  - DynamoDB (Read/Write)                              │
│  - S3 Full Access                                      │
│  - EC2, RDS, Lambda Full (Customer Deployments)       │
│  - IAM Limited (Create Roles)                         │
│  - STS AssumeRole (Customer Account Access)           │
└──────────────────────┬─────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
   Customer AWS   DynamoDB        CloudWatch
   (via Creds)    (Status)          (Logs)
```

## Usage

```hcl
module "ecs_deployment_worker" {
  source = "../../modules/ecs-deployment-worker"

  # Project Configuration
  project_name = "stackvertex"
  environment  = "prod"
  aws_region   = "us-east-1"

  # ECS Task Configuration
  task_cpu    = 512   # 0.5 vCPU
  task_memory = 1024  # 1 GB
  container_image = "${aws_ecr_repository.worker.repository_url}:latest"
  enable_container_insights = false  # Save costs
  log_retention_days = 30

  # Networking
  vpc_id     = module.networking.vpc_id
  subnet_ids = module.networking.private_subnet_ids

  # DynamoDB
  dynamodb_table_name = module.database.table_name

  # S3
  s3_bucket_name       = module.storage.bucket_name
  user_data_bucket_name = module.user_storage.bucket_name

  # Security
  jwt_secret_arn = module.security.jwt_secret_arn

  # Extra Environment Variables (optional)
  extra_environment_variables = [
    {
      name  = "DEBUG"
      value = "false"
    }
  ]

  tags = {
    Project     = "StackVertex"
    Environment = "prod"
    ManagedBy   = "Terraform"
  }
}
```

## Container Image bauen

### Dockerfile

Siehe: `/backend/deployment-worker/Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Terraform installieren
RUN apt-get update && \
    apt-get install -y wget unzip && \
    wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip && \
    unzip terraform_1.6.0_linux_amd64.zip && \
    mv terraform /usr/local/bin/ && \
    rm terraform_1.6.0_linux_amd64.zip

# Python Dependencies
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --only main

# App Code
COPY app/ ./app/
COPY deployment-worker/worker.py ./

CMD ["python", "worker.py"]
```

### Build & Push

```bash
cd backend/

# Build
docker build -t deployment-worker -f deployment-worker/Dockerfile .

# Tag
docker tag deployment-worker:latest <ecr_repo_url>:latest

# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <ecr_repo_url>

# Push
docker push <ecr_repo_url>:latest
```

### Automated Build (GitHub Actions)

```yaml
name: Build Deployment Worker

on:
  push:
    branches: [main]
    paths:
      - 'backend/**'

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: us-east-1
      
      - name: Login to ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v1
      
      - name: Build and push
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          ECR_REPOSITORY: stackvertex-prod-deployment-worker
          IMAGE_TAG: ${{ github.sha }}
        run: |
          cd backend
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG -f deployment-worker/Dockerfile .
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
          
          # Also tag as latest
          docker tag $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG $ECR_REGISTRY/$ECR_REPOSITORY:latest
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:latest
```

## ECS Task starten (via boto3)

### Im Lambda API Handler (Deployment Orchestrator)

```python
import boto3
import json

ecs = boto3.client('ecs')

response = ecs.run_task(
    cluster='stackvertex-prod-deployment-cluster',
    taskDefinition='stackvertex-prod-deployment-worker',
    launchType='FARGATE',
    
    # Fargate Spot (70% günstiger!)
    capacityProviderStrategy=[
        {
            'capacityProvider': 'FARGATE_SPOT',
            'weight': 100,
            'base': 0
        }
    ],
    
    # Network Configuration
    networkConfiguration={
        'awsvpcConfiguration': {
            'subnets': ['subnet-abc123', 'subnet-def456'],
            'securityGroups': ['sg-abc123'],
            'assignPublicIp': 'ENABLED'  # Benötigt für AWS API Calls (ohne NAT Gateway)
        }
    },
    
    # Environment Variables (runtime injection)
    overrides={
        'containerOverrides': [
            {
                'name': 'deployment-worker',
                'environment': [
                    {'name': 'DEPLOYMENT_ID', 'value': deployment_id},
                    {'name': 'ARCHITECTURE_JSON', 'value': json.dumps(architecture)},
                    {'name': 'USER_ID', 'value': user_id},
                    {'name': 'WEBSOCKET_API_ENDPOINT', 'value': websocket_endpoint},
                    {'name': 'AWS_CUSTOMER_ROLE_ARN', 'value': customer_role_arn},
                ]
            }
        ]
    }
)

task_arn = response['tasks'][0]['taskArn']
print(f"Started ECS Task: {task_arn}")
```

## Task CPU/Memory Kombinationen

Fargate erlaubt nur bestimmte CPU/Memory Kombinationen:

| CPU (vCPU) | Memory (GB) |
|------------|-------------|
| 0.25 (256) | 0.5, 1, 2 |
| 0.5 (512)  | 1, 2, 3, 4 |
| 1 (1024)   | 2, 3, 4, 5, 6, 7, 8 |
| 2 (2048)   | 4-16 (1 GB steps) |
| 4 (4096)   | 8-30 (1 GB steps) |

**Empfehlung für StackVertex:**
- **Dev**: 256 CPU + 512 MB Memory
- **Prod**: 512 CPU + 1024 MB Memory (oder 1024 CPU + 2048 MB bei vielen Komponenten)

## Fargate Spot vs Fargate Standard

**Fargate Spot:**
- ✅ **70% günstiger**
- ✅ Perfekt für non-critical Workloads
- ⚠️ Kann interrupted werden (bei Kapazitätsengpässen)
- ⚠️ Keine Garantie für Verfügbarkeit

**Fargate Standard:**
- ✅ Garantierte Verfügbarkeit
- ✅ Keine Interruptions
- ❌ 3x teurer als Spot

**StackVertex Strategy:**
- Primary: Fargate Spot (default)
- Fallback: Fargate Standard (wenn Spot nicht verfügbar)

```hcl
capacity_providers = ["FARGATE_SPOT", "FARGATE"]

default_capacity_provider_strategy {
  capacity_provider = "FARGATE_SPOT"
  weight            = 100
  base              = 0
}
```

## IAM Permissions

### Task Execution Role (Start Task)

Managed by AWS:
- `AmazonECSTaskExecutionRolePolicy` - ECR Pull, CloudWatch Logs

Custom:
- `secretsmanager:GetSecretValue` - Secrets (JWT, etc.)

### Task Role (Runtime Permissions)

⚠️ **ACHTUNG:** Sehr permissive Permissions für Customer Deployments!

**DynamoDB:**
- Full Read/Write auf Platform Table

**S3:**
- Full Access auf Platform Buckets
- Full Access auf Customer Buckets (`s3:*` auf `*`)

**EC2:**
- Full Access (`ec2:*`) - Customer VPCs, Instances, Security Groups

**RDS:**
- Full Access (`rds:*`) - Customer Databases

**Lambda:**
- Full Access (`lambda:*`) - Customer Functions

**ECS:**
- Full Access (`ecs:*`) - Customer ECS Clusters

**IAM:**
- Limited Access - Create/Delete Roles, PassRole

**STS:**
- AssumeRole (`*`) - Access Customer Accounts via Credentials

**CloudWatch:**
- CreateLogGroup, PutLogEvents

**API Gateway:**
- ManageConnections - WebSocket postToConnection

### Security Best Practices

**✅ Implemented:**
- Least Privilege where possible
- IAM only limited actions (no `iam:*`)
- CloudWatch Logs audit trail

**⚠️ TODO (für Production):**
- **Resource-based Policies** - einschränken welche Resources deployed werden dürfen
- **Service Control Policies (SCP)** - Organisation-level Guardrails
- **Tag-based Access Control** - nur Resources mit bestimmten Tags
- **VPC Endpoints** - private AWS API Calls (ohne Internet)
- **Secrets Rotation** - automatisch rotieren

## Networking

### Public Subnet vs Private Subnet

**Public Subnet (assignPublicIp: ENABLED):**
- ✅ Direkt Internet Access (AWS API Calls)
- ✅ Kein NAT Gateway nötig (spart $30-50/Monat)
- ✅ Schnellerer Start (keine NAT Latency)
- ⚠️ Task hat Public IP (aber Security Group schützt)

**Private Subnet + NAT Gateway:**
- ✅ Kein Public IP (mehr Sicherheit)
- ✅ Compliance-konform
- ❌ NAT Gateway Kosten ($0.045/h + $0.045/GB = ~$35/Monat)
- ❌ Höhere Latency

**StackVertex Recommendation:**
- **Dev/Staging**: Public Subnet (Kosten sparen)
- **Production**: Private Subnet + NAT Gateway (Sicherheit)

### VPC Endpoints (optional)

VPC Endpoints für AWS Services (kostenlos, schneller):

```hcl
resource "aws_vpc_endpoint" "s3" {
  vpc_id       = var.vpc_id
  service_name = "com.amazonaws.us-east-1.s3"
  route_table_ids = [...]
}

resource "aws_vpc_endpoint" "dynamodb" {
  vpc_id       = var.vpc_id
  service_name = "com.amazonaws.us-east-1.dynamodb"
  route_table_ids = [...]
}

resource "aws_vpc_endpoint" "ecr_api" {
  vpc_id              = var.vpc_id
  service_name        = "com.amazonaws.us-east-1.ecr.api"
  vpc_endpoint_type   = "Interface"
  security_group_ids  = [...]
  subnet_ids          = [...]
}
```

Vorteile:
- ✅ Kein Internet Traffic (günstiger)
- ✅ Schneller (direkter AWS Backbone)
- ✅ Sicherer (kein Public Internet)

## Monitoring & Observability

### CloudWatch Logs

Alle Task Logs in:
```
/ecs/stackvertex-prod-deployment-worker
```

Log Stream Format:
```
ecs/deployment-worker/<task_id>
```

### CloudWatch Metrics

Auto-generierte Metriken:
- `CPUUtilization` - CPU Usage (%)
- `MemoryUtilization` - Memory Usage (%)
- `RunningTaskCount` - Anzahl laufender Tasks

### Container Insights (optional)

Wenn `enable_container_insights = true`:
- Detaillierte Metriken (Network, Disk, etc.)
- Performance Insights
- Container Map

**Kosten:** $0.30 per custom metric per month

**Empfehlung:** Nur in Production aktivieren.

### CloudWatch Alarms

Empfohlene Alarme:

```hcl
resource "aws_cloudwatch_metric_alarm" "task_failed" {
  alarm_name          = "ecs-deployment-worker-failed"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "DesiredTaskCount"
  namespace           = "AWS/ECS"
  period              = "60"
  statistic           = "Average"
  threshold           = "0"
  alarm_description   = "Alert when deployment task fails"
  
  dimensions = {
    ClusterName = aws_ecs_cluster.deployment.name
  }
}
```

## Cost Optimization

### Fargate Pricing (us-east-1)

**Fargate Spot:**
- vCPU: $0.01227456 per vCPU per hour
- Memory: $0.00134432 per GB per hour

**Example (512 CPU, 1024 MB, 30 min deployment):**
```
CPU: 0.5 vCPU × $0.01227456 × 0.5h = $0.00306864
Memory: 1 GB × $0.00134432 × 0.5h = $0.00067216
Total: ~$0.0037 per deployment
```

**1000 Deployments/month:**
```
1000 × $0.0037 = $3.70/month
```

Sehr günstig! 🎉

### Fargate Standard (zum Vergleich)

**Fargate Standard:**
- vCPU: $0.04048 per vCPU per hour (3.3x teurer)
- Memory: $0.004445 per GB per hour (3.3x teurer)

**Example (512 CPU, 1024 MB, 30 min):**
```
CPU: 0.5 × $0.04048 × 0.5h = $0.01012
Memory: 1 × $0.004445 × 0.5h = $0.00222
Total: ~$0.0123 per deployment (3.3x teurer!)
```

### Optimization Tips

1. **Fargate Spot** - immer verwenden (70% günstiger)
2. **Right-size Tasks** - nicht überdimensionieren
3. **Efficient Code** - schnellere Deployments = weniger Kosten
4. **Minimize Cold Starts** - Container Image optimieren
5. **Auto-stop Tasks** - Task beendet sich nach Deployment

## Troubleshooting

### Task startet nicht

**Problem:** `ecs.run_task()` failed

**Ursachen:**
1. Subnet hat kein Internet Access (kein NAT Gateway, kein Public IP)
2. Security Group blockiert Outbound Traffic
3. ECR Image nicht gefunden
4. IAM Permissions fehlen

**Lösung:**
1. Check Network: assignPublicIp=ENABLED oder NAT Gateway
2. Check Security Group: Allow all outbound
3. Check ECR: Image existiert? Login funktioniert?
4. Check IAM: Task Execution Role hat ECR Pull Permission?

### Task crashed (Exit Code 1)

**Problem:** Task startet, crashed sofort

**Ursachen:**
1. Python Exception im worker.py
2. Environment Variable fehlt
3. Secrets nicht lesbar

**Lösung:**
1. Check CloudWatch Logs: `/ecs/stackvertex-prod-deployment-worker`
2. Test lokal: `docker run -e ... <image>`
3. Add Error Handling in worker.py

### Terraform Deployment timeout

**Problem:** Deployment dauert >15 Min, Lambda timeout

**Grund:** Deshalb verwenden wir ECS! 🎉

**Lösung:** Bereits implementiert - ECS Task hat kein Timeout.

### Out of Memory

**Problem:** Task killed wegen OOM

**Lösung:**
1. Erhöhe `task_memory`
2. Profiling: Welche Terraform Resources verbrauchen viel RAM?
3. Batch Deployments (split in multiple Tasks)

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|----------|
| project_name | Project name | string | - | yes |
| environment | Environment | string | - | yes |
| aws_region | AWS Region | string | us-east-1 | no |
| task_cpu | Task CPU units | number | 512 | no |
| task_memory | Task memory (MB) | number | 1024 | no |
| container_image | Container image URL | string | - | yes |
| vpc_id | VPC ID | string | - | yes |
| subnet_ids | Subnet IDs | list(string) | - | yes |
| dynamodb_table_name | DynamoDB table | string | - | yes |
| s3_bucket_name | S3 bucket | string | - | yes |

## Outputs

| Name | Description |
|------|-------------|
| cluster_name | ECS Cluster name |
| task_definition_arn | Task Definition ARN |
| security_group_id | Security Group ID |
| ecr_repository_url | ECR Repository URL |

## Related Modules

- **lambda-api** - Lambda Functions (starten ECS Tasks)
- **networking** - VPC, Subnets
- **database-dynamodb** - DynamoDB Table
- **storage** - S3 Buckets

## License

Proprietary - StackVertex Platform
