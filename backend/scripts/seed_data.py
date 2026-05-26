#!/usr/bin/env python3
"""StackVertex Backend - Database Seed Script.

Befüllt die Datenbank mit realistischen AWS-Beispiel-Architekturen.
Diese Architekturen sind vollständig schema-konform und demonstrieren
verschiedene Use Cases.

Usage:
    poetry run python scripts/seed_data.py           # Fügt Beispiele hinzu
    poetry run python scripts/seed_data.py --reset   # Löscht alles und fügt neu hinzu
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime, timezone
import uuid

# Python-Path anpassen, um Backend-Module zu importieren
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy.orm import Session
from app.models.database import SessionLocal, engine, Base
from app.models.architecture import Architecture
from app.crud.architecture import create_architecture, get_architectures
from app.schemas.architecture import ArchitectureCreate


# ============================================================================
# EXAMPLE 1: Simple Web Application
# ============================================================================

def create_web_app_architecture() -> dict:
    """Erstellt eine klassische Web-App-Architektur mit HA."""
    arch_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    return {
        "version": "1.0.0",
        "metadata": {
            "id": arch_id,
            "name": "Simple Web Application",
            "description": "Klassische Web-Anwendung mit Loadbalancer, Auto Scaling, RDS-Datenbank und CloudFront CDN. Geeignet für mittelgroße Web-Apps mit 1000-5000 gleichzeitigen Nutzern.",
            "provider": "aws",
            "region": "eu-central-1",
            "created_at": now,
            "updated_at": now,
            "created_by": "system",
            "tags": ["production", "web-app", "high-availability"]
        },
        "requirements": {
            "functional": {
                "workload_type": "web_application",
                "expected_traffic": {
                    "concurrent_users": 2000,
                    "requests_per_second": 500,
                    "data_transfer_gb_month": 500
                },
                "storage_needs": {
                    "database_size_gb": 50,
                    "file_storage_gb": 100,
                    "requires_object_storage": True
                },
                "compute_needs": {
                    "cpu_intensive": False,
                    "memory_intensive": False,
                    "gpu_required": False
                }
            },
            "non_functional": {
                "availability": {
                    "target_uptime_percent": 99.9,
                    "multi_az": True,
                    "disaster_recovery": True
                },
                "scalability": {
                    "auto_scaling": True,
                    "scale_to_zero": False,
                    "global_distribution": False
                },
                "security": {
                    "compliance_requirements": ["GDPR"],
                    "data_encryption": {
                        "at_rest": True,
                        "in_transit": True
                    },
                    "network_isolation": True,
                    "public_access": True
                },
                "performance": {
                    "max_latency_ms": 200,
                    "cdn_required": True
                },
                "cost": {
                    "monthly_budget_usd": 500,
                    "cost_optimization_priority": "medium"
                }
            }
        },
        "decisions": {
            "network": {
                "vpc_required": True,
                "subnet_strategy": "public_private",
                "reasoning": "Private Subnets für EC2 und RDS sorgen für bessere Sicherheit. Public Subnets nur für ALB."
            },
            "compute": {
                "service_type": "vm",
                "instance_size": "t3.medium",
                "reasoning": "EC2 mit Auto Scaling bietet gute Balance zwischen Flexibilität und Kosten. T3 instances sind cost-effective für Web-Workloads mit variabler Last."
            },
            "database": {
                "database_type": "relational",
                "managed_service": True,
                "reasoning": "RDS MySQL Multi-AZ für hohe Verfügbarkeit und automatische Backups. Managed Service reduziert Wartungsaufwand."
            },
            "storage": {
                "object_storage": True,
                "block_storage": True,
                "reasoning": "S3 für statische Assets (Bilder, CSS, JS) mit CloudFront CDN. EBS für EC2 instance storage."
            }
        },
        "architecture": {
            "components": [
                {
                    "id": "vpc-main",
                    "type": "network",
                    "name": "Main VPC",
                    "provider_service": "vpc",
                    "configuration": {
                        "cidr_block": "10.0.0.0/16",
                        "enable_dns_hostnames": True,
                        "enable_dns_support": True
                    },
                    "tags": {"Environment": "production", "ManagedBy": "StackVertex"}
                },
                {
                    "id": "subnet-public-1a",
                    "type": "network",
                    "name": "Public Subnet 1a",
                    "provider_service": "subnet",
                    "configuration": {
                        "cidr_block": "10.0.1.0/24",
                        "availability_zone": "eu-central-1a",
                        "map_public_ip_on_launch": True
                    }
                },
                {
                    "id": "subnet-public-1b",
                    "type": "network",
                    "name": "Public Subnet 1b",
                    "provider_service": "subnet",
                    "configuration": {
                        "cidr_block": "10.0.2.0/24",
                        "availability_zone": "eu-central-1b",
                        "map_public_ip_on_launch": True
                    }
                },
                {
                    "id": "subnet-private-1a",
                    "type": "network",
                    "name": "Private Subnet 1a",
                    "provider_service": "subnet",
                    "configuration": {
                        "cidr_block": "10.0.11.0/24",
                        "availability_zone": "eu-central-1a"
                    }
                },
                {
                    "id": "subnet-private-1b",
                    "type": "network",
                    "name": "Private Subnet 1b",
                    "provider_service": "subnet",
                    "configuration": {
                        "cidr_block": "10.0.12.0/24",
                        "availability_zone": "eu-central-1b"
                    }
                },
                {
                    "id": "alb-web",
                    "type": "load_balancer",
                    "name": "Web Application Load Balancer",
                    "provider_service": "alb",
                    "configuration": {
                        "load_balancer_type": "application",
                        "scheme": "internet-facing",
                        "ip_address_type": "ipv4",
                        "enable_deletion_protection": False,
                        "enable_http2": True
                    }
                },
                {
                    "id": "asg-web",
                    "type": "compute",
                    "name": "Web Server Auto Scaling Group",
                    "provider_service": "autoscaling_group",
                    "configuration": {
                        "min_size": 2,
                        "max_size": 10,
                        "desired_capacity": 2,
                        "health_check_type": "ELB",
                        "health_check_grace_period": 300
                    }
                },
                {
                    "id": "ec2-launch-template",
                    "type": "compute",
                    "name": "Web Server Launch Template",
                    "provider_service": "ec2",
                    "configuration": {
                        "instance_type": "t3.medium",
                        "ami": "ami-0c55b159cbfafe1f0",
                        "key_name": "web-app-key"
                    },
                    "artifacts": [
                        {
                            "type": "script",
                            "source": {
                                "type": "upload",
                                "platform_storage": "artifacts/web-app/bootstrap.sh"
                            },
                            "deployment_method": "user_data"
                        }
                    ]
                },
                {
                    "id": "rds-mysql",
                    "type": "database",
                    "name": "MySQL Database",
                    "provider_service": "rds",
                    "configuration": {
                        "engine": "mysql",
                        "engine_version": "8.0",
                        "instance_class": "db.t3.medium",
                        "allocated_storage": 100,
                        "storage_type": "gp3",
                        "multi_az": True,
                        "backup_retention_period": 7,
                        "storage_encrypted": True
                    }
                },
                {
                    "id": "s3-assets",
                    "type": "storage",
                    "name": "Static Assets Bucket",
                    "provider_service": "s3",
                    "configuration": {
                        "bucket_name": "web-app-static-assets",
                        "versioning": True,
                        "encryption": "AES256",
                        "public_access_block": False
                    }
                },
                {
                    "id": "cloudfront-cdn",
                    "type": "cdn",
                    "name": "CloudFront Distribution",
                    "provider_service": "cloudfront",
                    "configuration": {
                        "price_class": "PriceClass_100",
                        "enabled": True,
                        "default_root_object": "index.html",
                        "viewer_protocol_policy": "redirect-to-https"
                    }
                },
                {
                    "id": "sg-alb",
                    "type": "security_group",
                    "name": "ALB Security Group",
                    "provider_service": "security_group",
                    "configuration": {
                        "ingress": [
                            {"from_port": 80, "to_port": 80, "protocol": "tcp", "cidr_blocks": ["0.0.0.0/0"]},
                            {"from_port": 443, "to_port": 443, "protocol": "tcp", "cidr_blocks": ["0.0.0.0/0"]}
                        ]
                    }
                },
                {
                    "id": "sg-web",
                    "type": "security_group",
                    "name": "Web Server Security Group",
                    "provider_service": "security_group",
                    "configuration": {
                        "ingress": [
                            {"from_port": 80, "to_port": 80, "protocol": "tcp", "source_security_group": "sg-alb"}
                        ]
                    }
                },
                {
                    "id": "sg-rds",
                    "type": "security_group",
                    "name": "RDS Security Group",
                    "provider_service": "security_group",
                    "configuration": {
                        "ingress": [
                            {"from_port": 3306, "to_port": 3306, "protocol": "tcp", "source_security_group": "sg-web"}
                        ]
                    }
                }
            ],
            "relationships": [
                {"from": "subnet-public-1a", "to": "vpc-main", "type": "network"},
                {"from": "subnet-public-1b", "to": "vpc-main", "type": "network"},
                {"from": "subnet-private-1a", "to": "vpc-main", "type": "network"},
                {"from": "subnet-private-1b", "to": "vpc-main", "type": "network"},
                {"from": "alb-web", "to": "subnet-public-1a", "type": "network"},
                {"from": "alb-web", "to": "subnet-public-1b", "type": "network"},
                {"from": "alb-web", "to": "asg-web", "type": "accesses", "configuration": {"port": 80}},
                {"from": "asg-web", "to": "subnet-private-1a", "type": "network"},
                {"from": "asg-web", "to": "subnet-private-1b", "type": "network"},
                {"from": "asg-web", "to": "ec2-launch-template", "type": "depends_on"},
                {"from": "asg-web", "to": "rds-mysql", "type": "accesses", "configuration": {"port": 3306}},
                {"from": "rds-mysql", "to": "subnet-private-1a", "type": "network"},
                {"from": "rds-mysql", "to": "subnet-private-1b", "type": "network"},
                {"from": "cloudfront-cdn", "to": "s3-assets", "type": "accesses"},
                {"from": "cloudfront-cdn", "to": "alb-web", "type": "accesses"},
                {"from": "sg-alb", "to": "alb-web", "type": "depends_on"},
                {"from": "sg-web", "to": "asg-web", "type": "depends_on"},
                {"from": "sg-rds", "to": "rds-mysql", "type": "depends_on"}
            ]
        },
        "evaluation": {
            "cost": {
                "estimated_monthly_usd": 385.0,
                "breakdown": [
                    {"component_id": "alb-web", "component_name": "ALB", "cost_usd": 22.0, "billing_model": "hourly"},
                    {"component_id": "asg-web", "component_name": "EC2 Instances", "cost_usd": 120.0, "billing_model": "hourly"},
                    {"component_id": "rds-mysql", "component_name": "RDS MySQL", "cost_usd": 180.0, "billing_model": "hourly"},
                    {"component_id": "s3-assets", "component_name": "S3", "cost_usd": 15.0, "billing_model": "per_gb"},
                    {"component_id": "cloudfront-cdn", "component_name": "CloudFront", "cost_usd": 48.0, "billing_model": "per_gb"}
                ],
                "confidence": "high",
                "warnings": ["Kosten können bei starkem Traffic durch CloudFront steigen"]
            },
            "security": {
                "score": 85,
                "issues": [
                    {
                        "severity": "medium",
                        "component_id": "alb-web",
                        "message": "ALB erlaubt HTTP-Traffic",
                        "recommendation": "Aktiviere HTTPS-only mit SSL-Zertifikat (AWS Certificate Manager)"
                    },
                    {
                        "severity": "low",
                        "component_id": "s3-assets",
                        "message": "S3 Bucket hat public access für CloudFront",
                        "recommendation": "Verwende Origin Access Identity (OAI) für sicheren CloudFront-Zugriff"
                    }
                ]
            },
            "scalability": {
                "score": 90,
                "auto_scaling_enabled": True,
                "bottlenecks": [
                    {
                        "component_id": "rds-mysql",
                        "issue": "RDS kann nicht horizontal skalieren",
                        "recommendation": "Bei sehr hohem Traffic: Read Replicas hinzufügen oder auf Aurora umsteigen"
                    }
                ]
            },
            "availability": {
                "score": 95,
                "estimated_uptime_percent": 99.95,
                "single_points_of_failure": []
            },
            "complexity": {
                "score": 35,
                "component_count": 14,
                "recommendations": [
                    "Gute Balance zwischen Funktionalität und Komplexität",
                    "Standard-Pattern für Web-Apps - gut wartbar"
                ]
            },
            "alternatives": [
                {
                    "title": "Serverless mit Lambda + API Gateway",
                    "description": "Komplette Umstellung auf Serverless mit Lambda Functions, API Gateway und Aurora Serverless",
                    "trade_offs": {
                        "cost_change_percent": -40,
                        "complexity_change": "more_complex",
                        "pros": [
                            "Deutlich günstiger bei unregelmäßiger Last",
                            "Automatisches Scaling auf 0",
                            "Kein Server-Management"
                        ],
                        "cons": [
                            "Cold Starts können Latenz erhöhen",
                            "Komplexere Entwicklung und Debugging",
                            "Vendor Lock-in"
                        ]
                    }
                }
            ]
        }
    }


# ============================================================================
# EXAMPLE 2: Serverless API
# ============================================================================

def create_serverless_api_architecture() -> dict:
    """Erstellt eine vollständig serverless API-Architektur."""
    arch_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    return {
        "version": "1.0.0",
        "metadata": {
            "id": arch_id,
            "name": "Serverless REST API",
            "description": "Vollständig serverless REST API mit API Gateway, Lambda Functions und DynamoDB. Ideal für APIs mit unvorhersehbarer oder stark variierender Last. Scale-to-zero für minimale Kosten.",
            "provider": "aws",
            "region": "us-east-1",
            "created_at": now,
            "updated_at": now,
            "created_by": "system",
            "tags": ["serverless", "api", "cost-optimized", "microservices"]
        },
        "requirements": {
            "functional": {
                "workload_type": "api_service",
                "expected_traffic": {
                    "concurrent_users": 500,
                    "requests_per_second": 100,
                    "data_transfer_gb_month": 50
                },
                "storage_needs": {
                    "database_size_gb": 10,
                    "file_storage_gb": 5,
                    "requires_object_storage": False
                },
                "compute_needs": {
                    "cpu_intensive": False,
                    "memory_intensive": False,
                    "gpu_required": False
                }
            },
            "non_functional": {
                "availability": {
                    "target_uptime_percent": 99.5,
                    "multi_az": True,
                    "disaster_recovery": False
                },
                "scalability": {
                    "auto_scaling": True,
                    "scale_to_zero": True,
                    "global_distribution": False
                },
                "security": {
                    "compliance_requirements": [],
                    "data_encryption": {
                        "at_rest": True,
                        "in_transit": True
                    },
                    "network_isolation": False,
                    "public_access": True
                },
                "performance": {
                    "max_latency_ms": 500,
                    "cdn_required": False
                },
                "cost": {
                    "monthly_budget_usd": 100,
                    "cost_optimization_priority": "high"
                }
            }
        },
        "decisions": {
            "network": {
                "vpc_required": False,
                "subnet_strategy": "single_public",
                "reasoning": "Lambda Functions benötigen keine VPC für DynamoDB-Zugriff. Reduziert Komplexität und Cold Start Zeit."
            },
            "compute": {
                "service_type": "serverless",
                "instance_size": "128MB-512MB RAM",
                "reasoning": "Lambda Functions bieten perfektes Scale-to-Zero und Pay-per-Use. Ideal für APIs mit variabler Last."
            },
            "database": {
                "database_type": "nosql",
                "managed_service": True,
                "reasoning": "DynamoDB ist serverless, skaliert automatisch und integriert perfekt mit Lambda. On-Demand Pricing für unvorhersehbare Workloads."
            },
            "storage": {
                "object_storage": False,
                "block_storage": False,
                "reasoning": "DynamoDB reicht für API-Daten. Keine zusätzliche Storage-Layer notwendig."
            }
        },
        "architecture": {
            "components": [
                {
                    "id": "api-gateway",
                    "type": "load_balancer",
                    "name": "REST API Gateway",
                    "provider_service": "api_gateway",
                    "configuration": {
                        "api_type": "REST",
                        "endpoint_type": "REGIONAL",
                        "stage_name": "prod",
                        "throttle_burst_limit": 5000,
                        "throttle_rate_limit": 2000
                    }
                },
                {
                    "id": "lambda-get-items",
                    "type": "function",
                    "name": "Get Items Function",
                    "provider_service": "lambda",
                    "configuration": {
                        "runtime": "python3.11",
                        "memory_size": 256,
                        "timeout": 30,
                        "environment_variables": {
                            "TABLE_NAME": "items",
                            "LOG_LEVEL": "INFO"
                        }
                    },
                    "artifacts": [
                        {
                            "type": "zip",
                            "source": {
                                "type": "upload",
                                "platform_storage": "artifacts/api/get_items.zip"
                            },
                            "deployment_method": "function_code"
                        }
                    ]
                },
                {
                    "id": "lambda-create-item",
                    "type": "function",
                    "name": "Create Item Function",
                    "provider_service": "lambda",
                    "configuration": {
                        "runtime": "python3.11",
                        "memory_size": 256,
                        "timeout": 30,
                        "environment_variables": {
                            "TABLE_NAME": "items",
                            "LOG_LEVEL": "INFO"
                        }
                    },
                    "artifacts": [
                        {
                            "type": "zip",
                            "source": {
                                "type": "upload",
                                "platform_storage": "artifacts/api/create_item.zip"
                            },
                            "deployment_method": "function_code"
                        }
                    ]
                },
                {
                    "id": "lambda-delete-item",
                    "type": "function",
                    "name": "Delete Item Function",
                    "provider_service": "lambda",
                    "configuration": {
                        "runtime": "python3.11",
                        "memory_size": 128,
                        "timeout": 15,
                        "environment_variables": {
                            "TABLE_NAME": "items",
                            "LOG_LEVEL": "INFO"
                        }
                    },
                    "artifacts": [
                        {
                            "type": "zip",
                            "source": {
                                "type": "upload",
                                "platform_storage": "artifacts/api/delete_item.zip"
                            },
                            "deployment_method": "function_code"
                        }
                    ]
                },
                {
                    "id": "dynamodb-items",
                    "type": "database",
                    "name": "Items Table",
                    "provider_service": "dynamodb",
                    "configuration": {
                        "billing_mode": "PAY_PER_REQUEST",
                        "hash_key": "id",
                        "attributes": [
                            {"name": "id", "type": "S"},
                            {"name": "created_at", "type": "N"}
                        ],
                        "global_secondary_indexes": [
                            {
                                "name": "created_at-index",
                                "hash_key": "created_at",
                                "projection_type": "ALL"
                            }
                        ],
                        "point_in_time_recovery": True,
                        "server_side_encryption": True
                    }
                },
                {
                    "id": "iam-lambda-role",
                    "type": "iam_role",
                    "name": "Lambda Execution Role",
                    "provider_service": "iam",
                    "configuration": {
                        "assume_role_policy": "lambda.amazonaws.com",
                        "managed_policies": [
                            "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
                        ],
                        "inline_policies": [
                            {
                                "name": "DynamoDBAccess",
                                "actions": [
                                    "dynamodb:GetItem",
                                    "dynamodb:PutItem",
                                    "dynamodb:DeleteItem",
                                    "dynamodb:Query",
                                    "dynamodb:Scan"
                                ],
                                "resources": ["dynamodb-items"]
                            }
                        ]
                    }
                },
                {
                    "id": "cloudwatch-logs",
                    "type": "cache",
                    "name": "CloudWatch Logs",
                    "provider_service": "cloudwatch_logs",
                    "configuration": {
                        "log_group_name": "/aws/lambda/api",
                        "retention_days": 7
                    }
                },
                {
                    "id": "cloudwatch-alarms",
                    "type": "cache",
                    "name": "CloudWatch Alarms",
                    "provider_service": "cloudwatch",
                    "configuration": {
                        "alarms": [
                            {
                                "name": "HighErrorRate",
                                "metric": "Errors",
                                "threshold": 10,
                                "evaluation_periods": 2
                            },
                            {
                                "name": "HighLatency",
                                "metric": "Duration",
                                "threshold": 5000,
                                "evaluation_periods": 3
                            }
                        ]
                    }
                }
            ],
            "relationships": [
                {"from": "api-gateway", "to": "lambda-get-items", "type": "triggers", "configuration": {"method": "GET", "path": "/items"}},
                {"from": "api-gateway", "to": "lambda-create-item", "type": "triggers", "configuration": {"method": "POST", "path": "/items"}},
                {"from": "api-gateway", "to": "lambda-delete-item", "type": "triggers", "configuration": {"method": "DELETE", "path": "/items/{id}"}},
                {"from": "lambda-get-items", "to": "dynamodb-items", "type": "accesses"},
                {"from": "lambda-create-item", "to": "dynamodb-items", "type": "accesses"},
                {"from": "lambda-delete-item", "to": "dynamodb-items", "type": "accesses"},
                {"from": "lambda-get-items", "to": "iam-lambda-role", "type": "depends_on"},
                {"from": "lambda-create-item", "to": "iam-lambda-role", "type": "depends_on"},
                {"from": "lambda-delete-item", "to": "iam-lambda-role", "type": "depends_on"},
                {"from": "lambda-get-items", "to": "cloudwatch-logs", "type": "accesses"},
                {"from": "lambda-create-item", "to": "cloudwatch-logs", "type": "accesses"},
                {"from": "lambda-delete-item", "to": "cloudwatch-logs", "type": "accesses"}
            ]
        },
        "evaluation": {
            "cost": {
                "estimated_monthly_usd": 15.5,
                "breakdown": [
                    {"component_id": "api-gateway", "component_name": "API Gateway", "cost_usd": 3.5, "billing_model": "per_request"},
                    {"component_id": "lambda-get-items", "component_name": "Lambda GET", "cost_usd": 4.0, "billing_model": "per_request"},
                    {"component_id": "lambda-create-item", "component_name": "Lambda POST", "cost_usd": 3.0, "billing_model": "per_request"},
                    {"component_id": "lambda-delete-item", "component_name": "Lambda DELETE", "cost_usd": 1.0, "billing_model": "per_request"},
                    {"component_id": "dynamodb-items", "component_name": "DynamoDB", "cost_usd": 3.0, "billing_model": "per_request"},
                    {"component_id": "cloudwatch-logs", "component_name": "CloudWatch", "cost_usd": 1.0, "billing_model": "per_gb"}
                ],
                "confidence": "high",
                "warnings": [
                    "Kosten sind stark usage-abhängig",
                    "Bei 0 Requests = fast 0 Kosten (nur DynamoDB Table minimum)"
                ]
            },
            "security": {
                "score": 75,
                "issues": [
                    {
                        "severity": "high",
                        "component_id": "api-gateway",
                        "message": "API Gateway hat keine Authentifizierung konfiguriert",
                        "recommendation": "Implementiere API Keys, Cognito User Pools oder IAM Authentication"
                    },
                    {
                        "severity": "medium",
                        "component_id": "api-gateway",
                        "message": "Kein Rate Limiting pro Client",
                        "recommendation": "Konfiguriere Usage Plans mit API Keys für Rate Limiting"
                    },
                    {
                        "severity": "low",
                        "component_id": "dynamodb-items",
                        "message": "Keine VPC-Endpoints für DynamoDB",
                        "recommendation": "Für sensible Daten: Lambda in VPC mit DynamoDB VPC Endpoint"
                    }
                ]
            },
            "scalability": {
                "score": 100,
                "auto_scaling_enabled": True,
                "bottlenecks": []
            },
            "availability": {
                "score": 90,
                "estimated_uptime_percent": 99.9,
                "single_points_of_failure": []
            },
            "complexity": {
                "score": 20,
                "component_count": 8,
                "recommendations": [
                    "Sehr einfache Architektur - perfekt für kleine bis mittlere APIs",
                    "Kein Server-Management notwendig",
                    "Gut für MVPs und Prototypen"
                ]
            },
            "alternatives": [
                {
                    "title": "ECS Fargate mit Application Load Balancer",
                    "description": "Container-basierte API mit ECS Fargate, ALB und Aurora Serverless",
                    "trade_offs": {
                        "cost_change_percent": 120,
                        "complexity_change": "more_complex",
                        "pros": [
                            "Keine Cold Starts",
                            "Bessere Performance für konstanten Traffic",
                            "Mehr Kontrolle über Runtime-Umgebung",
                            "Einfacheres lokales Testing"
                        ],
                        "cons": [
                            "Deutlich höhere Kosten bei niedriger Last",
                            "Kein Scale-to-Zero",
                            "Mehr Infrastruktur-Management"
                        ]
                    }
                },
                {
                    "title": "AWS AppSync (GraphQL)",
                    "description": "Ersetze REST API durch GraphQL mit AppSync",
                    "trade_offs": {
                        "cost_change_percent": 5,
                        "complexity_change": "same",
                        "pros": [
                            "Flexiblere Queries für Clients",
                            "Real-time Subscriptions",
                            "Automatic schema generation",
                            "Bessere mobile app integration"
                        ],
                        "cons": [
                            "GraphQL-Lernkurve",
                            "Weniger REST-Tools verfügbar",
                            "Komplexere Caching-Strategien"
                        ]
                    }
                }
            ]
        }
    }


# ============================================================================
# EXAMPLE 3: Data Analytics Pipeline
# ============================================================================

def create_data_pipeline_architecture() -> dict:
    """Erstellt eine Daten-Pipeline für Analytics."""
    arch_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    return {
        "version": "1.0.0",
        "metadata": {
            "id": arch_id,
            "name": "Data Analytics Pipeline",
            "description": "ETL-Pipeline für Batch-Processing von großen Datenmengen. S3 für Storage, Lambda für Event-Triggering, Glue für ETL-Jobs und Athena für SQL-Queries. Ideal für Data Warehousing und Business Intelligence.",
            "provider": "aws",
            "region": "us-west-2",
            "created_at": now,
            "updated_at": now,
            "created_by": "system",
            "tags": ["analytics", "etl", "data-pipeline", "batch-processing"]
        },
        "requirements": {
            "functional": {
                "workload_type": "data_processing",
                "expected_traffic": {
                    "concurrent_users": 50,
                    "requests_per_second": 5,
                    "data_transfer_gb_month": 2000
                },
                "storage_needs": {
                    "database_size_gb": 0,
                    "file_storage_gb": 5000,
                    "requires_object_storage": True
                },
                "compute_needs": {
                    "cpu_intensive": True,
                    "memory_intensive": True,
                    "gpu_required": False
                }
            },
            "non_functional": {
                "availability": {
                    "target_uptime_percent": 99.0,
                    "multi_az": False,
                    "disaster_recovery": True
                },
                "scalability": {
                    "auto_scaling": True,
                    "scale_to_zero": True,
                    "global_distribution": False
                },
                "security": {
                    "compliance_requirements": ["SOC2"],
                    "data_encryption": {
                        "at_rest": True,
                        "in_transit": True
                    },
                    "network_isolation": True,
                    "public_access": False
                },
                "performance": {
                    "max_latency_ms": 60000,
                    "cdn_required": False
                },
                "cost": {
                    "monthly_budget_usd": 800,
                    "cost_optimization_priority": "high"
                }
            }
        },
        "decisions": {
            "network": {
                "vpc_required": True,
                "subnet_strategy": "public_private",
                "reasoning": "Glue Jobs laufen in VPC für sicheren Zugriff auf Datenquellen. S3 VPC Endpoints für cost-effective und sichere S3-Kommunikation."
            },
            "compute": {
                "service_type": "managed",
                "instance_size": "DPU-based (Glue)",
                "reasoning": "AWS Glue ist vollständig managed ETL Service. Keine Server-Verwaltung, automatisches Scaling, Spark-basiert für große Datenmengen."
            },
            "database": {
                "database_type": "none",
                "managed_service": False,
                "reasoning": "Athena ersetzt klassische Datenbank - SQL-Queries direkt auf S3-Daten. Cost-effective für Ad-hoc Analytics."
            },
            "storage": {
                "object_storage": True,
                "block_storage": False,
                "reasoning": "S3 als Data Lake - unbegrenzt skalierbar, verschiedene Storage Tiers für Cost Optimization. Lifecycle Policies für automatisches Archivieren."
            }
        },
        "architecture": {
            "components": [
                {
                    "id": "vpc-data",
                    "type": "network",
                    "name": "Data Processing VPC",
                    "provider_service": "vpc",
                    "configuration": {
                        "cidr_block": "10.1.0.0/16",
                        "enable_dns_hostnames": True,
                        "enable_dns_support": True
                    }
                },
                {
                    "id": "s3-raw-data",
                    "type": "storage",
                    "name": "Raw Data Lake",
                    "provider_service": "s3",
                    "configuration": {
                        "bucket_name": "data-pipeline-raw",
                        "versioning": True,
                        "encryption": "aws:kms",
                        "lifecycle_rules": [
                            {
                                "name": "archive-old-data",
                                "transition_days": 90,
                                "storage_class": "GLACIER"
                            },
                            {
                                "name": "delete-very-old",
                                "expiration_days": 730
                            }
                        ],
                        "intelligent_tiering": True
                    }
                },
                {
                    "id": "s3-processed-data",
                    "type": "storage",
                    "name": "Processed Data Bucket",
                    "provider_service": "s3",
                    "configuration": {
                        "bucket_name": "data-pipeline-processed",
                        "versioning": False,
                        "encryption": "aws:kms",
                        "partition_strategy": "year/month/day"
                    }
                },
                {
                    "id": "s3-results",
                    "type": "storage",
                    "name": "Query Results Bucket",
                    "provider_service": "s3",
                    "configuration": {
                        "bucket_name": "data-pipeline-results",
                        "versioning": False,
                        "encryption": "AES256",
                        "lifecycle_rules": [
                            {
                                "name": "delete-old-results",
                                "expiration_days": 30
                            }
                        ]
                    }
                },
                {
                    "id": "lambda-trigger",
                    "type": "function",
                    "name": "S3 Event Trigger Function",
                    "provider_service": "lambda",
                    "configuration": {
                        "runtime": "python3.11",
                        "memory_size": 512,
                        "timeout": 60,
                        "environment_variables": {
                            "GLUE_JOB_NAME": "data-etl-job",
                            "LOG_LEVEL": "INFO"
                        }
                    },
                    "artifacts": [
                        {
                            "type": "zip",
                            "source": {
                                "type": "upload",
                                "platform_storage": "artifacts/pipeline/trigger.zip"
                            },
                            "deployment_method": "function_code"
                        }
                    ]
                },
                {
                    "id": "glue-crawler",
                    "type": "function",
                    "name": "Data Catalog Crawler",
                    "provider_service": "glue_crawler",
                    "configuration": {
                        "database_name": "analytics_db",
                        "s3_targets": ["s3-processed-data"],
                        "schedule": "cron(0 2 * * ? *)",
                        "schema_change_policy": "UPDATE_IN_DATABASE"
                    }
                },
                {
                    "id": "glue-job",
                    "type": "function",
                    "name": "ETL Job",
                    "provider_service": "glue_job",
                    "configuration": {
                        "glue_version": "4.0",
                        "worker_type": "G.1X",
                        "number_of_workers": 10,
                        "max_concurrent_runs": 5,
                        "timeout_minutes": 2880,
                        "max_retries": 1
                    },
                    "artifacts": [
                        {
                            "type": "script",
                            "source": {
                                "type": "upload",
                                "platform_storage": "artifacts/pipeline/etl_script.py"
                            },
                            "deployment_method": "function_code"
                        }
                    ]
                },
                {
                    "id": "athena-workgroup",
                    "type": "database",
                    "name": "Analytics Workgroup",
                    "provider_service": "athena",
                    "configuration": {
                        "workgroup_name": "analytics",
                        "output_location": "s3-results",
                        "enforce_workgroup_configuration": True,
                        "bytes_scanned_cutoff_per_query": 10000000000,
                        "encryption_enabled": True
                    }
                },
                {
                    "id": "glue-catalog",
                    "type": "database",
                    "name": "Data Catalog Database",
                    "provider_service": "glue_database",
                    "configuration": {
                        "database_name": "analytics_db",
                        "description": "Metadata catalog for processed data"
                    }
                },
                {
                    "id": "eventbridge-rule",
                    "type": "queue",
                    "name": "Daily Processing Schedule",
                    "provider_service": "eventbridge",
                    "configuration": {
                        "schedule_expression": "cron(0 1 * * ? *)",
                        "description": "Trigger daily ETL job at 1 AM UTC"
                    }
                },
                {
                    "id": "sns-alerts",
                    "type": "queue",
                    "name": "Pipeline Alerts",
                    "provider_service": "sns",
                    "configuration": {
                        "topic_name": "data-pipeline-alerts",
                        "email_subscriptions": ["data-team@company.com"]
                    }
                },
                {
                    "id": "iam-glue-role",
                    "type": "iam_role",
                    "name": "Glue Service Role",
                    "provider_service": "iam",
                    "configuration": {
                        "assume_role_policy": "glue.amazonaws.com",
                        "managed_policies": [
                            "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
                        ],
                        "inline_policies": [
                            {
                                "name": "S3Access",
                                "actions": [
                                    "s3:GetObject",
                                    "s3:PutObject",
                                    "s3:DeleteObject"
                                ],
                                "resources": ["s3-raw-data", "s3-processed-data"]
                            }
                        ]
                    }
                },
                {
                    "id": "cloudwatch-dashboard",
                    "type": "cache",
                    "name": "Pipeline Monitoring Dashboard",
                    "provider_service": "cloudwatch",
                    "configuration": {
                        "dashboard_name": "DataPipeline",
                        "widgets": [
                            "Glue Job Success Rate",
                            "Lambda Invocations",
                            "S3 Bucket Size",
                            "Athena Query Performance"
                        ]
                    }
                }
            ],
            "relationships": [
                {"from": "s3-raw-data", "to": "lambda-trigger", "type": "triggers", "configuration": {"event": "s3:ObjectCreated:*"}},
                {"from": "lambda-trigger", "to": "glue-job", "type": "triggers"},
                {"from": "glue-job", "to": "s3-raw-data", "type": "accesses"},
                {"from": "glue-job", "to": "s3-processed-data", "type": "accesses"},
                {"from": "glue-job", "to": "iam-glue-role", "type": "depends_on"},
                {"from": "glue-crawler", "to": "s3-processed-data", "type": "accesses"},
                {"from": "glue-crawler", "to": "glue-catalog", "type": "accesses"},
                {"from": "athena-workgroup", "to": "s3-processed-data", "type": "accesses"},
                {"from": "athena-workgroup", "to": "s3-results", "type": "accesses"},
                {"from": "athena-workgroup", "to": "glue-catalog", "type": "depends_on"},
                {"from": "eventbridge-rule", "to": "glue-crawler", "type": "triggers"},
                {"from": "glue-job", "to": "sns-alerts", "type": "accesses"},
                {"from": "glue-job", "to": "vpc-data", "type": "network"}
            ]
        },
        "evaluation": {
            "cost": {
                "estimated_monthly_usd": 485.0,
                "breakdown": [
                    {"component_id": "s3-raw-data", "component_name": "S3 Raw Data", "cost_usd": 115.0, "billing_model": "per_gb"},
                    {"component_id": "s3-processed-data", "component_name": "S3 Processed", "cost_usd": 75.0, "billing_model": "per_gb"},
                    {"component_id": "s3-results", "component_name": "S3 Results", "cost_usd": 5.0, "billing_model": "per_gb"},
                    {"component_id": "glue-job", "component_name": "Glue ETL Jobs", "cost_usd": 240.0, "billing_model": "hourly"},
                    {"component_id": "glue-crawler", "component_name": "Glue Crawler", "cost_usd": 15.0, "billing_model": "hourly"},
                    {"component_id": "athena-workgroup", "component_name": "Athena Queries", "cost_usd": 30.0, "billing_model": "per_gb"},
                    {"component_id": "lambda-trigger", "component_name": "Lambda", "cost_usd": 2.0, "billing_model": "per_request"},
                    {"component_id": "vpc-data", "component_name": "VPC Endpoints", "cost_usd": 3.0, "billing_model": "hourly"}
                ],
                "confidence": "medium",
                "warnings": [
                    "Glue Job Kosten hängen stark von Datenvolumen und Worker-Anzahl ab",
                    "S3 Intelligent Tiering kann Kosten um 30-50% reduzieren",
                    "Athena-Kosten variieren je nach gescannter Datenmenge - Partitionierung empfohlen"
                ]
            },
            "security": {
                "score": 90,
                "issues": [
                    {
                        "severity": "low",
                        "component_id": "s3-raw-data",
                        "message": "S3 Bucket Logging nicht aktiviert",
                        "recommendation": "Aktiviere S3 Server Access Logging für Audit-Trail"
                    },
                    {
                        "severity": "info",
                        "component_id": "athena-workgroup",
                        "message": "Athena Workgroup Query Result Encryption aktiv",
                        "recommendation": "Best Practice - bereits implementiert"
                    }
                ]
            },
            "scalability": {
                "score": 95,
                "auto_scaling_enabled": True,
                "bottlenecks": [
                    {
                        "component_id": "glue-job",
                        "issue": "Maximale Anzahl concurrent runs auf 5 limitiert",
                        "recommendation": "Bei Bedarf Service Quota Erhöhung beantragen (Standard: 30)"
                    }
                ]
            },
            "availability": {
                "score": 85,
                "estimated_uptime_percent": 99.5,
                "single_points_of_failure": [
                    "Glue Job Failure kann Pipeline blockieren - SNS Alerts konfiguriert für schnelle Reaktion"
                ]
            },
            "complexity": {
                "score": 55,
                "component_count": 13,
                "recommendations": [
                    "Mittlere Komplexität - typisch für Data Pipelines",
                    "Managed Services reduzieren operativen Aufwand erheblich",
                    "Monitoring und Alerting sind essentiell für Production"
                ]
            },
            "alternatives": [
                {
                    "title": "Amazon EMR (Elastic MapReduce)",
                    "description": "Ersetze Glue durch EMR Cluster für mehr Kontrolle und Spark-Features",
                    "trade_offs": {
                        "cost_change_percent": -15,
                        "complexity_change": "more_complex",
                        "pros": [
                            "Mehr Kontrolle über Spark-Konfiguration",
                            "Unterstützung für mehr Frameworks (Presto, Hive, etc.)",
                            "Günstiger bei sehr großen, konstanten Workloads",
                            "Spot Instances für weitere Kosteneinsparungen"
                        ],
                        "cons": [
                            "Mehr Management-Overhead",
                            "Cluster-Sizing und Tuning notwendig",
                            "Längere Cold Start Zeiten",
                            "Keine Serverless-Option"
                        ]
                    }
                },
                {
                    "title": "AWS Data Pipeline + Redshift",
                    "description": "Traditionelle Data Warehouse Lösung mit Redshift statt Athena",
                    "trade_offs": {
                        "cost_change_percent": 85,
                        "complexity_change": "more_complex",
                        "pros": [
                            "Bessere Performance für komplexe Joins",
                            "Ideal für Business Intelligence Dashboards",
                            "Konsistentere Query-Performance",
                            "Mehr SQL-Features"
                        ],
                        "cons": [
                            "Deutlich höhere Kosten (Cluster läuft 24/7)",
                            "Mehr Wartungsaufwand",
                            "Weniger flexibel für Ad-hoc Analytics",
                            "Data Loading Prozess komplexer"
                        ]
                    }
                }
            ]
        }
    }


# ============================================================================
# MAIN SCRIPT
# ============================================================================

def reset_database():
    """Löscht alle bestehenden Architekturen aus der Datenbank."""
    print("🗑️  Lösche alle bestehenden Architekturen...")
    db = SessionLocal()
    try:
        count = db.query(Architecture).count()
        db.query(Architecture).delete()
        db.commit()
        print(f"✅ {count} Architekturen gelöscht")
    except Exception as e:
        db.rollback()
        print(f"❌ Fehler beim Löschen: {e}")
        raise
    finally:
        db.close()


def seed_architectures(reset: bool = False):
    """Befüllt die Datenbank mit Beispiel-Architekturen."""

    # Optional: Datenbank zurücksetzen
    if reset:
        reset_database()

    print("🌱 Starte Seed-Prozess...")
    print()

    # Beispiel-Architekturen generieren
    architectures = [
        create_web_app_architecture(),
        create_serverless_api_architecture(),
        create_data_pipeline_architecture(),
    ]

    db = SessionLocal()
    created_count = 0

    try:
        for arch_data in architectures:
            arch_name = arch_data["metadata"]["name"]

            # Prüfe ob Architektur bereits existiert (anhand des Namens)
            existing = db.query(Architecture).filter(
                Architecture.name == arch_name
            ).first()

            if existing and not reset:
                print(f"⏭️  Überspringe '{arch_name}' (existiert bereits)")
                continue

            # Erstelle Architecture Schema
            arch_create = ArchitectureCreate(
                name=arch_data["metadata"]["name"],
                description=arch_data["metadata"]["description"],
                version=arch_data["version"],
                architecture_json=arch_data,
                owner="system"
            )

            # In Datenbank speichern
            db_arch = create_architecture(db, arch_create)
            created_count += 1

            # Statistiken ausgeben
            component_count = len(arch_data["architecture"]["components"])
            relationship_count = len(arch_data["architecture"]["relationships"])
            estimated_cost = arch_data["evaluation"]["cost"]["estimated_monthly_usd"]

            print(f"✅ Erstellt: {arch_name}")
            print(f"   📦 Komponenten: {component_count}")
            print(f"   🔗 Beziehungen: {relationship_count}")
            print(f"   💰 Geschätzte Kosten: ${estimated_cost:.2f}/Monat")
            print(f"   🆔 ID: {db_arch.id}")
            print()

        print("=" * 60)
        print(f"✨ Seed-Prozess abgeschlossen!")
        print(f"📊 {created_count} Architekturen erstellt")

        # Gesamtanzahl in DB anzeigen
        total_count = db.query(Architecture).count()
        print(f"📁 Gesamt in Datenbank: {total_count} Architekturen")
        print()
        print("🚀 Du kannst die Architekturen jetzt über die API abrufen:")
        print("   GET http://localhost:8000/api/v1/architectures")

    except Exception as e:
        db.rollback()
        print(f"❌ Fehler beim Erstellen: {e}")
        raise
    finally:
        db.close()


def main():
    """Hauptfunktion mit CLI-Argument-Parsing."""
    parser = argparse.ArgumentParser(
        description="StackVertex Database Seed Script - Erstellt Beispiel-Architekturen"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Löscht alle bestehenden Architekturen vor dem Seeding"
    )

    args = parser.parse_args()

    print()
    print("=" * 60)
    print("🌥️  StackVertex Database Seeding")
    print("=" * 60)
    print()

    seed_architectures(reset=args.reset)


if __name__ == "__main__":
    main()
