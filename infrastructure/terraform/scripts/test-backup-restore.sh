#!/bin/bash
#
# Backup Restore Test Script für OverCloud
# Testet DynamoDB + S3 Backup-Wiederherstellung
#
# Usage: ./test-backup-restore.sh [environment]
# Example: ./test-backup-restore.sh staging
#

set -e
set -u

# Configuration
ENV="${1:-staging}"
AWS_REGION="${AWS_REGION:-us-east-1}"
DYNAMODB_TABLE="overcloud-${ENV}-main"
S3_BUCKET="overcloud-${ENV}-large-items"
TIMESTAMP=$(date +"%Y%m%d-%H%M%S")
TEST_TABLE="overcloud-test-restore-$TIMESTAMP"
TEST_BUCKET="overcloud-test-restore-$TIMESTAMP"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0;33m'

log() { echo "[$(date +'%H:%M:%S')] $1"; }
success() { echo -e "${GREEN}✅ $1${NC}"; }
error() { echo -e "${RED}❌ $1${NC}"; exit 1; }
warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }

cleanup() {
    log "Cleaning up test resources..."
    aws dynamodb delete-table --table-name "$TEST_TABLE" --region "$AWS_REGION" 2>/dev/null || true
    aws s3 rb "s3://$TEST_BUCKET" --force 2>/dev/null || true
    success "Cleanup done"
}
trap cleanup EXIT

log "========================================="
log "Backup Restore Test - Environment: $ENV"
log "========================================="

# 1. Check source table
log "Checking source table..."
SOURCE_COUNT=$(aws dynamodb scan --table-name "$DYNAMODB_TABLE" --select "COUNT" --region "$AWS_REGION" --output text --query 'Count' || error "Source table not found")
log "Source items: $SOURCE_COUNT"

# 2. Create backup
log "Creating backup..."
BACKUP_ARN=$(aws dynamodb create-backup --table-name "$DYNAMODB_TABLE" --backup-name "test-$TIMESTAMP" --region "$AWS_REGION" --output text --query 'BackupDetails.BackupArn')
log "Waiting for backup..."
aws dynamodb wait backup-completion --backup-arn "$BACKUP_ARN" --region "$AWS_REGION" || error "Backup failed"
success "Backup created"

# 3. Restore to test table
log "Restoring to test table..."
aws dynamodb restore-table-from-backup --target-table-name "$TEST_TABLE" --backup-arn "$BACKUP_ARN" --region "$AWS_REGION" >/dev/null
log "Waiting for restore (may take 5-10 min)..."
aws dynamodb wait table-exists --table-name "$TEST_TABLE" --region "$AWS_REGION" || error "Restore failed"
success "Restore complete"

# 4. Verify data
log "Verifying data..."
RESTORED_COUNT=$(aws dynamodb scan --table-name "$TEST_TABLE" --select "COUNT" --region "$AWS_REGION" --output text --query 'Count')
log "Restored items: $RESTORED_COUNT"

if [ "$SOURCE_COUNT" -ne "$RESTORED_COUNT" ]; then
    error "Item count mismatch! Expected: $SOURCE_COUNT, Got: $RESTORED_COUNT"
fi
success "Item counts match"

# 5. Test S3 backup
log "Testing S3 backup..."
aws s3 mb "s3://$TEST_BUCKET" --region "$AWS_REGION" >/dev/null
aws s3 sync "s3://$S3_BUCKET" "s3://$TEST_BUCKET" --quiet
SOURCE_S3_COUNT=$(aws s3 ls "s3://$S3_BUCKET" --recursive | wc -l)
TEST_S3_COUNT=$(aws s3 ls "s3://$TEST_BUCKET" --recursive | wc -l)
log "S3 objects: $SOURCE_S3_COUNT → $TEST_S3_COUNT"

if [ "$SOURCE_S3_COUNT" -ne "$TEST_S3_COUNT" ]; then
    error "S3 object count mismatch!"
fi
success "S3 backup verified"

# 6. Cleanup test backup
log "Deleting test backup..."
aws dynamodb delete-backup --backup-arn "$BACKUP_ARN" --region "$AWS_REGION" >/dev/null

# Summary
log "========================================="
success "BACKUP RESTORE TEST PASSED ✅"
log "========================================="
log "DynamoDB: $SOURCE_COUNT items restored correctly"
log "S3:       $SOURCE_S3_COUNT objects synced correctly"
log "Duration: $SECONDS seconds"
log "========================================="
