# OverCloud Infrastructure Architecture

Detaillierte Architektur-Dokumentation der AWS Serverless Infrastruktur.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              End Users / Browser                             │
└────────────────────────────┬────────────────────────────────────────────────┘
                             │ HTTPS
                             │
                    ┌────────▼──────────┐
                    │   CloudFront      │ (Optional, für Frontend)
                    │   CDN             │
                    └────────┬──────────┘
                             │
        ┌────────────────────┴────────────────────┐
        │                                         │
┌───────▼────────┐                       ┌────────▼────────┐
│ API Gateway    │                       │  S3 Bucket      │
│ (HTTP API)     │                       │  (Frontend)     │
│ - REST API     │                       │  - Static Site  │
│ - CORS         │                       └─────────────────┘
│ - Rate Limit   │
└───────┬────────┘
        │
┌───────▼────────┐
│ API Gateway    │
│ (WebSocket)    │
│ - Real-time    │
│ - Bidirectional│
└───────┬────────┘
        │
        └────────────────────┐
                             │
                    ┌────────▼──────────────────────┐
                    │   AWS Lambda                  │
                    │   - FastAPI App (Container)   │
                    │   - Mangum ASGI Adapter       │
                    │   - Python 3.11               │
                    │   - 512 MB Memory             │
                    │   - 30s Timeout               │
                    │   - VPC Connected             │
                    └────┬──────────────────┬───────┘
                         │                  │
        ┌────────────────┘                  └────────────────┐
        │                                                     │
┌───────▼────────┐                                   ┌───────▼────────┐
│  VPC           │                                   │ Secrets Manager│
│  - Private     │                                   │ - DB Creds     │
│    Subnets     │                                   │ - API Keys     │
│  - NAT Gateway │                                   └────────────────┘
└───────┬────────┘
        │
        ├──────────────────┬──────────────────┬──────────────────┐
        │                  │                  │                  │
┌───────▼────────┐ ┌───────▼────────┐ ┌───────▼────────┐ ┌─────▼──────┐
│ Aurora         │ │ ElastiCache    │ │ S3 Buckets     │ │ DynamoDB   │
│ Serverless v2  │ │ Redis          │ │ - Customer Data│ │ (Locks)    │
│ (PostgreSQL)   │ │ (Optional)     │ │ - Deployments  │ └────────────┘
│                │ │                │ │ - Terraform    │
│ - Multi-AZ     │ │ - Cache        │ │ - Lambda Code  │
│ - Auto-scale   │ │ - Sessions     │ │                │
│ - Encrypted    │ └────────────────┘ │ - Versioning   │
│ - Backup       │                    │ - Encryption   │
└────────────────┘                    │ - Lifecycle    │
                                      └────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                      Observability & Security Layer                          │
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ CloudWatch   │  │ CloudTrail   │  │ GuardDuty    │  │ Security Hub │   │
│  │              │  │              │  │              │  │              │   │
│  │ - Metrics    │  │ - API Calls  │  │ - Threats    │  │ - Compliance │   │
│  │ - Logs       │  │ - S3 Events  │  │ - Anomalies  │  │ - CIS Bench  │   │
│  │ - Alarms     │  │ - Lambda     │  │ - Malware    │  │ - AWS FBS    │   │
│  │ - Dashboard  │  │ - Audit      │  │              │  │              │   │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘   │
│         │                  │                  │                  │           │
│         └──────────────────┴──────────────────┴──────────────────┘           │
│                                     │                                        │
│                            ┌────────▼────────┐                               │
│                            │  SNS Topics     │                               │
│                            │  - Critical     │                               │
│                            │  - Warning      │                               │
│                            │  - Info         │                               │
│                            └────────┬────────┘                               │
│                                     │                                        │
│                    ┌────────────────┴────────────────┐                       │
│                    │                                 │                       │
│            ┌───────▼────────┐              ┌─────────▼────────┐              │
│            │  Email         │              │  Slack           │              │
│            │  Notifications │              │  Webhooks        │              │
│            └────────────────┘              └──────────────────┘              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Network Architecture

```
AWS Region: eu-central-1 (Frankfurt)
┌─────────────────────────────────────────────────────────────────────┐
│ VPC: 10.0.0.0/16                                                    │
│                                                                      │
│  Availability Zone A              Availability Zone B               │
│  ┌─────────────────────┐         ┌─────────────────────┐           │
│  │ Public Subnet       │         │ Public Subnet       │           │
│  │ 10.0.0.0/20         │         │ 10.0.16.0/20        │           │
│  │                     │         │                     │           │
│  │ - Internet Gateway  │         │ - Internet Gateway  │           │
│  │ - NAT Gateway       │         │ - NAT Gateway       │           │
│  │   (optional)        │         │   (optional)        │           │
│  └─────────────────────┘         └─────────────────────┘           │
│                                                                      │
│  ┌─────────────────────┐         ┌─────────────────────┐           │
│  │ Private Subnet      │         │ Private Subnet      │           │
│  │ 10.0.32.0/20        │         │ 10.0.48.0/20        │           │
│  │                     │         │                     │           │
│  │ - Aurora Primary    │         │ - Aurora Replica    │           │
│  │ - Lambda ENIs       │         │ - Lambda ENIs       │           │
│  │ - ElastiCache       │         │ - ElastiCache       │           │
│  │                     │         │                     │           │
│  └─────────────────────┘         └─────────────────────┘           │
│                                                                      │
│  Security Groups:                                                   │
│  - lambda-sg: Egress all, Ingress none                             │
│  - aurora-sg: Ingress 5432 from lambda-sg                          │
│  - redis-sg: Ingress 6379 from lambda-sg                           │
│                                                                      │
│  VPC Endpoints (optional):                                          │
│  - s3: Gateway endpoint (free)                                      │
│  - secretsmanager: Interface endpoint ($7.20/month)                 │
│  - ecr.api, ecr.dkr: For Lambda container image pull               │
└─────────────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. API Request Flow

```
User → CloudFront (optional) → API Gateway → Lambda → Aurora
                                    ↓
                                VPC (ENI)
                                    ↓
                        ┌───────────┴──────────┐
                        │                      │
                  Aurora (Read)          S3 (Files)
```

**Steps:**

1. User macht HTTPS Request: `https://api.overcloud.com/api/v1/architectures`
2. CloudFront (optional) cached Response oder forwarded zu API Gateway
3. API Gateway:
   - CORS Check
   - Rate Limiting
   - Invokes Lambda (Event Payload)
4. Lambda:
   - Mangum konvertiert API Gateway Event → ASGI Request
   - FastAPI Router matched `/api/v1/architectures`
   - Controller fetched DB Credentials aus Secrets Manager
   - SQLAlchemy Query → Aurora
5. Aurora returns Data
6. Lambda returns Response → API Gateway → CloudFront → User

**Latency:**
- Cold Start: 2-5s (erste Invocation)
- Warm Start: 50-200ms
- Database Query: 10-50ms
- Total (warm): ~100-300ms

---

### 2. WebSocket Flow (Real-time Updates)

```
User ←→ WebSocket API ←→ Lambda ←→ Aurora
         (Persistent)      ↓
                      ConnectionTable
                        (DynamoDB)
```

**Steps:**

1. **Connect:**
   - User: `ws://api.overcloud.com/ws/deployments/123`
   - WebSocket API → Lambda `$connect`
   - Lambda stores `connectionId` in DynamoDB
   - Returns 200 OK

2. **Send Message:**
   - User sends: `{"action": "subscribe", "deployment_id": "123"}`
   - WebSocket API → Lambda `$default`
   - Lambda processes, returns acknowledgement

3. **Broadcast (Server → Client):**
   - Backend Event (Deployment Status Changed)
   - Lambda queries DynamoDB for all `connectionId`s
   - For each connection:
     ```python
     apigw_client.post_to_connection(
         ConnectionId=connection_id,
         Data=json.dumps({"status": "running", "progress": 45})
     )
     ```

4. **Disconnect:**
   - User closes connection
   - WebSocket API → Lambda `$disconnect`
   - Lambda deletes `connectionId` from DynamoDB

---

### 3. Deployment Flow

```
User → API: POST /deployments → Lambda → Background Task
                                    ↓
                          ┌─────────┴──────────┐
                          │  ThreadPoolExecutor │
                          │  (5 Workers)        │
                          └─────────┬───────────┘
                                    ↓
                    ┌───────────────┴────────────────┐
                    │ Terraform Execution            │
                    │ 1. Generate HCL from JSON      │
                    │ 2. Write to /tmp/deployments/  │
                    │ 3. terraform init              │
                    │ 4. terraform plan              │
                    │ 5. terraform apply             │
                    │ 6. Save state → S3             │
                    │ 7. Update DB status            │
                    │ 8. Broadcast via WebSocket     │
                    └────────────────────────────────┘
```

---

### 4. Customer Data Flow

```
User → Presigned URL (from Lambda) → S3 Upload
                                       ↓
                              S3 Event Notification
                                       ↓
                                Lambda Trigger
                                       ↓
                          Process File (Virus Scan, etc.)
                                       ↓
                              Update Database
```

**Presigned URL Generation:**

```python
# Lambda Code
import boto3

s3 = boto3.client('s3')

presigned_url = s3.generate_presigned_url(
    'put_object',
    Params={
        'Bucket': 'overcloud-dev-customer-data-123456789012',
        'Key': f'customers/{customer_id}/uploads/{filename}',
        'ContentType': 'application/octet-stream'
    },
    ExpiresIn=3600  # 1 hour
)

return {"upload_url": presigned_url}
```

**Direct Upload (Frontend):**

```javascript
// Frontend
const response = await fetch('/api/v1/uploads/presigned-url', {
  method: 'POST',
  body: JSON.stringify({ filename: 'document.pdf' })
});

const { upload_url } = await response.json();

// Direct S3 Upload (bypasses Lambda!)
await fetch(upload_url, {
  method: 'PUT',
  body: file,
  headers: { 'Content-Type': 'application/pdf' }
});
```

---

## Security Architecture

### 1. Authentication & Authorization

```
User → JWT Token → API Gateway → Lambda → Verify Token
                                              ↓
                                    Check Permissions
                                              ↓
                                    Access Resource
```

**Token Flow:**

1. Login: `POST /auth/login` → Lambda generates JWT
2. Subsequent Requests: `Authorization: Bearer <JWT>`
3. Lambda middleware verifies signature (using Secret from Secrets Manager)
4. Extract User ID + Permissions from Token
5. Check if User can access Resource

**IAM Roles:**

```
Lambda Execution Role:
- Secrets Manager: GetSecretValue (DB credentials)
- S3: GetObject, PutObject (Customer Data, Deployments)
- CloudWatch Logs: CreateLogStream, PutLogEvents
- EC2: CreateNetworkInterface (VPC access)
- DynamoDB: GetItem, PutItem (WebSocket connections)

Aurora IAM Auth (optional):
- RDS: Connect via IAM instead of password
```

---

### 2. Data Encryption

**At Rest:**
- S3: AES-256 or KMS (optional)
- Aurora: AES-256 (always)
- Secrets Manager: KMS (always)
- EBS Volumes (Lambda): AES-256

**In Transit:**
- HTTPS only (API Gateway enforces TLS 1.2+)
- Aurora: SSL/TLS connections
- VPC Internal: No encryption (private network)

---

### 3. Network Security

**Defense in Depth:**

1. **Public Layer:**
   - API Gateway: Only HTTPS, CORS, Rate Limiting
   - CloudFront (optional): DDoS protection (AWS Shield)

2. **Application Layer:**
   - Lambda: No direct internet access (in VPC)
   - Security Groups: Minimal rules

3. **Data Layer:**
   - Aurora: Private subnets only, no public endpoint
   - S3: Bucket policies, no public access

**Security Groups:**

```hcl
# Lambda → Aurora
resource "aws_security_group_rule" "lambda_to_aurora" {
  type                     = "ingress"
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.lambda.id
  security_group_id        = aws_security_group.aurora.id
}

# Lambda → Internet (via NAT Gateway)
resource "aws_security_group_rule" "lambda_egress" {
  type              = "egress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.lambda.id
}
```

---

## Scalability & Performance

### Auto-Scaling Components

| Component | Scaling Metric | Min | Max | Target |
|-----------|----------------|-----|-----|--------|
| Lambda | Concurrent Executions | 0 | 1000 | Auto |
| Aurora | ACUs (Serverless v2) | 0.5 | 16 | CPU 70% |
| API Gateway | Requests/sec | - | 10000 | - |
| ElastiCache | Node Count | 1 | 5 | CPU 70% |

---

### Performance Optimization

**1. Lambda Cold Start Reduction:**

```hcl
# Provisioned Concurrency (keeps X instances warm)
resource "aws_lambda_provisioned_concurrency_config" "api" {
  function_name = aws_lambda_function.api.function_name
  provisioned_concurrent_executions = 2  # Always 2 warm
}

# Cost: ~$8.50/month per instance
```

**2. Database Connection Pooling:**

```python
# SQLAlchemy with connection pooling
engine = create_engine(
    DATABASE_URL,
    pool_size=5,          # 5 connections per Lambda instance
    max_overflow=2,       # Up to 7 connections
    pool_recycle=3600,    # Recycle after 1 hour
    pool_pre_ping=True    # Test connection before use
)
```

**3. Redis Caching:**

```python
# Cache frequently accessed data
@cache(ttl=300)  # 5 minutes
def get_architecture(architecture_id):
    return db.query(Architecture).get(architecture_id)
```

**4. API Response Caching:**

```hcl
# API Gateway Cache (optional)
resource "aws_apigatewayv2_stage" "default" {
  # ...
  default_route_settings {
    data_trace_enabled       = true
    throttling_rate_limit    = 100
    throttling_burst_limit   = 50
    caching_enabled          = true
    cache_ttl_in_seconds     = 300
    cache_data_encrypted     = true
  }
}

# Cost: $0.02/hour = ~$14.40/month (0.5 GB cache)
```

---

## Disaster Recovery

### Backup Strategy

| Component | Backup Frequency | Retention | Recovery Time |
|-----------|------------------|-----------|---------------|
| Aurora | Continuous (PITR) | 7-35 days | ~15 min |
| S3 | Versioning | 90-730 days | Instant |
| Terraform State | Versioning | 365 days | Instant |
| Lambda Code | ECR Versions | Keep last 5 | ~1 min |

---

### Recovery Procedures

**1. Database Recovery (Point-in-Time):**

```bash
# Restore to specific timestamp
aws rds restore-db-cluster-to-point-in-time \
  --source-db-cluster-identifier overcloud-prod-aurora \
  --db-cluster-identifier overcloud-prod-aurora-restored \
  --restore-to-time "2026-04-18T10:30:00Z" \
  --use-latest-restorable-time

# Takes ~15 minutes
```

**2. S3 Object Recovery:**

```bash
# List versions
aws s3api list-object-versions \
  --bucket overcloud-prod-customer-data-123456789012 \
  --prefix customers/customer-123/important-file.pdf

# Restore specific version
aws s3api copy-object \
  --copy-source "bucket/key?versionId=VERSION_ID" \
  --bucket bucket \
  --key key
```

**3. Infrastructure Recovery:**

```bash
# Complete recreation from Terraform
cd infrastructure/terraform/environments/prod
terraform init
terraform apply

# + Docker image redeploy
# + Database restore from snapshot
# Total: ~30 minutes
```

---

## Cost Optimization Strategies

### 1. Right-Sizing

**Aurora ACUs:**
- Dev: 0.5-1 ACU (sufficient for testing)
- Prod: Start with 2-4, monitor, adjust

**Lambda Memory:**
- Start: 512 MB
- Monitor: CloudWatch Duration vs Memory Used
- Optimize: Increase if CPU-bound, decrease if memory unused

---

### 2. Reserved Capacity (Prod only)

**Aurora Reserved Instances:**
- 1-Year Commitment: ~30% savings
- 3-Year Commitment: ~60% savings

```bash
# Calculate savings
# On-Demand: 2 ACU * $0.12/hour * 730 hours = $175/month
# 1-Year Reserved: ~$122/month (save $53/month)
```

---

### 3. Lifecycle Policies

**Already implemented:**
- S3: 30d → IA, 90d → Glacier
- CloudWatch Logs: 7-90 days retention
- Lambda Images: Keep last 5 versions

---

### 4. Cost Monitoring

```bash
# AWS Cost Explorer
aws ce get-cost-and-usage \
  --time-period Start=2026-04-01,End=2026-04-30 \
  --granularity MONTHLY \
  --metrics "UnblendedCost" \
  --group-by Type=SERVICE

# Set Budget Alert
aws budgets create-budget \
  --account-id 123456789012 \
  --budget file://budget.json \
  --notifications-with-subscribers file://notifications.json
```

---

## Compliance & Governance

### CIS AWS Foundations Benchmark

**Implemented Controls:**

- ✅ 1.2: MFA for Root Account
- ✅ 1.3: Credentials unused for 90 days
- ✅ 2.1: CloudTrail enabled in all regions
- ✅ 2.3: S3 bucket access logging
- ✅ 2.6: S3 bucket public access blocked
- ✅ 2.9: VPC Flow Logs enabled
- ✅ 3.1: CloudWatch Log Metric Filter for unauthorized API calls
- ✅ 4.1: SSH restricted to specific IPs (N/A - no EC2)
- ✅ 4.2: RDS instances not public

---

### GDPR Compliance

**Data Protection:**
- Encryption at rest (S3, Aurora, Secrets)
- Encryption in transit (HTTPS, TLS)
- Access logging (CloudTrail)
- Data retention policies (S3 Lifecycle)
- Right to deletion (S3 delete, Aurora hard delete)

**Audit Trail:**
- All API calls logged (CloudTrail)
- Database changes logged (Audit Log table)
- Retention: 365 days minimum

---

## Deployment Strategies

### Blue/Green Deployment

```
┌──────────────┐         ┌──────────────┐
│  Blue (old)  │         │ Green (new)  │
│  Lambda v1   │         │  Lambda v2   │
└──────┬───────┘         └──────┬───────┘
       │                        │
       │  ┌──────────────┐      │
       └──│ API Gateway  │──────┘
          │ (Weighted)   │
          └──────────────┘
          90% Blue, 10% Green → Monitor
          If OK: 100% Green
```

**Terraform Implementation:**

```hcl
resource "aws_lambda_alias" "live" {
  name             = "live"
  function_name    = aws_lambda_function.api.function_name
  function_version = aws_lambda_function.api.version

  routing_config {
    additional_version_weights = {
      aws_lambda_function.api.version = 0.1  # 10% to new version
    }
  }
}
```

---

### Canary Deployment

```
API Gateway Stage:
┌────────────────────────────────┐
│ Production Stage               │
│                                │
│ Deployment:                    │
│ - Canary: 10% traffic → v2     │
│ - Stable: 90% traffic → v1     │
│                                │
│ Monitor Canary Metrics:        │
│ - Errors < 1%                  │
│ - Latency < 500ms              │
│                                │
│ If OK: Promote Canary → 100%  │
└────────────────────────────────┘
```

---

## Monitoring KPIs

### Application Performance

| Metric | Target | Critical Threshold |
|--------|--------|-------------------|
| API Latency (p95) | < 500ms | > 2000ms |
| Lambda Duration (p95) | < 5s | > 20s |
| Lambda Error Rate | < 0.1% | > 1% |
| API Error Rate (5XX) | < 0.01% | > 0.1% |
| Database Connections | < 50 | > 80 |

---

### Infrastructure Health

| Metric | Target | Critical Threshold |
|--------|--------|-------------------|
| Aurora CPU | < 50% | > 80% |
| Aurora ACUs | 0.5-4 | > 8 |
| Lambda Concurrent Executions | < 100 | > 800 |
| S3 Storage | < 100 GB | > 500 GB |
| CloudWatch Log Volume | < 10 GB/day | > 50 GB/day |

---

## Future Enhancements

### Phase 2 (Planned)

1. **Multi-Region Deployment:**
   - Active-Active: eu-central-1 + us-east-1
   - Route53 Latency-based routing
   - Cross-region Aurora replication

2. **Advanced Caching:**
   - CloudFront for API responses
   - ElastiCache Redis cluster
   - DynamoDB Accelerator (DAX)

3. **Enhanced Security:**
   - AWS WAF (Web Application Firewall)
   - AWS Shield Advanced (DDoS protection)
   - Certificate Manager (custom domain)

4. **CI/CD Improvements:**
   - Automated rollback on failure
   - Integration tests in pipeline
   - Performance regression tests

---

## References

- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
- [Serverless Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [Aurora Serverless v2](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/aurora-serverless-v2.html)
- [API Gateway Best Practices](https://docs.aws.amazon.com/apigateway/latest/developerguide/best-practices.html)
- [FastAPI on AWS Lambda](https://www.mangum.io/)
