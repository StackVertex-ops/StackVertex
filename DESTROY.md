# StackVertex - Complete Teardown Guide

> **WICHTIG:** Dieser Guide ist speziell für **Pluralsight Sandbox** (4h Zeit-Limit)  
> Am Ende deines Tests: Alles cleanen um Kosten zu vermeiden!

---

## ⏱️ Zeit-Budget

- **Deployment:** ~30-45 Minuten
- **Testing:** ~2-3 Stunden
- **⚠️ DESTROY:** ~15-20 Minuten ← **RESERVE ZEIT!**

**→ Starte Destroy spätestens nach 3:40h!**

---

## 🗑️ Complete Teardown (Schnell-Methode)

### **Option 1: Terraform Destroy (Empfohlen)**

```bash
# 1. Gehe ins Terraform Environment
cd infrastructure/terraform/environments/dev

# 2. Destroy ALL resources
terraform destroy -auto-approve

# ODER: Mit Target (schneller, falls nur bestimmte Module)
terraform destroy -auto-approve \
  -target=module.lambda_api \
  -target=module.api_gateway \
  -target=module.dynamodb \
  -target=module.storage
```

**Dauer:** ~10-15 Minuten

---

### **Option 2: Cleanup Script (Noch schneller)**

```bash
# Im Root-Verzeichnis:
./infrastructure/scripts/destroy-all.sh
```

**Das Script macht:**
1. ✅ Terraform destroy (alle Environments)
2. ✅ Leert S3 Buckets (sonst Destroy-Error!)
3. ✅ Löscht DynamoDB Tables
4. ✅ Löscht CloudWatch Log Groups
5. ✅ Cleanup Terraform State

**Dauer:** ~5-10 Minuten

---

## 📋 Manuelle Cleanup-Checkliste

Falls Terraform hängt oder Fehler auftreten:

### **1. S3 Buckets leeren & löschen**

```bash
# Liste alle StackVertex Buckets
aws s3 ls | grep stackvertex

# Für jeden Bucket:
aws s3 rm s3://stackvertex-dev-frontend --recursive
aws s3 rm s3://stackvertex-dev-large-items --recursive
aws s3 rm s3://stackvertex-user-data-dev --recursive
aws s3 rm s3://stackvertex-terraform-state --recursive

# Buckets löschen
aws s3 rb s3://stackvertex-dev-frontend
aws s3 rb s3://stackvertex-dev-large-items
aws s3 rb s3://stackvertex-user-data-dev
aws s3 rb s3://stackvertex-terraform-state
```

### **2. DynamoDB Tables löschen**

```bash
aws dynamodb delete-table --table-name stackvertex-dev-main
aws dynamodb delete-table --table-name stackvertex-terraform-locks
```

### **3. Lambda Functions löschen**

```bash
# Liste Functions
aws lambda list-functions --query 'Functions[?starts_with(FunctionName, `stackvertex`)].FunctionName'

# Lösche jede Function
aws lambda delete-function --function-name stackvertex-dev-api
aws lambda delete-function --function-name stackvertex-dev-websocket-connect
aws lambda delete-function --function-name stackvertex-dev-websocket-disconnect
aws lambda delete-function --function-name stackvertex-dev-websocket-message
```

### **4. API Gateway löschen**

```bash
# HTTP API
aws apigatewayv2 get-apis --query 'Items[?Name==`stackvertex-dev-http`].ApiId' --output text | \
  xargs -I {} aws apigatewayv2 delete-api --api-id {}

# WebSocket API
aws apigatewayv2 get-apis --query 'Items[?Name==`stackvertex-dev-websocket`].ApiId' --output text | \
  xargs -I {} aws apigatewayv2 delete-api --api-id {}
```

### **5. CloudFront Distributions**

```bash
# Liste Distributions
aws cloudfront list-distributions --query 'DistributionList.Items[?Comment==`stackvertex-dev-frontend`].Id'

# WICHTIG: CloudFront löschen dauert 15-20 Minuten!
# Disable erst, dann löschen:
aws cloudfront get-distribution-config --id <DIST-ID> > dist-config.json
# Edit: "Enabled": false
aws cloudfront update-distribution --id <DIST-ID> --if-match <ETAG> --distribution-config file://dist-config.json
# Warten bis disabled...
aws cloudfront delete-distribution --id <DIST-ID> --if-match <ETAG>
```

⚠️ **CloudFront-Tipp:** Überspringen falls Zeit knapp! Kostet nur wenn Traffic.

### **6. ECS Cluster & Tasks**

```bash
# Liste Clusters
aws ecs list-clusters

# Stoppe alle Tasks
aws ecs list-tasks --cluster stackvertex-dev | \
  xargs -I {} aws ecs stop-task --cluster stackvertex-dev --task {}

# Lösche Cluster
aws ecs delete-cluster --cluster stackvertex-dev
```

### **7. CloudWatch Log Groups**

```bash
# Liste Log Groups
aws logs describe-log-groups --query 'logGroups[?starts_with(logGroupName, `/aws/lambda/stackvertex`)].logGroupName'

# Lösche alle
aws logs describe-log-groups --query 'logGroups[?starts_with(logGroupName, `/aws/lambda/stackvertex`)].logGroupName' --output text | \
  xargs -I {} aws logs delete-log-group --log-group-name {}
```

### **8. IAM Roles & Policies (Optional)**

```bash
# Liste Roles
aws iam list-roles --query 'Roles[?starts_with(RoleName, `stackvertex`)].RoleName'

# Für jede Role: Detach Policies, dann löschen
aws iam list-attached-role-policies --role-name stackvertex-dev-lambda-role --query 'AttachedPolicies[].PolicyArn' --output text | \
  xargs -I {} aws iam detach-role-policy --role-name stackvertex-dev-lambda-role --policy-arn {}

aws iam delete-role --role-name stackvertex-dev-lambda-role
```

### **9. VPC & Networking (Falls erstellt)**

```bash
# Liste VPCs
aws ec2 describe-vpcs --filters "Name=tag:Name,Values=stackvertex*"

# NAT Gateways löschen (dauert ~2-3 Min)
aws ec2 describe-nat-gateways --filter "Name=tag:Name,Values=stackvertex*" --query 'NatGateways[].NatGatewayId' --output text | \
  xargs -I {} aws ec2 delete-nat-gateway --nat-gateway-id {}

# Internet Gateways detachen & löschen
aws ec2 describe-internet-gateways --filters "Name=tag:Name,Values=stackvertex*" --query 'InternetGateways[].[InternetGatewayId,Attachments[0].VpcId]' --output text | \
  while read igw vpc; do
    aws ec2 detach-internet-gateway --internet-gateway-id $igw --vpc-id $vpc
    aws ec2 delete-internet-gateway --internet-gateway-id $igw
  done

# Subnets löschen
aws ec2 describe-subnets --filters "Name=tag:Name,Values=stackvertex*" --query 'Subnets[].SubnetId' --output text | \
  xargs -I {} aws ec2 delete-subnet --subnet-id {}

# Security Groups löschen
aws ec2 describe-security-groups --filters "Name=tag:Name,Values=stackvertex*" --query 'SecurityGroups[].GroupId' --output text | \
  xargs -I {} aws ec2 delete-security-group --group-id {}

# VPC löschen
aws ec2 describe-vpcs --filters "Name=tag:Name,Values=stackvertex*" --query 'Vpcs[].VpcId' --output text | \
  xargs -I {} aws ec2 delete-vpc --vpc-id {}
```

---

## 🚨 Häufige Destroy-Probleme

### **Problem 1: S3 Bucket nicht leer**

```
Error: BucketNotEmpty
```

**Lösung:**
```bash
aws s3 rm s3://bucket-name --recursive
```

### **Problem 2: DynamoDB Table hat Backups**

```
Error: ResourceInUseException
```

**Lösung:**
```bash
# Liste Backups
aws dynamodb list-backups --table-name stackvertex-dev-main

# Lösche alle Backups
aws dynamodb list-backups --table-name stackvertex-dev-main --query 'BackupSummaries[].BackupArn' --output text | \
  xargs -I {} aws dynamodb delete-backup --backup-arn {}
```

### **Problem 3: Lambda hat Event Source Mappings**

```
Error: ResourceInUseException
```

**Lösung:**
```bash
# Liste Mappings
aws lambda list-event-source-mappings --function-name stackvertex-dev-api

# Lösche Mapping
aws lambda delete-event-source-mapping --uuid <UUID>
```

### **Problem 4: CloudFront Distribution "InUse"**

```
Error: DistributionNotDisabled
```

**Lösung:**
```bash
# Warte 15-20 Minuten nach Disable
# ODER: Überspringen (kostet nur bei Traffic)
```

---

## ⚡ Quick-Destroy Script

```bash
#!/bin/bash
# File: infrastructure/scripts/quick-destroy.sh

set -e

echo "🗑️  Quick Destroy - StackVertex Infrastructure"
echo "=============================================="

# 1. Terraform Destroy (mit Force-Unlock falls nötig)
cd infrastructure/terraform/environments/dev
terraform destroy -auto-approve || {
  echo "⚠️  Terraform destroy failed, trying force-unlock..."
  terraform force-unlock -force $(terraform state list | head -1)
  terraform destroy -auto-approve
}

# 2. Manual Cleanup (S3, DynamoDB)
cd ../../../..
./infrastructure/scripts/cleanup-aws-resources.sh

echo "✅ Destroy complete!"
```

---

## 📊 Kosten nach Destroy

**Sofort gestoppt:**
- ✅ Lambda (keine Invocations)
- ✅ API Gateway (keine Requests)
- ✅ DynamoDB (gelöscht)
- ✅ ECS (keine Tasks)

**Dauert bis $0:**
- ⏳ CloudFront (~15 Min bis disabled)
- ⏳ CloudWatch Logs (bis Retention abläuft)

**Restkosten (minimal):**
- Route53 Hosted Zone: $0.50/Monat (bleibt)
- S3 Terraform State: ~$0.01 (bis manuell gelöscht)

---

## ✅ Verifikation (Alles weg?)

```bash
# Check alle Ressourcen
aws resourcegroupstaggingapi get-resources \
  --tag-filters Key=Project,Values=stackvertex \
  --query 'ResourceTagMappingList[].ResourceARN'

# Sollte leer sein: []
```

---

## 🎯 Empfohlener Workflow (Pluralsight Sandbox)

```
00:00 - Start Sandbox
00:15 - Bootstrap (S3, DynamoDB für State)
00:30 - Terraform Apply (Infrastructure)
01:00 - Testing & Development
03:30 - ⚠️  START DESTROY!
03:45 - Terraform Destroy
03:55 - Manual Cleanup (falls nötig)
04:00 - Sandbox endet
```

**→ NIEMALS später als 03:30 mit Destroy starten!**

---

## 📞 Support

**Falls Probleme beim Destroy:**
1. Check Terraform State: `terraform state list`
2. Force Unlock: `terraform force-unlock <LOCK-ID>`
3. Manual Cleanup: Siehe Checkliste oben

**Logs checken:**
```bash
terraform destroy -auto-approve 2>&1 | tee destroy.log
```

---

**Last Updated:** 2026-05-26  
**Version:** 1.0.0
