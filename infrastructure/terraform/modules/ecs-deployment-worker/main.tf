/**
 * ECS Deployment Worker Module
 *
 * Erstellt ECS Fargate Task Definition für on-demand Terraform Deployments.
 * KEIN ECS Service! Tasks werden on-demand via boto3 gestartet.
 *
 * Features:
 * - Fargate Spot (70% günstiger als Fargate)
 * - On-demand Start via ecs.run_task()
 * - Terraform pre-installed im Container
 * - Volle AWS Permissions für Customer Deployments
 */

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# ==========================================
# ECS Cluster
# ==========================================

resource "aws_ecs_cluster" "deployment" {
  name = "${var.project_name}-${var.environment}-deployment-cluster"

  setting {
    name  = "containerInsights"
    value = var.enable_container_insights ? "enabled" : "disabled"
  }

  tags = merge(var.tags, {
    Name        = "${var.project_name}-${var.environment}-deployment-cluster"
    Environment = var.environment
  })
}

# Fargate Spot Capacity Provider
resource "aws_ecs_cluster_capacity_providers" "deployment" {
  cluster_name = aws_ecs_cluster.deployment.name

  capacity_providers = ["FARGATE_SPOT", "FARGATE"]

  default_capacity_provider_strategy {
    capacity_provider = "FARGATE_SPOT"
    weight            = 100
    base              = 0
  }
}

# ==========================================
# ECS Task Definition
# ==========================================

resource "aws_ecs_task_definition" "deployment_worker" {
  family                   = "${var.project_name}-${var.environment}-deployment-worker"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.task_cpu
  memory                   = var.task_memory

  execution_role_arn = aws_iam_role.task_execution.arn
  task_role_arn      = aws_iam_role.task_role.arn

  container_definitions = jsonencode([
    {
      name      = "deployment-worker"
      image     = var.container_image
      essential = true

      # Environment Variables (global, für alle Tasks)
      environment = concat([
        {
          name  = "AWS_REGION"
          value = var.aws_region
        },
        {
          name  = "ENV"
          value = var.environment
        },
        {
          name  = "DYNAMODB_TABLE_NAME"
          value = var.dynamodb_table_name
        },
        {
          name  = "S3_LARGE_ITEMS_BUCKET"
          value = var.s3_bucket_name
        },
        {
          name  = "USER_DATA_BUCKET"
          value = var.user_data_bucket_name
        }
      ], var.extra_environment_variables)

      # Secrets (aus Secrets Manager)
      secrets = compact([
        var.jwt_secret_arn != "" ? {
          name      = "SECRET_KEY"
          valueFrom = var.jwt_secret_arn
        } : null
      ])

      # CloudWatch Logs
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.deployment_worker.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }

      # Resource Limits
      ulimits = []

      # Health Check (optional)
      # Nicht notwendig für Tasks (nur für Services)

      # Linux Parameters
      linuxParameters = {
        initProcessEnabled = true
      }
    }
  ])

  tags = merge(var.tags, {
    Name        = "${var.project_name}-${var.environment}-deployment-worker"
    Environment = var.environment
  })
}

# ==========================================
# CloudWatch Log Group
# ==========================================

resource "aws_cloudwatch_log_group" "deployment_worker" {
  name              = "/ecs/${var.project_name}-${var.environment}-deployment-worker"
  retention_in_days = var.log_retention_days

  tags = merge(var.tags, {
    Name        = "${var.project_name}-${var.environment}-deployment-worker-logs"
    Environment = var.environment
  })
}

# ==========================================
# IAM Role: Task Execution Role
# ==========================================

resource "aws_iam_role" "task_execution" {
  name               = "${var.project_name}-${var.environment}-ecs-task-execution"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume_role.json

  tags = merge(var.tags, {
    Name        = "${var.project_name}-${var.environment}-ecs-task-execution"
    Environment = var.environment
  })
}

data "aws_iam_policy_document" "ecs_assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

# Managed Policy: ECS Task Execution Role Policy
resource "aws_iam_role_policy_attachment" "task_execution" {
  role       = aws_iam_role.task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Custom Policy: Secrets Manager Access
resource "aws_iam_role_policy" "task_execution_secrets" {
  name   = "${var.project_name}-${var.environment}-ecs-execution-secrets"
  role   = aws_iam_role.task_execution.id
  policy = data.aws_iam_policy_document.task_execution_secrets.json
}

data "aws_iam_policy_document" "task_execution_secrets" {
  statement {
    effect = "Allow"
    actions = [
      "secretsmanager:GetSecretValue",
    ]
    resources = compact([
      var.jwt_secret_arn,
    ])
  }
}

# ==========================================
# IAM Role: Task Role (Runtime Permissions)
# ==========================================

resource "aws_iam_role" "task_role" {
  name               = "${var.project_name}-${var.environment}-ecs-task-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume_role.json

  tags = merge(var.tags, {
    Name        = "${var.project_name}-${var.environment}-ecs-task-role"
    Environment = var.environment
  })
}

# Custom Policy: Full AWS Access für Customer Deployments
resource "aws_iam_role_policy" "task_role_permissions" {
  name   = "${var.project_name}-${var.environment}-ecs-task-permissions"
  role   = aws_iam_role.task_role.id
  policy = data.aws_iam_policy_document.task_role_permissions.json
}

data "aws_iam_policy_document" "task_role_permissions" {
  # DynamoDB Access
  statement {
    effect = "Allow"
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
      "dynamodb:DeleteItem",
      "dynamodb:Query",
      "dynamodb:Scan",
      "dynamodb:BatchGetItem",
      "dynamodb:BatchWriteItem",
    ]
    resources = [
      "arn:aws:dynamodb:${var.aws_region}:*:table/${var.dynamodb_table_name}",
      "arn:aws:dynamodb:${var.aws_region}:*:table/${var.dynamodb_table_name}/index/*",
    ]
  }

  # S3 Full Access (für Customer Deployments + Platform Storage)
  statement {
    effect = "Allow"
    actions = [
      "s3:*",
    ]
    resources = [
      "arn:aws:s3:::${var.s3_bucket_name}",
      "arn:aws:s3:::${var.s3_bucket_name}/*",
      "arn:aws:s3:::${var.user_data_bucket_name}",
      "arn:aws:s3:::${var.user_data_bucket_name}/*",
      "arn:aws:s3:::*",  # Full S3 Access für Customer Buckets
    ]
  }

  # EC2 Full Access (für Customer VPCs, EC2 Instances, etc.)
  statement {
    effect = "Allow"
    actions = [
      "ec2:*",
    ]
    resources = ["*"]
  }

  # RDS Full Access (für Customer Databases)
  statement {
    effect = "Allow"
    actions = [
      "rds:*",
    ]
    resources = ["*"]
  }

  # Lambda Full Access (für Customer Functions)
  statement {
    effect = "Allow"
    actions = [
      "lambda:*",
    ]
    resources = ["*"]
  }

  # ECS Full Access (für Customer ECS Clusters)
  statement {
    effect = "Allow"
    actions = [
      "ecs:*",
    ]
    resources = ["*"]
  }

  # IAM Limited Access (für Customer IAM Roles)
  statement {
    effect = "Allow"
    actions = [
      "iam:CreateRole",
      "iam:DeleteRole",
      "iam:AttachRolePolicy",
      "iam:DetachRolePolicy",
      "iam:PutRolePolicy",
      "iam:DeleteRolePolicy",
      "iam:GetRole",
      "iam:GetRolePolicy",
      "iam:ListRolePolicies",
      "iam:ListAttachedRolePolicies",
      "iam:PassRole",
      "iam:CreateInstanceProfile",
      "iam:DeleteInstanceProfile",
      "iam:AddRoleToInstanceProfile",
      "iam:RemoveRoleFromInstanceProfile",
      "iam:GetInstanceProfile",
    ]
    resources = ["*"]
  }

  # CloudFormation (optional, für Stack Management)
  statement {
    effect = "Allow"
    actions = [
      "cloudformation:DescribeStacks",
      "cloudformation:DescribeStackResources",
      "cloudformation:GetTemplate",
    ]
    resources = ["*"]
  }

  # Secrets Manager (read-only für Platform Secrets)
  statement {
    effect = "Allow"
    actions = [
      "secretsmanager:GetSecretValue",
    ]
    resources = compact([
      var.jwt_secret_arn,
    ])
  }

  # CloudWatch Logs
  statement {
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = [
      "arn:aws:logs:${var.aws_region}:*:log-group:/ecs/${var.project_name}-${var.environment}-deployment-worker",
      "arn:aws:logs:${var.aws_region}:*:log-group:/ecs/${var.project_name}-${var.environment}-deployment-worker:*",
    ]
  }

  # API Gateway Management API (für WebSocket postToConnection)
  statement {
    effect = "Allow"
    actions = [
      "execute-api:ManageConnections",
    ]
    resources = [
      "arn:aws:execute-api:${var.aws_region}:*:*/*",
    ]
  }

  # STS AssumeRole (für Customer Account Access via Credentials)
  statement {
    effect = "Allow"
    actions = [
      "sts:AssumeRole",
    ]
    resources = ["*"]
  }
}

# ==========================================
# Security Group
# ==========================================

resource "aws_security_group" "deployment_worker" {
  name        = "${var.project_name}-${var.environment}-deployment-worker-sg"
  description = "Security Group for ECS Deployment Workers"
  vpc_id      = var.vpc_id

  # Outbound: Allow all (Worker needs to access AWS services + Customer resources)
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }

  tags = merge(var.tags, {
    Name        = "${var.project_name}-${var.environment}-deployment-worker-sg"
    Environment = var.environment
  })
}

# ==========================================
# ECR Repository (für Container Images)
# ==========================================

resource "aws_ecr_repository" "deployment_worker" {
  name                 = "${var.project_name}-${var.environment}-deployment-worker"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = merge(var.tags, {
    Name        = "${var.project_name}-${var.environment}-deployment-worker"
    Environment = var.environment
  })
}

# ECR Lifecycle Policy (auto-delete old images)
resource "aws_ecr_lifecycle_policy" "deployment_worker" {
  repository = aws_ecr_repository.deployment_worker.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 10 images"
        selection = {
          tagStatus     = "any"
          countType     = "imageCountMoreThan"
          countNumber   = 10
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}
