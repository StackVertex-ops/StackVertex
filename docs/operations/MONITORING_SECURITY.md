# OverCloud Monitoring & Security Guide

Kompletter Guide für Monitoring, Alerting und Security der OverCloud Infrastruktur.

## Übersicht

```
┌─────────────────────────────────────────────────────────────┐
│                    OverCloud Infrastruktur                   │
│  Lambda │ API Gateway │ Aurora │ S3 │ ...                   │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
   ┌────▼──────┐          ┌───────▼────────┐
   │ CloudWatch│          │   CloudTrail   │
   │           │          │ (API Audit)    │
   │ - Metrics │          └────────┬───────┘
   │ - Logs    │                   │
   │ - Alarms  │          ┌────────▼────────┐
   │ - Dashboard│         │   GuardDuty     │
   └────┬──────┘          │ (Threat Detect) │
        │                 └────────┬────────┘
        │                          │
   ┌────▼──────────────────────────▼────────┐
   │         SNS Topics (Alerts)             │
   │  - Critical │ Warning │ Info            │
   └────┬────────────────────────────────────┘
        │
   ┌────▼────────┐
   │  Email      │
   │  Slack      │
   │  PagerDuty  │
   └─────────────┘
```

## 1. CloudWatch Monitoring

### Dashboard Übersicht

Nach dem Deployment ist ein zentrales Dashboard verfügbar:

```bash
# Dashboard URL
terraform output cloudwatch_dashboard_url

# Oder manuell:
open "https://console.aws.amazon.com/cloudwatch/home?region=eu-central-1#dashboards:name=overcloud-dev-overview"
```

**Dashboard Widgets:**

1. **Lambda Performance**
   - Total Invocations
   - Errors
   - Throttles
   - Average Duration
   - Max Concurrent Executions

2. **API Gateway Performance**
   - Request Count
   - 4XX Errors
   - 5XX Errors
   - Latency

3. **Aurora Database**
   - CPU Utilization
   - Database Connections
   - Serverless Capacity (ACUs)
   - Read/Write Latency

4. **S3 Storage**
   - Bucket Size
   - Object Count

5. **Error Rate**
   - Calculated: Errors / Invocations * 100

6. **Recent Errors**
   - Last 20 ERROR log entries

### Custom Metrics

Zusätzliche Custom Metrics in Namespace `OverCloud/{environment}`:

```python
# Im Backend Code (app/services/metrics.py)
import boto3

cloudwatch = boto3.client('cloudwatch')

def track_deployment(deployment_id, status):
    """Track deployment metrics."""
    cloudwatch.put_metric_data(
        Namespace=f'OverCloud/{os.getenv("ENVIRONMENT")}',
        MetricData=[
            {
                'MetricName': 'DeploymentCount',
                'Value': 1,
                'Unit': 'Count',
                'Dimensions': [
                    {'Name': 'Status', 'Value': status}
                ]
            },
            {
                'MetricName': 'DeploymentDuration',
                'Value': duration_seconds,
                'Unit': 'Seconds'
            }
        ]
    )
```

### CloudWatch Logs Insights Queries

**Vordefinierte Queries:**

1. **Error Analysis**
```sql
fields @timestamp, @message, level, request_id
| filter level = "ERROR"
| stats count() by bin(5m)
| sort @timestamp desc
```

2. **Slow Requests**
```sql
fields @timestamp, @message, duration_ms, request_path
| filter duration_ms > 1000
| sort duration_ms desc
| limit 50
```

3. **Deployment History**
```sql
fields @timestamp, deployment_id, status, customer_id
| filter @message like /deployment/
| sort @timestamp desc
```

4. **Customer Activity**
```sql
fields @timestamp, customer_id, action, resource_type
| stats count() by customer_id
| sort count desc
```

**Custom Query erstellen:**

```bash
# Via AWS Console
CloudWatch → Logs → Insights → New query

# Via CLI
aws logs start-query \
  --log-group-name /aws/lambda/overcloud-dev-api \
  --start-time $(date -u -d '1 hour ago' +%s) \
  --end-time $(date -u +%s) \
  --query-string 'fields @timestamp, @message | filter level = "ERROR" | sort @timestamp desc'
```

## 2. Alerting System

### SNS Topics

Drei Alert-Severity-Level:

1. **Critical** (`overcloud-{env}-critical-alerts`)
   - Lambda Errors > 10 (prod) / 20 (dev)
   - Lambda Throttles
   - API 5XX Errors > 5
   - Aurora CPU > 80%
   - Deployment Failures > 3
   - Root Account Usage
   - GuardDuty High/Critical Findings
   - Security Hub Critical Findings

2. **Warning** (`overcloud-{env}-warning-alerts`)
   - Lambda Duration > 80% of timeout
   - API 4XX Errors > 50 (prod) / 100 (dev)
   - API Latency > 2000ms
   - Aurora Connections > 80% of max
   - Aurora Storage threshold
   - Unauthorized Access Attempts > 10
   - IAM Policy Changes
   - S3 Bucket Policy Changes

3. **Info** (`overcloud-{env}-info-alerts`)
   - Alarm Recovery (OK state)
   - IAM Policy Changes (info)

### Email Alerts konfigurieren

```bash
# In terraform.tfvars
alert_emails = [
  "admin@example.com",
  "ops-team@example.com"
]
```

Nach `terraform apply`:
- Jede Email bekommt SNS Subscription Confirmation
- Link in Email klicken zum Bestätigen
- Danach: Alerts werden zugestellt

### Slack Integration

**1. Slack Webhook erstellen:**

```bash
# In Slack:
Apps → Incoming Webhooks → Add to Slack
# Wähle Channel (z.B. #overcloud-alerts)
# Kopiere Webhook URL
```

**2. In terraform.tfvars:**

```hcl
slack_webhook_url = "https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX"
```

**3. Deploy:**

```bash
terraform apply
```

**Alert Format:**

```json
{
  "AlarmName": "overcloud-prod-lambda-errors-critical",
  "NewStateValue": "ALARM",
  "NewStateReason": "Threshold Crossed: 15 datapoints > 10.0",
  "Trigger": {
    "MetricName": "Errors",
    "Namespace": "AWS/Lambda",
    "Threshold": 10
  }
}
```

### PagerDuty Integration (Optional)

```hcl
# SNS → Lambda → PagerDuty API
resource "aws_sns_topic_subscription" "pagerduty" {
  topic_arn = module.monitoring.critical_alerts_topic_arn
  protocol  = "https"
  endpoint  = "https://events.pagerduty.com/integration/${var.pagerduty_key}/enqueue"
}
```

## 3. Security Monitoring

### CloudTrail - API Audit Log

**Alle AWS API Calls werden geloggt:**

- Wer? (User/Role)
- Was? (API Call)
- Wann? (Timestamp)
- Wo? (IP, User Agent)
- Ergebnis? (Success/Failure)

**CloudTrail Console:**

```bash
terraform output security_monitoring_urls
# → cloudtrail: https://...
```

**Wichtige Events:**

1. **IAM Changes:**
   - CreateUser, DeleteUser
   - AttachUserPolicy, DetachUserPolicy
   - CreateRole, DeleteRole

2. **S3 Changes:**
   - PutBucketPolicy, DeleteBucketPolicy
   - PutBucketAcl
   - PutObject, DeleteObject (für bestimmte Buckets)

3. **Database Changes:**
   - CreateDBCluster, DeleteDBCluster
   - ModifyDBCluster

4. **Lambda Changes:**
   - UpdateFunctionCode
   - UpdateFunctionConfiguration

**Query Events:**

```bash
# Via CLI
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=PutBucketPolicy \
  --max-results 10

# Via CloudWatch Logs Insights
fields @timestamp, userIdentity.principalId, eventName, sourceIPAddress, errorCode
| filter eventSource = "s3.amazonaws.com"
| filter eventName like /PutBucket/
| sort @timestamp desc
```

### GuardDuty - Threat Detection

**Automatische Erkennung von:**

- Compromised Instances (wenn EC2 verwendet wird)
- Reconnaissance (Port Scanning, ungewöhnliche API Calls)
- Instance/Credential Compromise
- Malware / Crypto Mining
- Unauthorized Access (zu S3, IAM, etc.)

**GuardDuty Console:**

```bash
# URL aus Terraform Output
terraform output security_monitoring_urls
# → guardduty: https://...
```

**Finding Severity:**

- **Low (1-3.9):** Minimal risk, für Info
- **Medium (4-6.9):** Potenzielles Problem, untersuchen
- **High (7-8.9):** Ernstes Problem, sofort handeln (→ SNS Alert)
- **Critical (9-10):** Aktive Bedrohung, sofort mitigieren (→ SNS Alert)

**Common Findings:**

1. **UnauthorizedAccess:IAMUser/InstanceCredentialExfiltration**
   - Credentials wurden außerhalb AWS genutzt
   - Action: Credentials rotieren, Source IP blocken

2. **Recon:IAMUser/MaliciousIPCaller**
   - API Calls von bekannter böswilliger IP
   - Action: IP blocken, User Session beenden

3. **Persistence:IAMUser/AnomalousBehavior**
   - Ungewöhnliches User-Verhalten
   - Action: Untersuchen, ggf. Account sperren

**Auto-Response (Optional):**

```python
# Lambda Function triggered von GuardDuty Findings
def lambda_handler(event, context):
    finding = event['detail']
    severity = finding['severity']
    
    if severity >= 7:  # High/Critical
        # Isolate compromised instance
        # Revoke credentials
        # Send detailed alert
        pass
```

### Security Hub - Compliance Dashboard

**Zentrale Übersicht:**

- CIS AWS Foundations Benchmark
- AWS Foundational Security Best Practices
- PCI-DSS (optional)
- GDPR (manual checks)

**Security Hub Console:**

```bash
terraform output security_monitoring_urls
# → security_hub: https://...
```

**Security Score:**

- 100% = Alle Checks passed
- < 90% = Action required
- Critical/High Findings → SNS Alert

**Common Findings:**

1. **S3.1: S3 buckets should have public access blocked**
   - Status: ✅ PASSED (alle Buckets haben Public Access Block)

2. **RDS.2: RDS DB instances should prohibit public access**
   - Status: ✅ PASSED (Aurora in private subnets)

3. **IAM.1: IAM policies should not allow full "*:*" privileges**
   - Status: ⚠️ WARNING (prüfen)

4. **Lambda.1: Lambda functions should restrict public access**
   - Status: ✅ PASSED (nur via API Gateway)

**Remediation:**

Security Hub gibt automatische Remediation-Steps:

```bash
# Example: Fix S3 Public Access
aws s3api put-public-access-block \
  --bucket overcloud-dev-customer-data-123456789012 \
  --public-access-block-configuration \
    BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
```

## 4. Proactive Monitoring

### Health Checks

**Externe Monitoring (Optional):**

- UptimeRobot, Pingdom, StatusCake
- Check API Endpoint alle 1 Minute
- Alert bei Downtime > 2 Minuten

```bash
# UptimeRobot konfigurieren
URL: https://abc123.execute-api.eu-central-1.amazonaws.com/health
Method: GET
Expected Response: 200 OK
Alert Contacts: Email, Slack
```

**Synthetic Monitoring:**

```python
# Lambda CloudWatch Synthetics Canary
from aws_synthetics.selenium import synthetics_webdriver as syn_webdriver
from aws_synthetics.common import synthetics_logger as logger

def handler(event, context):
    """Synthetic test - API health check."""
    url = "https://abc123.execute-api.eu-central-1.amazonaws.com"
    browser = syn_webdriver.Chrome()
    browser.get(f"{url}/health")
    
    # Check response
    response = browser.page_source
    assert "healthy" in response
    
    # Test critical endpoints
    browser.get(f"{url}/api/v1/architectures")
    assert browser.status_code == 200
    
    logger.info("✅ All checks passed")
```

### Performance Monitoring

**X-Ray Tracing (Optional):**

```python
# app/main.py
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.ext.fastapi.middleware import XRayMiddleware

app.add_middleware(XRayMiddleware, recorder=xray_recorder)

@app.get("/api/v1/architectures")
@xray_recorder.capture("get_architectures")
async def get_architectures():
    # Request wird getracet
    pass
```

**Metrics to Track:**

- Cold Start Duration
- API Response Time (p50, p95, p99)
- Database Query Time
- S3 Operation Time
- Terraform Execution Time

## 5. Incident Response

### Alert kommt rein - Was tun?

#### Critical Alert: Lambda Errors

**1. Identifiziere Fehler:**

```bash
# CloudWatch Logs
aws logs tail /aws/lambda/overcloud-dev-api --follow --filter-pattern "ERROR"

# Oder Logs Insights
fields @timestamp, @message, level, error, traceback
| filter level = "ERROR"
| sort @timestamp desc
| limit 20
```

**2. Analyse:**

- Ist es ein Code-Fehler? → Fix + Deploy
- Ist es eine Dependency? → Check AWS Service Status
- Ist es eine Rate Limit? → Throttling Config anpassen

**3. Mitigate:**

```bash
# Rollback zu vorheriger Version
aws lambda update-function-code \
  --function-name overcloud-dev-api \
  --image-uri <PREVIOUS_IMAGE_URI>

# Oder: Provisioned Concurrency erhöhen
aws lambda put-provisioned-concurrency-config \
  --function-name overcloud-dev-api \
  --provisioned-concurrent-executions 2
```

**4. Post-Mortem:**

- Root Cause dokumentieren
- Prevention Maßnahmen
- Monitoring verbessern

#### Critical Alert: API 5XX Errors

**1. Check Lambda:**

```bash
# Lambda Errors?
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Errors \
  --dimensions Name=FunctionName,Value=overcloud-dev-api \
  --start-time $(date -u -d '1 hour ago' --iso-8601=seconds) \
  --end-time $(date -u --iso-8601=seconds) \
  --period 300 \
  --statistics Sum
```

**2. Check API Gateway:**

```bash
# API Gateway Logs
aws logs tail /aws/apigateway/overcloud-dev-http-api --follow
```

**3. Check Aurora:**

```bash
# Database Connection Errors?
aws rds describe-db-clusters \
  --db-cluster-identifier overcloud-dev-aurora \
  --query 'DBClusters[0].Status'
```

#### Critical Alert: Root Account Usage

**🚨 SOFORT HANDELN:**

```bash
# 1. Change Root Password
aws iam update-login-profile --user-name root --password <NEW_STRONG_PASSWORD>

# 2. Enable MFA
aws iam enable-mfa-device --user-name root --serial-number <MFA_SERIAL> --authentication-code1 <CODE1> --authentication-code2 <CODE2>

# 3. Check CloudTrail - Was wurde gemacht?
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=User,AttributeValue=root

# 4. Rotate ALL Credentials
# 5. Review ALL IAM Policies
# 6. Check for new IAM Users/Roles
aws iam list-users
aws iam list-roles --query 'Roles[?contains(CreateDate, `2026-04-18`)]'
```

## 6. Best Practices

### Monitoring

✅ **DO:**
- Alerts für alle kritischen Metriken setzen
- Dashboard täglich checken
- Log Retention passend zur Compliance (90+ Tage für prod)
- Custom Metrics für Business Logic tracken
- Synthetic Tests für critical paths

❌ **DON'T:**
- Zu viele Alerts (Alert Fatigue)
- Alerts ohne Action (sinnlos)
- Logs ohne Retention Policy (teuer)
- Monitoring erst nach Incident hinzufügen

### Security

✅ **DO:**
- CloudTrail IMMER aktiviert
- GuardDuty aktiviert
- Security Hub regelmäßig checken (wöchentlich)
- Credentials rotieren (90 Tage)
- Least Privilege IAM Policies
- Multi-Factor Auth für alle Users
- Security Findings sofort behandeln

❌ **DON'T:**
- Root Account nutzen (außer Notfall)
- Access Keys langfristig nutzen (nur Roles)
- Public S3 Buckets (außer explizit gewollt)
- Secrets in Code oder Logs
- Security Findings ignorieren

### Cost Optimization

**Monitoring Kosten:**

- CloudWatch Logs: ~$0.50/GB ingested, $0.03/GB stored
- CloudWatch Metrics: $0.30 pro Metric/Monat
- CloudWatch Alarms: $0.10 pro Alarm/Monat
- CloudTrail: $2 pro 100k Data Events
- GuardDuty: ~$10-20/Monat
- Security Hub: $0.0010 pro Check

**Dev Environment (~$15/Monat):**
- 10 GB Logs: $5
- 50 Metrics: $15
- 20 Alarms: $2
- CloudTrail: $2
- GuardDuty: $10
- **Total: ~$34/Monat**

**Production (~$100/Monat):**
- 100 GB Logs: $50
- 200 Metrics: $60
- 50 Alarms: $5
- CloudTrail: $20
- GuardDuty: $20
- Security Hub: $10
- **Total: ~$165/Monat**

## 7. Dashboards & Reports

### Weekly Security Report

```bash
#!/bin/bash
# weekly-security-report.sh

# GuardDuty Findings
aws guardduty list-findings \
  --detector-id $(aws guardduty list-detectors --query 'DetectorIds[0]' --output text) \
  --finding-criteria 'Criterion={updatedAt={Gte=604800000}}' \
  --max-results 50

# Security Hub Compliance Score
aws securityhub get-findings \
  --filters 'ComplianceStatus=[{Value=FAILED,Comparison=EQUALS}]' \
  --max-results 100

# Unauthorized API Calls
aws cloudwatch get-metric-statistics \
  --namespace OverCloud/Security \
  --metric-name UnauthorizedAPICalls \
  --start-time $(date -u -d '7 days ago' --iso-8601=seconds) \
  --end-time $(date -u --iso-8601=seconds) \
  --period 86400 \
  --statistics Sum
```

### Monthly Cost Report

```bash
# AWS Cost Explorer
aws ce get-cost-and-usage \
  --time-period Start=$(date -u -d '1 month ago' +%Y-%m-01),End=$(date -u +%Y-%m-01) \
  --granularity MONTHLY \
  --metrics "UnblendedCost" \
  --group-by Type=SERVICE

# Top 10 teuerste Services
aws ce get-cost-and-usage \
  --time-period Start=$(date -u -d '1 month ago' +%Y-%m-01),End=$(date -u +%Y-%m-01) \
  --granularity MONTHLY \
  --metrics "UnblendedCost" \
  --group-by Type=SERVICE \
  | jq '.ResultsByTime[0].Groups | sort_by(.Metrics.UnblendedCost.Amount | tonumber) | reverse | .[0:10]'
```

## Links

- [CloudWatch Dashboard Docs](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Dashboards.html)
- [CloudTrail Best Practices](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/best-practices-security.html)
- [GuardDuty Findings](https://docs.aws.amazon.com/guardduty/latest/ug/guardduty_findings.html)
- [Security Hub Controls](https://docs.aws.amazon.com/securityhub/latest/userguide/securityhub-controls.html)
- [AWS Well-Architected Framework - Security Pillar](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/welcome.html)
