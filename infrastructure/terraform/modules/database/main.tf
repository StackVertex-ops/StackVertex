# Database Module - Aurora Serverless v2 PostgreSQL

terraform {
  required_version = ">= 1.5.0"
}

# DB Subnet Group
resource "aws_db_subnet_group" "aurora" {
  name       = "${var.project_name}-${var.environment}-aurora-subnet-group"
  subnet_ids = var.private_subnet_ids

  tags = {
    Name = "${var.project_name}-${var.environment}-aurora-subnet-group"
  }
}

# Aurora Cluster
resource "aws_rds_cluster" "aurora" {
  cluster_identifier      = "${var.project_name}-${var.environment}-aurora"
  engine                  = "aurora-postgresql"
  engine_mode             = "provisioned"
  engine_version          = var.postgres_version
  database_name           = var.database_name
  master_username         = var.master_username
  master_password         = var.master_password
  db_subnet_group_name    = aws_db_subnet_group.aurora.name
  vpc_security_group_ids  = [var.security_group_id]
  backup_retention_period = var.backup_retention_days
  preferred_backup_window = var.backup_window
  skip_final_snapshot     = var.skip_final_snapshot
  final_snapshot_identifier = var.skip_final_snapshot ? null : "${var.project_name}-${var.environment}-final-snapshot-${formatdate("YYYY-MM-DD-hhmm", timestamp())}"

  # Aurora Serverless v2 Scaling
  serverlessv2_scaling_configuration {
    min_capacity = var.min_capacity
    max_capacity = var.max_capacity
  }

  enabled_cloudwatch_logs_exports = ["postgresql"]

  tags = {
    Name = "${var.project_name}-${var.environment}-aurora-cluster"
  }
}

# Aurora Serverless v2 Instance
resource "aws_rds_cluster_instance" "aurora" {
  count              = var.instance_count
  identifier         = "${var.project_name}-${var.environment}-aurora-${count.index + 1}"
  cluster_identifier = aws_rds_cluster.aurora.id
  instance_class     = "db.serverless"
  engine             = aws_rds_cluster.aurora.engine
  engine_version     = aws_rds_cluster.aurora.engine_version

  performance_insights_enabled = var.enable_performance_insights

  tags = {
    Name = "${var.project_name}-${var.environment}-aurora-instance-${count.index + 1}"
  }
}

# Secrets Manager für DB Credentials
resource "aws_secretsmanager_secret" "db_credentials" {
  name = "${var.project_name}-${var.environment}-db-credentials"

  tags = {
    Name = "${var.project_name}-${var.environment}-db-credentials"
  }
}

resource "aws_secretsmanager_secret_version" "db_credentials" {
  secret_id = aws_secretsmanager_secret.db_credentials.id
  secret_string = jsonencode({
    username = var.master_username
    password = var.master_password
    host     = aws_rds_cluster.aurora.endpoint
    port     = aws_rds_cluster.aurora.port
    database = var.database_name
    engine   = "postgres"
  })
}

# CloudWatch Alarms
resource "aws_cloudwatch_metric_alarm" "aurora_cpu" {
  count               = var.enable_cloudwatch_alarms ? 1 : 0
  alarm_name          = "${var.project_name}-${var.environment}-aurora-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "Aurora CPU utilization is too high"
  alarm_actions       = var.alarm_sns_topic_arn != null ? [var.alarm_sns_topic_arn] : []

  dimensions = {
    DBClusterIdentifier = aws_rds_cluster.aurora.cluster_identifier
  }
}

resource "aws_cloudwatch_metric_alarm" "aurora_connections" {
  count               = var.enable_cloudwatch_alarms ? 1 : 0
  alarm_name          = "${var.project_name}-${var.environment}-aurora-high-connections"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "DatabaseConnections"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = var.max_connections_threshold
  alarm_description   = "Aurora database connections are too high"
  alarm_actions       = var.alarm_sns_topic_arn != null ? [var.alarm_sns_topic_arn] : []

  dimensions = {
    DBClusterIdentifier = aws_rds_cluster.aurora.cluster_identifier
  }
}
