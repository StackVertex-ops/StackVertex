/**
 * OverCloud - Example Architectures
 *
 * Vorgefertigte Beispiel-Architekturen für schnellen Einstieg
 */

/**
 * Generiere UUID v4
 */
function generateUUID() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

/**
 * Hole aktuelle ISO-Timestamp
 */
function getCurrentTimestamp() {
  return new Date().toISOString();
}

/**
 * Beispiel 1: Simple Web Application
 * VPC + EC2 + RDS + S3 + ALB
 */
export const EXAMPLE_SIMPLE_WEB_APP = {
  version: "1.0.0",
  metadata: {
    id: generateUUID(),
    name: "Simple Web Application",
    description: "Klassische 3-Tier Web-Anwendung mit Load Balancer, EC2-Instanzen, RDS-Datenbank und S3 für statische Assets",
    provider: "aws",
    region: "eu-central-1",
    created_at: getCurrentTimestamp(),
    updated_at: getCurrentTimestamp(),
    tags: ["web", "production", "example"]
  },
  requirements: {
    functional: {
      workload_type: "web_application",
      expected_traffic: {
        concurrent_users: 1000,
        requests_per_second: 50,
        data_transfer_gb_month: 100
      },
      storage_needs: {
        database_size_gb: 20,
        file_storage_gb: 50,
        requires_object_storage: true
      },
      compute_needs: {
        cpu_intensive: false,
        memory_intensive: false,
        gpu_required: false
      }
    },
    non_functional: {
      availability: {
        target_uptime_percent: 99.9,
        multi_az: true,
        disaster_recovery: false
      },
      scalability: {
        auto_scaling: true,
        scale_to_zero: false,
        global_distribution: false
      },
      security: {
        compliance_requirements: [],
        data_encryption: {
          at_rest: true,
          in_transit: true
        },
        network_isolation: true,
        public_access: true
      },
      performance: {
        max_latency_ms: 500,
        cdn_required: false
      },
      cost: {
        monthly_budget_usd: 500,
        cost_optimization_priority: "medium"
      }
    }
  },
  architecture: {
    components: [
      {
        id: "main-vpc",
        type: "network",
        name: "Main VPC",
        provider_service: "vpc",
        configuration: {
          cidr_block: "10.0.0.0/16",
          enable_dns_hostnames: true,
          enable_dns_support: true
        }
      },
      {
        id: "public-subnet-1",
        type: "network",
        name: "Public Subnet AZ1",
        provider_service: "subnet",
        configuration: {
          cidr_block: "10.0.1.0/24",
          availability_zone: "eu-central-1a",
          map_public_ip_on_launch: true
        }
      },
      {
        id: "public-subnet-2",
        type: "network",
        name: "Public Subnet AZ2",
        provider_service: "subnet",
        configuration: {
          cidr_block: "10.0.2.0/24",
          availability_zone: "eu-central-1b",
          map_public_ip_on_launch: true
        }
      },
      {
        id: "private-subnet-1",
        type: "network",
        name: "Private Subnet AZ1",
        provider_service: "subnet",
        configuration: {
          cidr_block: "10.0.11.0/24",
          availability_zone: "eu-central-1a",
          map_public_ip_on_launch: false
        }
      },
      {
        id: "private-subnet-2",
        type: "network",
        name: "Private Subnet AZ2",
        provider_service: "subnet",
        configuration: {
          cidr_block: "10.0.12.0/24",
          availability_zone: "eu-central-1b",
          map_public_ip_on_launch: false
        }
      },
      {
        id: "web-alb",
        type: "load_balancer",
        name: "Web Application Load Balancer",
        provider_service: "alb",
        configuration: {
          internal: false,
          load_balancer_type: "application",
          ip_address_type: "ipv4"
        }
      },
      {
        id: "web-server-1",
        type: "compute",
        name: "Web Server 1",
        provider_service: "ec2",
        configuration: {
          instance_type: "t3.medium",
          ami: "ami-0c55b159cbfafe1f0",
          key_name: "web-server-key"
        }
      },
      {
        id: "web-server-2",
        type: "compute",
        name: "Web Server 2",
        provider_service: "ec2",
        configuration: {
          instance_type: "t3.medium",
          ami: "ami-0c55b159cbfafe1f0",
          key_name: "web-server-key"
        }
      },
      {
        id: "main-rds",
        type: "database",
        name: "Main Database",
        provider_service: "rds",
        configuration: {
          engine: "postgres",
          engine_version: "15.3",
          instance_class: "db.t3.medium",
          allocated_storage: 20,
          multi_az: true,
          storage_encrypted: true
        }
      },
      {
        id: "static-assets-bucket",
        type: "storage",
        name: "Static Assets Bucket",
        provider_service: "s3",
        configuration: {
          versioning_enabled: true,
          encryption: "AES256",
          public_access_block: false
        }
      },
      {
        id: "web-sg",
        type: "security_group",
        name: "Web Server Security Group",
        provider_service: "security_group",
        configuration: {
          ingress: [
            { port: 80, protocol: "tcp", source: "0.0.0.0/0" },
            { port: 443, protocol: "tcp", source: "0.0.0.0/0" }
          ],
          egress: [
            { port: 0, protocol: "-1", destination: "0.0.0.0/0" }
          ]
        }
      },
      {
        id: "db-sg",
        type: "security_group",
        name: "Database Security Group",
        provider_service: "security_group",
        configuration: {
          ingress: [
            { port: 5432, protocol: "tcp", source: "web-sg" }
          ],
          egress: []
        }
      }
    ],
    relationships: [
      {
        from: "public-subnet-1",
        to: "main-vpc",
        type: "network"
      },
      {
        from: "public-subnet-2",
        to: "main-vpc",
        type: "network"
      },
      {
        from: "private-subnet-1",
        to: "main-vpc",
        type: "network"
      },
      {
        from: "private-subnet-2",
        to: "main-vpc",
        type: "network"
      },
      {
        from: "web-alb",
        to: "public-subnet-1",
        type: "network"
      },
      {
        from: "web-alb",
        to: "public-subnet-2",
        type: "network"
      },
      {
        from: "web-server-1",
        to: "public-subnet-1",
        type: "network"
      },
      {
        from: "web-server-2",
        to: "public-subnet-2",
        type: "network"
      },
      {
        from: "main-rds",
        to: "private-subnet-1",
        type: "network"
      },
      {
        from: "web-alb",
        to: "web-server-1",
        type: "accesses",
        configuration: { port: 80 }
      },
      {
        from: "web-alb",
        to: "web-server-2",
        type: "accesses",
        configuration: { port: 80 }
      },
      {
        from: "web-server-1",
        to: "main-rds",
        type: "accesses",
        configuration: { port: 5432 }
      },
      {
        from: "web-server-2",
        to: "main-rds",
        type: "accesses",
        configuration: { port: 5432 }
      },
      {
        from: "web-server-1",
        to: "static-assets-bucket",
        type: "accesses"
      },
      {
        from: "web-server-2",
        to: "static-assets-bucket",
        type: "accesses"
      }
    ]
  }
};

/**
 * Beispiel 2: Serverless API
 * API Gateway + Lambda + DynamoDB + S3
 */
export const EXAMPLE_SERVERLESS_API = {
  version: "1.0.0",
  metadata: {
    id: generateUUID(),
    name: "Serverless REST API",
    description: "Vollständig serverlose API mit API Gateway, Lambda-Funktionen, DynamoDB und S3 für File-Uploads",
    provider: "aws",
    region: "eu-central-1",
    created_at: getCurrentTimestamp(),
    updated_at: getCurrentTimestamp(),
    tags: ["serverless", "api", "example"]
  },
  requirements: {
    functional: {
      workload_type: "api_service",
      expected_traffic: {
        concurrent_users: 500,
        requests_per_second: 20,
        data_transfer_gb_month: 50
      },
      storage_needs: {
        database_size_gb: 10,
        file_storage_gb: 100,
        requires_object_storage: true
      },
      compute_needs: {
        cpu_intensive: false,
        memory_intensive: false,
        gpu_required: false
      }
    },
    non_functional: {
      availability: {
        target_uptime_percent: 99.5,
        multi_az: false,
        disaster_recovery: false
      },
      scalability: {
        auto_scaling: true,
        scale_to_zero: true,
        global_distribution: false
      },
      security: {
        compliance_requirements: [],
        data_encryption: {
          at_rest: true,
          in_transit: true
        },
        network_isolation: false,
        public_access: true
      },
      performance: {
        max_latency_ms: 1000,
        cdn_required: false
      },
      cost: {
        monthly_budget_usd: 200,
        cost_optimization_priority: "high"
      }
    }
  },
  architecture: {
    components: [
      {
        id: "api-gateway",
        type: "network",
        name: "REST API Gateway",
        provider_service: "api_gateway",
        configuration: {
          protocol_type: "REST",
          cors_enabled: true
        }
      },
      {
        id: "get-items-lambda",
        type: "function",
        name: "Get Items Lambda",
        provider_service: "lambda",
        configuration: {
          runtime: "nodejs18.x",
          memory_mb: 256,
          timeout_seconds: 30,
          handler: "index.handler"
        },
        artifacts: [
          {
            type: "zip",
            source: {
              type: "upload",
              platform_storage: "functions/get-items.zip"
            },
            deployment_method: "function_code"
          }
        ]
      },
      {
        id: "create-item-lambda",
        type: "function",
        name: "Create Item Lambda",
        provider_service: "lambda",
        configuration: {
          runtime: "nodejs18.x",
          memory_mb: 256,
          timeout_seconds: 30,
          handler: "index.handler"
        },
        artifacts: [
          {
            type: "zip",
            source: {
              type: "upload",
              platform_storage: "functions/create-item.zip"
            },
            deployment_method: "function_code"
          }
        ]
      },
      {
        id: "items-table",
        type: "database",
        name: "Items Table",
        provider_service: "dynamodb",
        configuration: {
          billing_mode: "PAY_PER_REQUEST",
          hash_key: "id",
          attributes: [
            { name: "id", type: "S" }
          ],
          encryption_enabled: true
        }
      },
      {
        id: "uploads-bucket",
        type: "storage",
        name: "File Uploads Bucket",
        provider_service: "s3",
        configuration: {
          versioning_enabled: false,
          encryption: "AES256",
          lifecycle_rules: [
            {
              id: "delete-old-files",
              expiration_days: 90
            }
          ]
        }
      },
      {
        id: "lambda-execution-role",
        type: "iam_role",
        name: "Lambda Execution Role",
        provider_service: "iam_role",
        configuration: {
          assume_role_policy: "lambda.amazonaws.com",
          managed_policies: [
            "AWSLambdaBasicExecutionRole"
          ]
        }
      }
    ],
    relationships: [
      {
        from: "api-gateway",
        to: "get-items-lambda",
        type: "triggers",
        configuration: {
          method: "GET",
          path: "/items"
        }
      },
      {
        from: "api-gateway",
        to: "create-item-lambda",
        type: "triggers",
        configuration: {
          method: "POST",
          path: "/items"
        }
      },
      {
        from: "get-items-lambda",
        to: "items-table",
        type: "accesses"
      },
      {
        from: "create-item-lambda",
        to: "items-table",
        type: "accesses"
      },
      {
        from: "create-item-lambda",
        to: "uploads-bucket",
        type: "accesses"
      },
      {
        from: "get-items-lambda",
        to: "lambda-execution-role",
        type: "depends_on"
      },
      {
        from: "create-item-lambda",
        to: "lambda-execution-role",
        type: "depends_on"
      }
    ]
  }
};

/**
 * Beispiel 3: Data Pipeline
 * S3 + Lambda + Glue + Athena
 */
export const EXAMPLE_DATA_PIPELINE = {
  version: "1.0.0",
  metadata: {
    id: generateUUID(),
    name: "Data Processing Pipeline",
    description: "Daten-Pipeline für ETL-Verarbeitung mit S3, Lambda-Trigger, Glue-Jobs und Athena-Queries",
    provider: "aws",
    region: "eu-central-1",
    created_at: getCurrentTimestamp(),
    updated_at: getCurrentTimestamp(),
    tags: ["data", "etl", "analytics", "example"]
  },
  requirements: {
    functional: {
      workload_type: "data_processing",
      expected_traffic: {
        data_transfer_gb_month: 500
      },
      storage_needs: {
        file_storage_gb: 1000,
        requires_object_storage: true
      },
      compute_needs: {
        cpu_intensive: true,
        memory_intensive: true,
        gpu_required: false
      }
    },
    non_functional: {
      availability: {
        target_uptime_percent: 99.0,
        multi_az: false,
        disaster_recovery: false
      },
      scalability: {
        auto_scaling: true,
        scale_to_zero: true,
        global_distribution: false
      },
      security: {
        compliance_requirements: ["GDPR"],
        data_encryption: {
          at_rest: true,
          in_transit: true
        },
        network_isolation: false,
        public_access: false
      },
      performance: {
        max_latency_ms: 10000,
        cdn_required: false
      },
      cost: {
        monthly_budget_usd: 300,
        cost_optimization_priority: "high"
      }
    }
  },
  architecture: {
    components: [
      {
        id: "raw-data-bucket",
        type: "storage",
        name: "Raw Data Bucket",
        provider_service: "s3",
        configuration: {
          versioning_enabled: true,
          encryption: "AES256",
          lifecycle_rules: [
            {
              id: "move-to-glacier",
              transition_days: 30,
              storage_class: "GLACIER"
            }
          ]
        }
      },
      {
        id: "processed-data-bucket",
        type: "storage",
        name: "Processed Data Bucket",
        provider_service: "s3",
        configuration: {
          versioning_enabled: true,
          encryption: "AES256"
        }
      },
      {
        id: "trigger-lambda",
        type: "function",
        name: "S3 Trigger Lambda",
        provider_service: "lambda",
        configuration: {
          runtime: "python3.11",
          memory_mb: 512,
          timeout_seconds: 300,
          handler: "handler.main"
        },
        artifacts: [
          {
            type: "zip",
            source: {
              type: "upload",
              platform_storage: "functions/s3-trigger.zip"
            },
            deployment_method: "function_code"
          }
        ]
      },
      {
        id: "glue-job",
        type: "compute",
        name: "ETL Glue Job",
        provider_service: "glue",
        configuration: {
          glue_version: "4.0",
          worker_type: "G.1X",
          number_of_workers: 2,
          max_retries: 1
        }
      },
      {
        id: "athena-workgroup",
        type: "analytics",
        name: "Athena Query Workgroup",
        provider_service: "athena",
        configuration: {
          enforce_workgroup_configuration: true,
          bytes_scanned_cutoff_per_query: 10000000000
        }
      },
      {
        id: "glue-catalog",
        type: "database",
        name: "Glue Data Catalog",
        provider_service: "glue",
        configuration: {
          database_name: "analytics_db"
        }
      },
      {
        id: "glue-execution-role",
        type: "iam_role",
        name: "Glue Execution Role",
        provider_service: "iam_role",
        configuration: {
          assume_role_policy: "glue.amazonaws.com",
          managed_policies: [
            "AWSGlueServiceRole"
          ]
        }
      }
    ],
    relationships: [
      {
        from: "raw-data-bucket",
        to: "trigger-lambda",
        type: "triggers",
        configuration: {
          event: "s3:ObjectCreated:*"
        }
      },
      {
        from: "trigger-lambda",
        to: "glue-job",
        type: "triggers"
      },
      {
        from: "glue-job",
        to: "raw-data-bucket",
        type: "accesses"
      },
      {
        from: "glue-job",
        to: "processed-data-bucket",
        type: "accesses"
      },
      {
        from: "glue-job",
        to: "glue-catalog",
        type: "accesses"
      },
      {
        from: "athena-workgroup",
        to: "glue-catalog",
        type: "accesses"
      },
      {
        from: "athena-workgroup",
        to: "processed-data-bucket",
        type: "accesses"
      },
      {
        from: "glue-job",
        to: "glue-execution-role",
        type: "depends_on"
      }
    ]
  }
};

/**
 * Liste aller verfügbaren Beispiele
 */
export const EXAMPLE_ARCHITECTURES = [
  {
    id: 'simple-web-app',
    name: 'Simple Web Application',
    description: '3-Tier Web-App mit Load Balancer, EC2, RDS und S3',
    provider: 'aws',
    complexity: 'medium',
    data: EXAMPLE_SIMPLE_WEB_APP
  },
  {
    id: 'serverless-api',
    name: 'Serverless REST API',
    description: 'Vollständig serverlose API mit Lambda und DynamoDB',
    provider: 'aws',
    complexity: 'low',
    data: EXAMPLE_SERVERLESS_API
  },
  {
    id: 'data-pipeline',
    name: 'Data Processing Pipeline',
    description: 'ETL-Pipeline mit S3, Lambda, Glue und Athena',
    provider: 'aws',
    complexity: 'high',
    data: EXAMPLE_DATA_PIPELINE
  }
];

/**
 * Hole ein Beispiel nach ID
 * @param {string} id - Example ID
 * @returns {Object|null} Example architecture or null
 */
export function getExampleById(id) {
  const example = EXAMPLE_ARCHITECTURES.find(ex => ex.id === id);
  return example ? { ...example.data } : null;
}

/**
 * Hole alle Beispiele für einen Provider
 * @param {string} provider - Provider ID (aws, azure, gcp)
 * @returns {Array} List of examples
 */
export function getExamplesByProvider(provider) {
  return EXAMPLE_ARCHITECTURES.filter(ex => ex.provider === provider);
}
