# Database Module Outputs

output "cluster_id" {
  description = "Aurora cluster ID"
  value       = aws_rds_cluster.aurora.cluster_identifier
}

output "cluster_endpoint" {
  description = "Aurora cluster endpoint (writer)"
  value       = aws_rds_cluster.aurora.endpoint
}

output "cluster_reader_endpoint" {
  description = "Aurora cluster reader endpoint"
  value       = aws_rds_cluster.aurora.reader_endpoint
}

output "cluster_port" {
  description = "Aurora cluster port"
  value       = aws_rds_cluster.aurora.port
}

output "database_name" {
  description = "Database name"
  value       = aws_rds_cluster.aurora.database_name
}

output "master_username" {
  description = "Master username"
  value       = aws_rds_cluster.aurora.master_username
  sensitive   = true
}

output "secret_arn" {
  description = "ARN of Secrets Manager secret containing database credentials"
  value       = aws_secretsmanager_secret.db_credentials.arn
}

output "secret_name" {
  description = "Name of Secrets Manager secret"
  value       = aws_secretsmanager_secret.db_credentials.name
}

output "connection_string" {
  description = "PostgreSQL connection string (without password)"
  value       = "postgresql://${var.master_username}@${aws_rds_cluster.aurora.endpoint}:${aws_rds_cluster.aurora.port}/${var.database_name}"
  sensitive   = true
}
