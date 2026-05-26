/**
 * ECS Deployment Worker Module - Outputs
 */

# ==========================================
# ECS Cluster
# ==========================================

output "cluster_name" {
  description = "ECS Cluster name"
  value       = aws_ecs_cluster.deployment.name
}

output "cluster_arn" {
  description = "ECS Cluster ARN"
  value       = aws_ecs_cluster.deployment.arn
}

output "cluster_id" {
  description = "ECS Cluster ID"
  value       = aws_ecs_cluster.deployment.id
}

# ==========================================
# ECS Task Definition
# ==========================================

output "task_definition_arn" {
  description = "ECS Task Definition ARN"
  value       = aws_ecs_task_definition.deployment_worker.arn
}

output "task_definition_family" {
  description = "ECS Task Definition family"
  value       = aws_ecs_task_definition.deployment_worker.family
}

output "task_definition_revision" {
  description = "ECS Task Definition revision"
  value       = aws_ecs_task_definition.deployment_worker.revision
}

# ==========================================
# IAM Roles
# ==========================================

output "task_execution_role_arn" {
  description = "ECS Task Execution Role ARN"
  value       = aws_iam_role.task_execution.arn
}

output "task_execution_role_name" {
  description = "ECS Task Execution Role name"
  value       = aws_iam_role.task_execution.name
}

output "task_role_arn" {
  description = "ECS Task Role ARN (runtime permissions)"
  value       = aws_iam_role.task_role.arn
}

output "task_role_name" {
  description = "ECS Task Role name"
  value       = aws_iam_role.task_role.name
}

# ==========================================
# Security Group
# ==========================================

output "security_group_id" {
  description = "Security Group ID for ECS Tasks"
  value       = aws_security_group.deployment_worker.id
}

output "security_group_name" {
  description = "Security Group name"
  value       = aws_security_group.deployment_worker.name
}

# ==========================================
# CloudWatch Logs
# ==========================================

output "log_group_name" {
  description = "CloudWatch Log Group name"
  value       = aws_cloudwatch_log_group.deployment_worker.name
}

output "log_group_arn" {
  description = "CloudWatch Log Group ARN"
  value       = aws_cloudwatch_log_group.deployment_worker.arn
}

# ==========================================
# ECR Repository
# ==========================================

output "ecr_repository_url" {
  description = "ECR Repository URL"
  value       = aws_ecr_repository.deployment_worker.repository_url
}

output "ecr_repository_arn" {
  description = "ECR Repository ARN"
  value       = aws_ecr_repository.deployment_worker.arn
}

output "ecr_repository_name" {
  description = "ECR Repository name"
  value       = aws_ecr_repository.deployment_worker.name
}
