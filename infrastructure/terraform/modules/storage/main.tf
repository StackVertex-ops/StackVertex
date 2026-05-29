# Storage Module - S3 Buckets for Deployments

terraform {
  required_version = ">= 1.5.0"
}

# S3 Bucket für Customer Deployment States
resource "aws_s3_bucket" "deployment_states" {
  bucket = "${var.project_name}-${var.environment}-deployment-states-${var.aws_account_id}"

  tags = {
    Name = "${var.project_name}-${var.environment}-deployment-states"
  }
}

# Versioning für Deployment States
resource "aws_s3_bucket_versioning" "deployment_states" {
  bucket = aws_s3_bucket.deployment_states.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Encryption at rest
resource "aws_s3_bucket_server_side_encryption_configuration" "deployment_states" {
  bucket = aws_s3_bucket.deployment_states.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Block public access
resource "aws_s3_bucket_public_access_block" "deployment_states" {
  bucket = aws_s3_bucket.deployment_states.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Lifecycle rules für alte Deployment States
resource "aws_s3_bucket_lifecycle_configuration" "deployment_states" {
  bucket = aws_s3_bucket.deployment_states.id

  rule {
    id     = "archive-old-deployments"
    status = "Enabled"

    filter {}

    # Nach 30 Tagen → Infrequent Access
    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    # Expiration muss größer sein als alle Transitions
    expiration {
      days = var.deployment_retention_days
    }
  }

  rule {
    id     = "delete-old-versions"
    status = "Enabled"

    filter {}

    noncurrent_version_transition {
      noncurrent_days = 30
      storage_class   = "STANDARD_IA"
    }

    noncurrent_version_expiration {
      noncurrent_days = 90
    }
  }
}

# S3 Bucket für Terraform Workspaces (temporäre Files während Deployment)
resource "aws_s3_bucket" "terraform_workspaces" {
  count  = var.create_workspace_bucket ? 1 : 0
  bucket = "${var.project_name}-${var.environment}-terraform-workspaces-${var.aws_account_id}"

  tags = {
    Name = "${var.project_name}-${var.environment}-terraform-workspaces"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_workspaces" {
  count  = var.create_workspace_bucket ? 1 : 0
  bucket = aws_s3_bucket.terraform_workspaces[0].id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "terraform_workspaces" {
  count  = var.create_workspace_bucket ? 1 : 0
  bucket = aws_s3_bucket.terraform_workspaces[0].id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Lifecycle: Auto-delete nach 7 Tagen (nur temporäre Daten)
resource "aws_s3_bucket_lifecycle_configuration" "terraform_workspaces" {
  count  = var.create_workspace_bucket ? 1 : 0
  bucket = aws_s3_bucket.terraform_workspaces[0].id

  rule {
    id     = "auto-delete-temp-files"
    status = "Enabled"

    filter {}

    expiration {
      days = 7
    }
  }
}

# S3 Bucket für Large Items (DynamoDB offload > 300KB)
# Stores: architecture_json, terraform_state, plan/apply outputs
resource "aws_s3_bucket" "large_items" {
  bucket = "${var.project_name}-${var.environment}-large-items-${var.aws_account_id}"

  tags = {
    Name = "${var.project_name}-${var.environment}-large-items"
  }
}

# Versioning für Large Items (ermöglicht Rollback)
resource "aws_s3_bucket_versioning" "large_items" {
  bucket = aws_s3_bucket.large_items.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Encryption at rest
resource "aws_s3_bucket_server_side_encryption_configuration" "large_items" {
  bucket = aws_s3_bucket.large_items.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Block public access
resource "aws_s3_bucket_public_access_block" "large_items" {
  bucket = aws_s3_bucket.large_items.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Lifecycle rules für Large Items
resource "aws_s3_bucket_lifecycle_configuration" "large_items" {
  bucket = aws_s3_bucket.large_items.id

  rule {
    id     = "intelligent-tiering"
    status = "Enabled"

    filter {}

    # Nach 30 Tagen → Intelligent Tiering (auto-optimize)
    transition {
      days          = 30
      storage_class = "INTELLIGENT_TIERING"
    }
  }

  rule {
    id     = "delete-old-versions"
    status = "Enabled"

    filter {}

    # Alte Versionen nach 90 Tagen löschen
    noncurrent_version_expiration {
      noncurrent_days = 90
    }
  }
}
