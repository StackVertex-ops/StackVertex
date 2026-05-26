# Lambda API Module

Erstellt Lambda Functions für StackVertex API:
- **Main API Handler** - FastAPI via Mangum (handelt 99% der API Requests)
- **WebSocket Handlers** - $connect, $disconnect, $default für real-time Deployment Updates

## Features

- **FastAPI Integration** via Mangum (Lambda adapter)
- **WebSocket Support** mit API Gateway WebSocket API
- **VPC Support** (optional) für private Subnet Integration
- **X-Ray Tracing** für Performance-Monitoring
- **CloudWatch Logs** mit konfigurierbarer Retention
- **Secrets Manager** Integration für sichere Credentials
- **ECS Integration** für Deployment Orchestrator (kann ECS Tasks starten)
- **Least Privilege IAM** - nur notwendige Permissions

## Architektur

```
┌─────────────────────────────────────────────────────────────┐
│                      API Gateway (HTTP)                     │
│                  /api/v1/* → Lambda Integration             │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              Lambda: api-handler (FastAPI)                  │
│  - Memory: 512 MB (konfigurierbar)                         │
│  - Timeout: 30s (konfigurierbar, max 900s)                 │
│  - Layer: Python Dependencies (FastAPI, boto3, etc.)       │
│  - Environment: DynamoDB, S3, ECS, Secrets Manager         │
└──────────────────────────┬──────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
   DynamoDB           S3 Buckets        ECS RunTask
   (Main DB)      (Large Items + User)  (Deployments)
```

```
┌─────────────────────────────────────────────────────────────┐
│                 API Gateway (WebSocket)                     │
│  - $connect → websocket_connect                             │
│  - $disconnect → websocket_disconnect                       │
│  - $default → websocket_message                             │
└──────────────────────────┬──────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
   ws-connect        ws-disconnect       ws-message
   (256 MB)           (256 MB)           (256 MB)
        │                  │                  │
        └──────────────────┴──────────────────┘
                           │
                           ▼
                      DynamoDB
                  (Connection Mgmt)
```

## Usage

```hcl
module "lambda_api" {
  source = "../../modules/lambda-api"

  # Project Configuration
  project_name = "stackvertex"
  environment  = "prod"
  aws_region   = "us-east-1"

  # Lambda Configuration
  lambda_runtime          = "python3.11"
  lambda_timeout          = 30
  lambda_memory           = 512
  lambda_code_zip_path    = "${path.root}/../../backend/dist/lambda.zip"
  lambda_layer_zip_path   = "${path.root}/../../backend/dist/layer.zip"
  enable_xray             = true
  log_retention_days      = 30

  # VPC (optional - leave empty for no VPC)
  vpc_id     = module.networking.vpc_id
  subnet_ids = module.networking.private_subnet_ids

  # DynamoDB
  dynamodb_table_name   = module.database.table_name
  dynamodb_endpoint_url = ""

  # S3
  s3_bucket_name       = module.storage.bucket_name
  user_data_bucket_name = module.user_storage.bucket_name
  large_item_threshold  = 300000  # 300 KB

  # ECS (für Deployment Orchestrator)
  ecs_cluster_name          = module.ecs_worker.cluster_name
  ecs_task_definition_arn   = module.ecs_worker.task_definition_arn
  ecs_subnets               = module.networking.private_subnet_ids
  ecs_security_group_id     = module.ecs_worker.security_group_id

  # Security (Secrets Manager)
  jwt_secret_arn                = module.security.jwt_secret_arn
  jwt_algorithm                 = "HS256"
  access_token_expire_minutes   = 15
  refresh_token_expire_days     = 7

  # Stripe (optional)
  stripe_enabled               = true
  stripe_secret_key_arn        = module.security.stripe_secret_arn
  stripe_webhook_secret_arn    = module.security.stripe_webhook_secret_arn

  # WebSocket
  websocket_api_id       = module.api_gateway.websocket_api_id
  websocket_api_endpoint = module.api_gateway.websocket_api_endpoint

  tags = {
    Project     = "StackVertex"
    Environment = "prod"
    ManagedBy   = "Terraform"
  }
}
```

## Requirements

- **Terraform**: >= 1.5.0
- **AWS Provider**: ~> 5.0
- **Archive Provider**: ~> 2.4

## Deployment ZIP Files

Das Modul erwartet zwei ZIP-Dateien:

### 1. Lambda Code (`lambda.zip`)

Enthält den FastAPI Application Code:

```
lambda.zip
├── lambda_handler.py          # Mangum Handler
├── websocket_connect.py       # WebSocket $connect
├── websocket_disconnect.py    # WebSocket $disconnect
├── websocket_message.py       # WebSocket $default
└── app/                       # FastAPI App
    ├── main.py
    ├── api/
    ├── core/
    ├── models/
    ├── repositories/
    ├── services/
    └── ...
```

### 2. Lambda Layer (`layer.zip`)

Enthält Python Dependencies:

```
layer.zip
└── python/
    └── lib/
        └── python3.11/
            └── site-packages/
                ├── fastapi/
                ├── boto3/
                ├── mangum/
                ├── pydantic/
                └── ...
```

### Build-Skripte

Erstelle Lambda ZIP-Dateien:

```bash
# Im backend/ Verzeichnis

# 1. Lambda Layer (Dependencies)
cd /tmp
mkdir -p python/lib/python3.11/site-packages
pip install -r /path/to/backend/requirements.txt -t python/lib/python3.11/site-packages
zip -r layer.zip python/
mv layer.zip /path/to/backend/dist/

# 2. Lambda Code (App)
cd /path/to/backend
zip -r dist/lambda.zip lambda_handler.py websocket_*.py app/
```

Oder verwende Poetry:

```bash
cd backend/

# Install dependencies
poetry install --only main

# Build Lambda package
poetry run python scripts/build_lambda.py
```

## Environment Variables

Die Lambda Functions erhalten folgende Environment Variables:

### DynamoDB

- `DYNAMODB_TABLE_NAME` - DynamoDB Tabellenname
- `DYNAMODB_ENDPOINT_URL` - Endpoint (optional, für local testing)

### S3

- `S3_LARGE_ITEMS_BUCKET` - S3 Bucket für große Items
- `USER_DATA_BUCKET` - S3 Bucket für User Uploads
- `LARGE_ITEM_THRESHOLD` - Threshold für S3 Storage (bytes)

### AWS

- `AWS_REGION` - AWS Region

### Security

- `SECRET_KEY` - JWT Secret (aus Secrets Manager)
- `ALGORITHM` - JWT Algorithmus (HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES` - Token Expiration
- `REFRESH_TOKEN_EXPIRE_DAYS` - Refresh Token Expiration
- `ENV` - Environment (dev, staging, prod)

### ECS

- `ECS_CLUSTER_NAME` - ECS Cluster Name
- `ECS_TASK_DEFINITION` - ECS Task Definition ARN
- `ECS_SUBNETS` - Comma-separated Subnets
- `ECS_SECURITY_GROUP` - Security Group ID

### Stripe (optional)

- `STRIPE_SECRET_KEY` - Stripe Secret Key (aus Secrets Manager)
- `STRIPE_WEBHOOK_SECRET` - Stripe Webhook Secret
- `STRIPE_ENABLED` - true/false

### WebSocket

- `WEBSOCKET_API_ENDPOINT` - API Gateway WebSocket Endpoint

## IAM Permissions

Lambda Execution Role hat folgende Permissions:

### Managed Policies

- `AWSLambdaBasicExecutionRole` - CloudWatch Logs
- `AWSLambdaVPCAccessExecutionRole` - VPC (wenn VPC aktiv)
- `AWSXRayDaemonWriteAccess` - X-Ray Tracing (wenn aktiv)

### Custom Policies

- **DynamoDB**: GetItem, PutItem, UpdateItem, DeleteItem, Query, Scan, Batch*
- **S3**: GetObject, PutObject, DeleteObject, ListBucket
- **ECS**: RunTask, DescribeTasks, StopTask
- **IAM**: PassRole (für ECS Task Execution)
- **Secrets Manager**: GetSecretValue
- **API Gateway**: ManageConnections (für WebSocket postToConnection)
- **CloudWatch Logs**: CreateLogGroup, CreateLogStream, PutLogEvents

## VPC Configuration

**VPC ist optional!** Nur verwenden wenn:
- Lambda muss auf private RDS zugreifen
- Compliance erfordert private Subnets
- NAT Gateway vorhanden (für Internet-Zugriff zu AWS Services)

**Ohne VPC:**
- Lambda hat direkten Zugriff auf AWS Services
- Schnelleres Cold Start
- Keine NAT Gateway Kosten

**Mit VPC:**
- Höhere Cold Start Latency (~1-2s)
- Benötigt NAT Gateway für AWS Services ($30-50/Monat)
- Security Group Management erforderlich

### VPC Best Practices

Wenn VPC verwendet wird:

1. **Private Subnets** verwenden (nicht public!)
2. **NAT Gateway** in Public Subnets für AWS Service Access
3. **VPC Endpoints** für DynamoDB/S3 (kostenlos, schneller)
4. **Security Group**: Allow all outbound, no inbound

## X-Ray Tracing

Wenn `enable_xray = true`:
- Lambda Functions haben X-Ray Tracing aktiviert
- Traces erscheinen im AWS X-Ray Service Map
- Performance-Metriken für Cold Start, Dauer, Downstream Calls
- Hilfreich für Debugging von Performance-Problemen

## Monitoring & Observability

### CloudWatch Logs

- Log Group: `/aws/lambda/{function_name}`
- Retention: Konfigurierbar (default 30 Tage)
- Auto-created by Lambda Execution Role

### CloudWatch Metrics

Auto-generierte Metriken:
- `Invocations` - Anzahl Aufrufe
- `Duration` - Ausführungsdauer
- `Errors` - Fehler-Rate
- `Throttles` - Rate Limiting Hits
- `ConcurrentExecutions` - Parallele Ausführungen

### Alarme (TODO)

Empfohlene CloudWatch Alarme:
- Error Rate > 1%
- Duration > 10s (p99)
- Throttles > 0
- Cold Start Rate > 20%

## Cost Optimization

### Lambda Pricing (us-east-1)

**Request Kosten:**
- $0.20 per 1M Requests
- Erste 1M Requests/Monat: Kostenlos

**Compute Kosten:**
- $0.0000166667 per GB-second
- Erste 400,000 GB-seconds/Monat: Kostenlos

**Beispiel (512 MB Lambda, 100ms average, 1M requests/month):**
```
Requests: 1M × $0.20/1M = $0.20
Compute: (1M × 0.1s × 0.5 GB) = 50,000 GB-seconds
         50,000 × $0.0000166667 = $0.83
Total: ~$1.03/month (sehr günstig!)
```

### Optimization Tips

1. **Memory Tuning**: Teste verschiedene Memory Settings (mehr Memory = schneller = günstiger!)
2. **Cold Starts reduzieren**: Provisioned Concurrency (kostet mehr, aber garantiert Performance)
3. **Layer verwenden**: Dependencies im Layer = schnelleres Deployment
4. **VPC vermeiden**: Wenn möglich, ohne VPC = schnellere Starts
5. **X-Ray selective**: Nur in Prod aktivieren wenn nötig

## Security Best Practices

### ✅ Implemented

- **Least Privilege IAM** - nur notwendige Permissions
- **Secrets Manager** - keine Credentials in Environment Variables
- **VPC Security Groups** - restrictive Outbound Rules
- **CloudWatch Logs** - Audit Trail aller Requests
- **X-Ray Tracing** - Security Event Detection

### ⚠️ TODO (für Production)

- **Lambda Function URLs deaktivieren** - nur via API Gateway
- **Resource-based Policies** - einschränken wer Lambda invoke darf
- **KMS Encryption** - Environment Variables encrypted
- **WAF Integration** - API Gateway WAF Rules
- **DDoS Protection** - AWS Shield
- **Rate Limiting** - API Gateway Throttling

## Troubleshooting

### Lambda Timeout Errors

**Problem:** Lambda erreicht Timeout (default 30s)

**Lösung:**
1. Erhöhe `lambda_timeout` (max 900s = 15 Min)
2. Optimiere Code (async IO, Caching)
3. Verwende ECS für lange Tasks (>10 Min)

### Cold Start Performance

**Problem:** Erste Request dauert 2-3 Sekunden

**Ursachen:**
- VPC Integration (adds ~1-2s)
- Große Dependencies (FastAPI, boto3)
- Provisioning neuer Container

**Lösungen:**
1. **Provisioned Concurrency** (kostet mehr)
2. **Warmer Lambda** via EventBridge (scheduled ping)
3. **Layer optimization** (reduce dependencies)
4. **Ohne VPC** (wenn möglich)

### WebSocket Connection Issues

**Problem:** WebSocket disconnect nach 2 Stunden

**Grund:** API Gateway WebSocket Limit (idle timeout)

**Lösung:** Client muss ping/pong implementieren (keep-alive)

### Out of Memory Errors

**Problem:** Lambda killed wegen Memory Limit

**Lösung:**
1. Erhöhe `lambda_memory`
2. Profiling: Welche Code Paths verbrauchen viel RAM?
3. Streaming für große Payloads

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|----------|
| project_name | Project name | string | - | yes |
| environment | Environment | string | - | yes |
| aws_region | AWS Region | string | us-east-1 | no |
| lambda_runtime | Lambda runtime | string | python3.11 | no |
| lambda_timeout | Lambda timeout (seconds) | number | 30 | no |
| lambda_memory | Lambda memory (MB) | number | 512 | no |
| lambda_code_zip_path | Path to Lambda code ZIP | string | - | yes |
| lambda_layer_zip_path | Path to Lambda layer ZIP | string | - | yes |
| enable_xray | Enable X-Ray tracing | bool | true | no |
| log_retention_days | CloudWatch Logs retention | number | 30 | no |
| vpc_id | VPC ID (optional) | string | "" | no |
| subnet_ids | Subnet IDs (optional) | list(string) | [] | no |
| dynamodb_table_name | DynamoDB table name | string | - | yes |
| s3_bucket_name | S3 bucket name | string | - | yes |
| user_data_bucket_name | User data bucket name | string | - | yes |
| ecs_cluster_name | ECS cluster name | string | - | yes |
| ecs_task_definition_arn | ECS task definition ARN | string | - | yes |
| ecs_subnets | ECS subnets | list(string) | - | yes |
| ecs_security_group_id | ECS security group ID | string | - | yes |
| jwt_secret_arn | JWT secret ARN | string | "" | no |
| websocket_api_id | WebSocket API ID | string | "" | no |
| websocket_api_endpoint | WebSocket API endpoint | string | "" | no |

## Outputs

| Name | Description |
|------|-------------|
| api_handler_function_arn | API Handler Lambda ARN |
| api_handler_invoke_arn | API Handler invoke ARN |
| websocket_lambda_arns | WebSocket Lambda ARNs map |
| lambda_execution_role_arn | Lambda execution role ARN |
| dependencies_layer_arn | Dependencies layer ARN |

## Related Modules

- **api-gateway** - API Gateway HTTP & WebSocket APIs
- **ecs-deployment-worker** - ECS Tasks für lange Deployments
- **database-dynamodb** - DynamoDB Table
- **storage** - S3 Buckets

## License

Proprietary - StackVertex Platform
