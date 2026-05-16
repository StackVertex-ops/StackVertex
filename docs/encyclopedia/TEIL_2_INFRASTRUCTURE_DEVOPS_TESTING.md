# OverCloud Developer's Encyclopedia - Teil 2

**Infrastructure, DevOps, Testing & Security**

**Version:** 1.0  
**Datum:** 2026-05-16  
**Autor:** Claude Agent (mit vollständiger Codebase-Analyse)

---

## Inhaltsverzeichnis

1. [Infrastructure as Code (Terraform)](#1-infrastructure-as-code-terraform)
2. [CI/CD Pipeline (GitHub Actions)](#2-cicd-pipeline-github-actions)
3. [Testing Strategy](#3-testing-strategy)
4. [Cost Estimation System](#4-cost-estimation-system)
5. [Monitoring & Logging](#5-monitoring--logging)
6. [Security Architecture](#6-security-architecture)
7. [Deployment Patterns](#7-deployment-patterns)

---

## 1. Infrastructure as Code (Terraform)

### 1.1 OverCloud Infrastructure (Platform selbst)

OverCloud nutzt Terraform für die **eigene** Platform-Infrastruktur (nicht zu verwechseln mit den Terraform Files die für User-Architectures generiert werden).

**Verzeichnisstruktur:**

```
infrastructure/terraform/
├── modules/               # Wiederverwendbare Module
│   ├── networking/       # VPC, Subnets, Security Groups
│   ├── storage/          # S3, DynamoDB
│   ├── compute/          # Lambda, ECS
│   └── database/         # Aurora Serverless (Legacy - wird zu DynamoDB migriert)
│
└── environments/         # Umgebungs-spezifische Configs
    ├── dev/
    │   ├── main.tf       # Main Config
    │   ├── variables.tf  # Environment Variables
    │   ├── backend.tf    # Terraform State Config
    │   └── terraform.tfvars  # Actual Values (gitignored!)
    ├── staging/
    └── prod/
```

**Beispiel: dev/main.tf**

```hcl
# infrastructure/terraform/environments/dev/main.tf

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Backend: Store Terraform state in S3
  backend "s3" {
    bucket         = "overcloud-terraform-state-dev"
    key            = "dev/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "overcloud-terraform-locks"  # State locking
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "OverCloud"
      ManagedBy   = "Terraform"
      Environment = "dev"
    }
  }
}

# Networking Module
module "networking" {
  source = "../../modules/networking"

  project_name       = "overcloud"
  environment        = "dev"
  vpc_cidr           = "10.0.0.0/16"
  availability_zones = ["us-east-1a", "us-east-1b"]
  
  enable_nat_gateway = false  # Dev: Cost Saving
}

# Storage Module
module "storage" {
  source = "../../modules/storage"

  project_name = "overcloud"
  environment  = "dev"
  
  # DynamoDB Main Table
  dynamodb_table_name = "overcloud-dev-main"
  dynamodb_billing_mode = "PAY_PER_REQUEST"  # On-Demand für dev
  
  # S3 Buckets
  s3_large_items_bucket = "overcloud-dev-large-items"
  s3_terraform_state_bucket = "overcloud-terraform-state-dev"
  
  enable_versioning = true
  enable_encryption = true
}

# Compute Module (Lambda Backend)
module "compute" {
  source = "../../modules/compute"

  project_name = "overcloud"
  environment  = "dev"
  
  lambda_function_name = "overcloud-backend-dev"
  lambda_runtime       = "python3.11"
  lambda_handler       = "lambda_handler.handler"
  lambda_memory_mb     = 512
  lambda_timeout_sec   = 30
  
  # Environment Variables
  lambda_environment_vars = {
    ENV                    = "dev"
    DYNAMODB_TABLE_NAME    = module.storage.dynamodb_table_name
    S3_LARGE_ITEMS_BUCKET  = module.storage.s3_large_items_bucket
    SECRET_KEY             = var.secret_key  # From AWS Secrets Manager
  }
  
  vpc_config = {
    subnet_ids         = module.networking.private_subnet_ids
    security_group_ids = [module.networking.lambda_security_group_id]
  }
}

# API Gateway (Lambda Trigger)
module "api_gateway" {
  source = "../../modules/api_gateway"

  api_name    = "overcloud-api-dev"
  environment = "dev"
  
  lambda_function_arn  = module.compute.lambda_function_arn
  lambda_function_name = module.compute.lambda_function_name
  
  # Custom Domain (optional)
  # domain_name = "api-dev.overcloud.com"
  # certificate_arn = var.acm_certificate_arn
}

# Outputs
output "api_gateway_url" {
  value       = module.api_gateway.api_gateway_url
  description = "API Gateway Invoke URL"
}

output "dynamodb_table_name" {
  value = module.storage.dynamodb_table_name
}
```

**Terraform Commands:**

```bash
# Initialize Terraform
cd infrastructure/terraform/environments/dev
terraform init

# Plan (preview changes)
terraform plan

# Apply (create/update infrastructure)
terraform apply

# Destroy (cleanup)
terraform destroy

# Show current state
terraform show

# List resources
terraform state list
```

### 1.2 User Architecture Generation (Customer-facing)

Dies ist der Terraform Code der **für User Architectures generiert wird**.

**Flow:**

```
User designed Architecture in Frontend
    ↓
JSON State saved to DynamoDB
    ↓
User clicks "Deploy"
    ↓
POST /api/v1/deployments { architecture_id }
    ↓
TerraformGeneratorV2.generate(architecture_json)
    ↓
Terraform Files (.tf) written to /tmp/overcloud/deployments/{deployment_id}/
    ↓
terraform init && terraform plan && terraform apply
    ↓
AWS Resources created in User's AWS Account
```

**Template Beispiele:**

```jinja2
{# backend/templates/terraform/components/main.tf.j2 #}

# ============================================================================
# {{ metadata.name }} - Infrastructure as Code
# ============================================================================
# Generated by OverCloud Infrastructure Designer
# Created: {{ metadata.created_at }}
# Last Updated: {{ metadata.updated_at }}

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "{{ metadata.region }}"

  default_tags {
    tags = {
      Project   = "{{ metadata.name }}"
      ManagedBy = "OverCloud"
      CreatedBy = "{{ metadata.created_by }}"
    }
  }
}
```

```jinja2
{# backend/templates/terraform/components/vpc.tf.j2 #}

# ============================================================================
# VPC Resources
# ============================================================================

{% for vpc in components %}
resource "aws_vpc" "{{ vpc.id }}" {
  cidr_block = "{{ vpc.config.cidr }}"
  
  enable_dns_hostnames = {{ vpc.config.get('enable_dns_hostnames', true) | lower }}
  enable_dns_support   = {{ vpc.config.get('enable_dns_support', true) | lower }}

  tags = {
    Name = "{{ vpc.name }}"
    {% for key, value in vpc.config.get('tags', {}).items() %}
    {{ key }} = "{{ value }}"
    {% endfor %}
  }
}

# Internet Gateway für {{ vpc.name }}
resource "aws_internet_gateway" "{{ vpc.id }}_igw" {
  vpc_id = aws_vpc.{{ vpc.id }}.id

  tags = {
    Name = "{{ vpc.name }}-igw"
  }
}
{% endfor %}
```

```jinja2
{# backend/templates/terraform/components/subnet.tf.j2 #}

# ============================================================================
# Subnet Resources
# ============================================================================

{% for subnet in components %}
resource "aws_subnet" "{{ subnet.id }}" {
  vpc_id            = aws_vpc.{{ subnet.config.vpc_id }}.id
  cidr_block        = "{{ subnet.config.cidr }}"
  availability_zone = "{{ subnet.config.availability_zone }}"
  
  {% if subnet.config.get('map_public_ip_on_launch') %}
  map_public_ip_on_launch = true
  {% endif %}

  tags = {
    Name = "{{ subnet.name }}"
    Type = "{{ subnet.config.get('subnet_type', 'private') }}"
  }
}

# Route Table für {{ subnet.name }}
resource "aws_route_table" "{{ subnet.id }}_rt" {
  vpc_id = aws_vpc.{{ subnet.config.vpc_id }}.id

  {% if subnet.config.get('subnet_type') == 'public' %}
  # Public Subnet: Route zu Internet Gateway
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.{{ subnet.config.vpc_id }}_igw.id
  }
  {% endif %}

  tags = {
    Name = "{{ subnet.name }}-rt"
  }
}

# Route Table Association
resource "aws_route_table_association" "{{ subnet.id }}_rta" {
  subnet_id      = aws_subnet.{{ subnet.id }}.id
  route_table_id = aws_route_table.{{ subnet.id }}_rt.id
}
{% endfor %}
```

```jinja2
{# backend/templates/terraform/components/ec2.tf.j2 #}

# ============================================================================
# EC2 Instances
# ============================================================================

{% for ec2 in components %}
resource "aws_instance" "{{ ec2.id }}" {
  ami           = "{{ ec2.config.ami }}"
  instance_type = "{{ ec2.config.instance_type }}"
  subnet_id     = aws_subnet.{{ ec2.config.subnet_id }}.id
  
  {% if ec2.config.get('key_name') %}
  key_name = "{{ ec2.config.key_name }}"
  {% endif %}
  
  {% if ec2.config.get('security_group_ids') %}
  vpc_security_group_ids = [
    {% for sg_id in ec2.config.security_group_ids %}
    aws_security_group.{{ sg_id }}.id,
    {% endfor %}
  ]
  {% endif %}
  
  {% if ec2.config.get('user_data') %}
  user_data = <<-EOF
{{ ec2.config.user_data | indent(4) }}
  EOF
  {% endif %}
  
  {% if ec2.config.get('iam_instance_profile') %}
  iam_instance_profile = "{{ ec2.config.iam_instance_profile }}"
  {% endif %}

  root_block_device {
    volume_type = "{{ ec2.config.get('volume_type', 'gp3') }}"
    volume_size = {{ ec2.config.get('volume_size', 20) }}
    encrypted   = true
  }

  tags = {
    Name = "{{ ec2.name }}"
    {% for key, value in ec2.config.get('tags', {}).items() %}
    {{ key }} = "{{ value }}"
    {% endfor %}
  }
}

# Elastic IP (wenn public)
{% if ec2.config.get('assign_elastic_ip', false) %}
resource "aws_eip" "{{ ec2.id }}_eip" {
  instance = aws_instance.{{ ec2.id }}.id
  domain   = "vpc"

  tags = {
    Name = "{{ ec2.name }}-eip"
  }
}
{% endif %}
{% endfor %}
```

```jinja2
{# backend/templates/terraform/components/outputs.tf.j2 #}

# ============================================================================
# Outputs
# ============================================================================

# VPC Outputs
{% for vpc in components_by_type.get('vpc', []) %}
output "vpc_{{ vpc.id }}_id" {
  value       = aws_vpc.{{ vpc.id }}.id
  description = "VPC ID for {{ vpc.name }}"
}

output "vpc_{{ vpc.id }}_cidr" {
  value       = aws_vpc.{{ vpc.id }}.cidr_block
  description = "VPC CIDR block"
}
{% endfor %}

# EC2 Outputs
{% for ec2 in components_by_type.get('ec2', []) %}
output "ec2_{{ ec2.id }}_id" {
  value       = aws_instance.{{ ec2.id }}.id
  description = "Instance ID"
}

output "ec2_{{ ec2.id }}_private_ip" {
  value       = aws_instance.{{ ec2.id }}.private_ip
  description = "Private IP address"
}

output "ec2_{{ ec2.id }}_public_ip" {
  value       = aws_instance.{{ ec2.id }}.public_ip
  description = "Public IP address (if assigned)"
}

{% if ec2.config.get('assign_elastic_ip') %}
output "ec2_{{ ec2.id }}_elastic_ip" {
  value       = aws_eip.{{ ec2.id }}_eip.public_ip
  description = "Elastic IP address"
}
{% endif %}
{% endfor %}

# RDS Outputs
{% for rds in components_by_type.get('rds', []) %}
output "rds_{{ rds.id }}_endpoint" {
  value       = aws_db_instance.{{ rds.id }}.endpoint
  description = "RDS endpoint"
}

output "rds_{{ rds.id }}_address" {
  value       = aws_db_instance.{{ rds.id }}.address
  description = "RDS hostname"
}
{% endfor %}

# S3 Outputs
{% for s3 in components_by_type.get('s3', []) %}
output "s3_{{ s3.id }}_bucket_name" {
  value       = aws_s3_bucket.{{ s3.id }}.id
  description = "S3 bucket name"
}

output "s3_{{ s3.id }}_bucket_arn" {
  value       = aws_s3_bucket.{{ s3.id }}.arn
  description = "S3 bucket ARN"
}
{% endfor %}
```

### 1.3 Terraform Execution

**Backend Service:**

```python
# backend/app/services/terraform_executor.py

import subprocess
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class TerraformExecutor:
    """Execute Terraform commands via subprocess."""
    
    def __init__(self, working_dir: Path, terraform_binary: str = "terraform"):
        self.working_dir = working_dir
        self.terraform_binary = terraform_binary
        
        # Ensure working directory exists
        self.working_dir.mkdir(parents=True, exist_ok=True)
    
    def init(self) -> Tuple[bool, str, str]:
        """Run terraform init.
        
        Returns:
            (success, stdout, stderr)
        """
        logger.info(f"Running terraform init in {self.working_dir}")
        
        result = subprocess.run(
            [self.terraform_binary, "init", "-no-color"],
            cwd=self.working_dir,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes
        )
        
        success = result.returncode == 0
        
        if success:
            logger.info("Terraform init successful")
        else:
            logger.error(f"Terraform init failed: {result.stderr}")
        
        return success, result.stdout, result.stderr
    
    def plan(self, out_file: str = "tfplan") -> Tuple[bool, str, str]:
        """Run terraform plan.
        
        Args:
            out_file: Output file for plan (relative to working_dir)
        
        Returns:
            (success, stdout, stderr)
        """
        logger.info(f"Running terraform plan in {self.working_dir}")
        
        result = subprocess.run(
            [
                self.terraform_binary,
                "plan",
                "-no-color",
                "-out", out_file
            ],
            cwd=self.working_dir,
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes
        )
        
        success = result.returncode == 0
        
        if success:
            logger.info("Terraform plan successful")
        else:
            logger.error(f"Terraform plan failed: {result.stderr}")
        
        return success, result.stdout, result.stderr
    
    def apply(self, plan_file: str = "tfplan") -> Tuple[bool, str, str]:
        """Run terraform apply.
        
        Args:
            plan_file: Plan file to apply (relative to working_dir)
        
        Returns:
            (success, stdout, stderr)
        """
        logger.info(f"Running terraform apply in {self.working_dir}")
        
        result = subprocess.run(
            [
                self.terraform_binary,
                "apply",
                "-no-color",
                "-auto-approve",
                plan_file
            ],
            cwd=self.working_dir,
            capture_output=True,
            text=True,
            timeout=1800  # 30 minutes
        )
        
        success = result.returncode == 0
        
        if success:
            logger.info("Terraform apply successful")
        else:
            logger.error(f"Terraform apply failed: {result.stderr}")
        
        return success, result.stdout, result.stderr
    
    def destroy(self, auto_approve: bool = False) -> Tuple[bool, str, str]:
        """Run terraform destroy.
        
        Args:
            auto_approve: Skip confirmation prompt
        
        Returns:
            (success, stdout, stderr)
        """
        logger.warning(f"Running terraform destroy in {self.working_dir}")
        
        cmd = [self.terraform_binary, "destroy", "-no-color"]
        if auto_approve:
            cmd.append("-auto-approve")
        
        result = subprocess.run(
            cmd,
            cwd=self.working_dir,
            capture_output=True,
            text=True,
            timeout=1800  # 30 minutes
        )
        
        success = result.returncode == 0
        
        if success:
            logger.info("Terraform destroy successful")
        else:
            logger.error(f"Terraform destroy failed: {result.stderr}")
        
        return success, result.stdout, result.stderr
    
    def output(self, json: bool = True) -> Tuple[bool, Dict, str]:
        """Get terraform outputs.
        
        Args:
            json: Return outputs as JSON
        
        Returns:
            (success, outputs_dict, stderr)
        """
        cmd = [self.terraform_binary, "output", "-no-color"]
        if json:
            cmd.append("-json")
        
        result = subprocess.run(
            cmd,
            cwd=self.working_dir,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        success = result.returncode == 0
        
        if success and json:
            import json as json_module
            outputs = json_module.loads(result.stdout)
        else:
            outputs = {}
        
        return success, outputs, result.stderr
    
    def validate(self) -> Tuple[bool, str, str]:
        """Run terraform validate.
        
        Returns:
            (success, stdout, stderr)
        """
        result = subprocess.run(
            [self.terraform_binary, "validate", "-no-color", "-json"],
            cwd=self.working_dir,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        return result.returncode == 0, result.stdout, result.stderr
```

**Deployment API:**

```python
# backend/app/api/deployments.py

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from uuid import UUID, uuid4
from pathlib import Path
import json

from app.repositories.deployment import DeploymentRepository
from app.repositories.architecture import ArchitectureRepository
from app.services.terraform_generator_v2 import TerraformGeneratorV2
from app.services.terraform_executor import TerraformExecutor
from app.config import settings

router = APIRouter()

@router.post("/deployments")
async def create_deployment(
    deployment_data: DeploymentCreate,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    deployment_repo: DeploymentRepository = Depends(get_deployment_repo),
    arch_repo: ArchitectureRepository = Depends(get_arch_repo)
):
    """
    Create new deployment.
    
    Flow:
    1. Get architecture JSON
    2. Generate Terraform files
    3. Write to workspace
    4. Run terraform init, plan, apply (in background)
    5. Return deployment ID
    """
    
    # 1. Get architecture
    architecture = arch_repo.get(deployment_data.architecture_id)
    if not architecture:
        raise HTTPException(404, "Architecture not found")
    
    # Authorization check
    if architecture['organisation_id'] != current_user['organisation_id']:
        raise HTTPException(403, "Access denied")
    
    # 2. Create deployment record
    deployment_id = uuid4()
    deployment = deployment_repo.create({
        "id": str(deployment_id),
        "organisation_id": architecture['organisation_id'],
        "architecture_id": str(deployment_data.architecture_id),
        "status": "pending",
        "created_by": current_user['id']
    })
    
    # 3. Schedule background task
    background_tasks.add_task(
        execute_deployment,
        deployment_id,
        architecture,
        deployment_repo
    )
    
    return DeploymentResponse(**deployment)

async def execute_deployment(
    deployment_id: UUID,
    architecture: dict,
    deployment_repo: DeploymentRepository
):
    """
    Background task: Execute Terraform deployment.
    
    This runs asynchronously after API response.
    """
    
    try:
        # Update status
        deployment_repo.update(deployment_id, {"status": "generating"})
        
        # 1. Generate Terraform files
        generator = TerraformGeneratorV2()
        tf_files = generator.generate(architecture)
        
        # 2. Write to workspace
        workspace_dir = Path(settings.TERRAFORM_WORKSPACE_DIR) / str(deployment_id)
        workspace_dir.mkdir(parents=True, exist_ok=True)
        
        for filename, content in tf_files.items():
            file_path = workspace_dir / filename
            file_path.write_text(content)
        
        logger.info(f"Generated {len(tf_files)} Terraform files in {workspace_dir}")
        
        # 3. Execute Terraform
        executor = TerraformExecutor(workspace_dir)
        
        deployment_repo.update(deployment_id, {"status": "initializing"})
        
        # Init
        success, stdout, stderr = executor.init()
        if not success:
            raise Exception(f"Terraform init failed: {stderr}")
        
        deployment_repo.update(deployment_id, {"status": "planning"})
        
        # Plan
        success, stdout, stderr = executor.plan()
        if not success:
            raise Exception(f"Terraform plan failed: {stderr}")
        
        # Store plan output
        deployment_repo.update(deployment_id, {
            "status": "applying",
            "plan_output": stdout
        })
        
        # Apply
        success, stdout, stderr = executor.apply()
        if not success:
            raise Exception(f"Terraform apply failed: {stderr}")
        
        # Get outputs
        success, outputs, _ = executor.output(json=True)
        
        # 4. Update deployment with results
        deployment_repo.update(deployment_id, {
            "status": "completed",
            "outputs": outputs,
            "completed_at": datetime.utcnow().isoformat()
        })
        
        logger.info(f"Deployment {deployment_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Deployment {deployment_id} failed: {e}")
        
        deployment_repo.update(deployment_id, {
            "status": "failed",
            "error_message": str(e),
            "failed_at": datetime.utcnow().isoformat()
        })
```

---

## 2. CI/CD Pipeline (GitHub Actions)

### 2.1 Backend CI/CD

**Workflow: `.github/workflows/backend-ci.yml`**

```yaml
name: Backend CI/CD

on:
  push:
    branches: [ main, master, develop ]
    paths:
      - 'backend/**'
      - '.github/workflows/backend-ci.yml'
  pull_request:
    branches: [ main, master ]
    paths:
      - 'backend/**'

env:
  PYTHON_VERSION: '3.11'

jobs:
  # ============================================================================
  # Test & Lint Job
  # ============================================================================
  test:
    name: Test & Lint
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install Poetry
        uses: snok/install-poetry@v1
        with:
          version: latest
          virtualenvs-create: true
          virtualenvs-in-project: true

      - name: Load cached venv
        id: cached-poetry-dependencies
        uses: actions/cache@v4
        with:
          path: backend/.venv
          key: venv-${{ runner.os }}-${{ hashFiles('**/poetry.lock') }}

      - name: Install dependencies
        if: steps.cached-poetry-dependencies.outputs.cache-hit != 'true'
        working-directory: backend
        run: poetry install --no-interaction --no-root

      - name: Install project
        working-directory: backend
        run: poetry install --no-interaction

      - name: Lint with Ruff
        working-directory: backend
        run: poetry run ruff check app tests

      - name: Format check with Black
        working-directory: backend
        run: poetry run black --check app tests

      - name: Type check with mypy
        working-directory: backend
        run: poetry run mypy app
        continue-on-error: true  # Don't fail build (yet)

      - name: Run tests with coverage
        working-directory: backend
        env:
          TESTING: 'true'
          SECRET_KEY: ${{ secrets.TEST_SECRET_KEY || 'test-secret-key-min-32-chars-long-for-jwt' }}
          DYNAMODB_TABLE_NAME: 'test-table'
          AWS_REGION: 'us-east-1'
          AWS_ACCESS_KEY_ID: 'test'
          AWS_SECRET_ACCESS_KEY: 'test'
        run: |
          poetry run pytest tests/ \
            -v \
            --cov=app \
            --cov-report=xml \
            --cov-report=term \
            --cov-report=html

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        with:
          file: backend/coverage.xml
          flags: backend
          name: backend-coverage
        continue-on-error: true

  # ============================================================================
  # Security Scan Job
  # ============================================================================
  security:
    name: Security Scan
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install Poetry
        uses: snok/install-poetry@v1

      - name: Install dependencies
        working-directory: backend
        run: poetry install --no-interaction

      - name: Run Bandit (security linter)
        working-directory: backend
        run: |
          poetry run bandit -r app \
            -f json \
            -o bandit-report.json
        continue-on-error: true

      - name: Run Safety (dependency vulnerabilities)
        working-directory: backend
        run: poetry run safety check --json
        continue-on-error: true

      - name: Detect secrets
        working-directory: backend
        run: |
          poetry run detect-secrets scan \
            --baseline .secrets.baseline
        continue-on-error: true

  # ============================================================================
  # Build Docker Image Job
  # ============================================================================
  build:
    name: Build Docker Image
    runs-on: ubuntu-latest
    needs: [test, security]
    if: github.ref == 'refs/heads/main' || github.ref == 'refs/heads/master'

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to Docker Hub
        if: github.event_name != 'pull_request'
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ secrets.DOCKER_USERNAME }}/overcloud-backend
          tags: |
            type=ref,event=branch
            type=sha,prefix={{branch}}-
            type=semver,pattern={{version}}
            type=raw,value=latest,enable={{is_default_branch}}

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: backend
          push: ${{ github.event_name != 'pull_request' }}
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  # ============================================================================
  # Deploy to AWS Job
  # ============================================================================
  deploy:
    name: Deploy to AWS
    runs-on: ubuntu-latest
    needs: [build]
    if: github.ref == 'refs/heads/main' || github.ref == 'refs/heads/master'
    environment: production

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ secrets.AWS_REGION || 'us-east-1' }}

      - name: Deploy to Lambda
        run: |
          # Update Lambda function code
          aws lambda update-function-code \
            --function-name overcloud-backend-prod \
            --image-uri ${{ secrets.DOCKER_USERNAME }}/overcloud-backend:latest

      - name: Health check
        run: |
          # Wait for deployment to stabilize
          sleep 30
          
          # Check API health
          curl -f https://api.overcloud.com/health || exit 1

      - name: Notify deployment
        if: success()
        run: echo "Deployment successful! 🚀"
```

### 2.2 Frontend CI/CD

**Workflow: `.github/workflows/frontend-ci.yml`**

```yaml
name: Frontend CI/CD

on:
  push:
    branches: [ main, master, develop ]
    paths:
      - 'frontend/**'
  pull_request:
    branches: [ main, master ]
    paths:
      - 'frontend/**'

jobs:
  test:
    name: Test & Build
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        working-directory: frontend
        run: npm ci

      - name: Run E2E tests (Playwright)
        working-directory: frontend
        run: npm run test:e2e

      - name: Build production
        working-directory: frontend
        run: npm run build

      - name: Upload build artifact
        uses: actions/upload-artifact@v4
        with:
          name: frontend-dist
          path: frontend/dist/

  deploy:
    name: Deploy to S3 + CloudFront
    runs-on: ubuntu-latest
    needs: [test]
    if: github.ref == 'refs/heads/main'
    environment: production

    steps:
      - name: Download build artifact
        uses: actions/download-artifact@v4
        with:
          name: frontend-dist
          path: dist/

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1

      - name: Sync to S3
        run: |
          aws s3 sync dist/ s3://overcloud-frontend-prod/ \
            --delete \
            --cache-control "public,max-age=31536000,immutable"

      - name: Invalidate CloudFront cache
        run: |
          aws cloudfront create-invalidation \
            --distribution-id ${{ secrets.CLOUDFRONT_DISTRIBUTION_ID }} \
            --paths "/*"
```

### 2.3 Security Scanning

**Workflow: `.github/workflows/security-scan.yml`**

```yaml
name: Security Scan

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday

jobs:
  # SAST (Static Application Security Testing)
  sast:
    name: Static Analysis
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Run Trivy vulnerability scanner (Filesystem)
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          format: 'sarif'
          output: 'trivy-results.sarif'

      - name: Upload Trivy results to GitHub Security
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: 'trivy-results.sarif'

  # Dependency Review
  dependency-review:
    name: Dependency Review
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request'

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Dependency Review
        uses: actions/dependency-review-action@v4
        with:
          fail-on-severity: high

  # Secret Scanning
  secret-scan:
    name: Secret Scanning
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Full history for Gitleaks

      - name: Run Gitleaks
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GITLEAKS_LICENSE: ${{ secrets.GITLEAKS_LICENSE }}
```

---

## 3. Testing Strategy

### 3.1 Backend Testing (pytest)

**Test Struktur:**

```
backend/tests/
├── unit/                  # Unit Tests (einzelne Funktionen/Klassen)
│   ├── test_user_repository.py
│   ├── test_architecture_repository.py
│   ├── test_terraform_generator.py
│   └── test_cost_calculator.py
│
├── integration/           # Integration Tests (API Endpoints)
│   ├── test_auth_api.py
│   ├── test_users_api.py
│   ├── test_architectures_api.py
│   └── test_deployments_api.py
│
├── fixtures/              # Test Data
│   ├── sample_architectures.json
│   └── sample_users.json
│
└── conftest.py            # Pytest Fixtures & Config
```

**conftest.py (Shared Fixtures):**

```python
# backend/tests/conftest.py

import pytest
from fastapi.testclient import TestClient
from moto import mock_dynamodb, mock_s3
import boto3
from uuid import uuid4

from app.main import app
from app.config import settings
from app.db.dynamodb import get_dynamodb_table
from app.repositories.user import UserRepository

# ============================================================================
# Fixtures: Mock AWS Services
# ============================================================================

@pytest.fixture(scope="function")
def aws_credentials():
    """Mock AWS Credentials for moto."""
    import os
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

@pytest.fixture(scope="function")
def dynamodb_table(aws_credentials):
    """Create mock DynamoDB table."""
    with mock_dynamodb():
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        
        # Create table
        table = dynamodb.create_table(
            TableName='test-table',
            KeySchema=[
                {'AttributeName': 'PK', 'KeyType': 'HASH'},
                {'AttributeName': 'SK', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'PK', 'AttributeType': 'S'},
                {'AttributeName': 'SK', 'AttributeType': 'S'},
                {'AttributeName': 'email', 'AttributeType': 'S'},
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'email-index',
                    'KeySchema': [
                        {'AttributeName': 'email', 'KeyType': 'HASH'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 1,
                        'WriteCapacityUnits': 1
                    }
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        yield table

@pytest.fixture(scope="function")
def s3_bucket(aws_credentials):
    """Create mock S3 bucket."""
    with mock_s3():
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='test-bucket')
        
        yield s3

# ============================================================================
# Fixtures: Test Client
# ============================================================================

@pytest.fixture(scope="function")
def client(dynamodb_table, s3_bucket):
    """FastAPI TestClient mit mocked AWS."""
    
    # Override dependencies
    app.dependency_overrides[get_dynamodb_table] = lambda: dynamodb_table
    
    # Disable rate limiting in tests
    settings.TESTING = True
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Cleanup
    app.dependency_overrides.clear()
    settings.TESTING = False

# ============================================================================
# Fixtures: Test Data
# ============================================================================

@pytest.fixture
def test_user(dynamodb_table):
    """Create test user."""
    from passlib.context import CryptContext
    
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    user_id = str(uuid4())
    user_data = {
        "PK": f"USER#{user_id}",
        "SK": "METADATA",
        "entity_type": "user",
        "id": user_id,
        "email": "test@example.com",
        "name": "Test User",
        "hashed_password": pwd_context.hash("TestPassword123"),
        "system_role": "user",
        "status": "active"
    }
    
    dynamodb_table.put_item(Item=user_data)
    
    return user_data

@pytest.fixture
def auth_headers(client, test_user):
    """Get authentication headers (JWT token)."""
    
    # Login to get token
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user["email"],
            "password": "TestPassword123"
        }
    )
    
    assert response.status_code == 200
    
    token = response.json()["access_token"]
    
    return {"Authorization": f"Bearer {token}"}
```

**Example Unit Test:**

```python
# backend/tests/unit/test_user_repository.py

import pytest
from uuid import uuid4
from app.repositories.user import UserRepository

def test_create_user(dynamodb_table):
    """Test creating a user."""
    repo = UserRepository(table=dynamodb_table)
    
    user_data = {
        "id": str(uuid4()),
        "email": "newuser@example.com",
        "name": "New User",
        "hashed_password": "hashed",
        "system_role": "user",
        "status": "active"
    }
    
    user = repo.create(user_data)
    
    assert user["email"] == "newuser@example.com"
    assert user["name"] == "New User"
    assert "created_at" in user
    assert "updated_at" in user

def test_get_user_by_id(dynamodb_table, test_user):
    """Test getting user by ID."""
    repo = UserRepository(table=dynamodb_table)
    
    user = repo.get(uuid4(test_user["id"]))
    
    assert user is not None
    assert user["email"] == test_user["email"]

def test_get_user_by_email(dynamodb_table, test_user):
    """Test getting user by email (GSI)."""
    repo = UserRepository(table=dynamodb_table)
    
    user = repo.get_by_email(test_user["email"])
    
    assert user is not None
    assert user["id"] == test_user["id"]

def test_get_nonexistent_user(dynamodb_table):
    """Test getting user that doesn't exist."""
    repo = UserRepository(table=dynamodb_table)
    
    user = repo.get(uuid4())
    
    assert user is None
```

**Example Integration Test:**

```python
# backend/tests/integration/test_auth_api.py

import pytest

def test_register_user(client):
    """Test user registration."""
    
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "name": "New User",
            "password": "SecurePassword123"
        }
    )
    
    assert response.status_code == 201
    
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["name"] == "New User"
    assert "hashed_password" not in data  # Password should not be in response
    assert data["system_role"] == "user"
    assert data["status"] == "active"

def test_register_duplicate_email(client, test_user):
    """Test registering with existing email."""
    
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": test_user["email"],
            "name": "Duplicate User",
            "password": "SecurePassword123"
        }
    )
    
    assert response.status_code == 409  # Conflict
    assert "already registered" in response.json()["detail"].lower()

def test_login_success(client, test_user):
    """Test successful login."""
    
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user["email"],
            "password": "TestPassword123"
        }
    )
    
    assert response.status_code == 200
    
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 3600  # 1 hour

def test_login_wrong_password(client, test_user):
    """Test login with wrong password."""
    
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user["email"],
            "password": "WrongPassword"
        }
    )
    
    assert response.status_code == 401
    assert "invalid credentials" in response.json()["detail"].lower()

def test_get_current_user(client, auth_headers):
    """Test getting current user profile."""
    
    response = client.get(
        "/api/v1/users/me",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    
    data = response.json()
    assert data["email"] == "test@example.com"

def test_protected_endpoint_without_token(client):
    """Test accessing protected endpoint without token."""
    
    response = client.get("/api/v1/users/me")
    
    assert response.status_code == 401
```

**Running Tests:**

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_user_repository.py

# Run with verbose output
pytest -v

# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/
```

### 3.2 Frontend Testing (Playwright)

**Test Struktur:**

```
frontend/tests/
├── e2e/                      # End-to-End Tests
│   ├── auth.spec.js         # Login, Registration
│   ├── designer.spec.js     # Infrastructure Designer
│   └── deployment.spec.js   # Deployment Flow
│
└── unit/                     # Unit Tests (geplant - Vitest)
    ├── state.test.js
    └── canvas.test.js
```

**Example E2E Test:**

```javascript
// frontend/tests/e2e/auth.spec.js

import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('http://localhost:5173');
    });

    test('should show login page', async ({ page }) => {
        await page.goto('http://localhost:5173/login.html');
        
        await expect(page.locator('h1')).toContainText('Login');
        await expect(page.locator('input[name="email"]')).toBeVisible();
        await expect(page.locator('input[name="password"]')).toBeVisible();
    });

    test('should register new user', async ({ page }) => {
        await page.goto('http://localhost:5173/register.html');
        
        // Fill form
        await page.fill('input[name="email"]', 'test@example.com');
        await page.fill('input[name="name"]', 'Test User');
        await page.fill('input[name="password"]', 'SecurePassword123');
        
        // Submit
        await page.click('button[type="submit"]');
        
        // Should redirect to dashboard
        await expect(page).toHaveURL(/dashboard.html/);
    });

    test('should login existing user', async ({ page }) => {
        await page.goto('http://localhost:5173/login.html');
        
        // Fill credentials
        await page.fill('input[name="email"]', 'test@example.com');
        await page.fill('input[name="password"]', 'TestPassword123');
        
        // Submit
        await page.click('button[type="submit"]');
        
        // Should redirect to dashboard
        await expect(page).toHaveURL(/dashboard.html/);
        
        // Should show user name
        await expect(page.locator('.user-name')).toContainText('Test User');
    });

    test('should show error for invalid credentials', async ({ page }) => {
        await page.goto('http://localhost:5173/login.html');
        
        await page.fill('input[name="email"]', 'test@example.com');
        await page.fill('input[name="password"]', 'WrongPassword');
        await page.click('button[type="submit"]');
        
        // Should show error message
        await expect(page.locator('.error-message')).toBeVisible();
        await expect(page.locator('.error-message')).toContainText('Invalid credentials');
    });
});

test.describe('Infrastructure Designer', () => {
    test.beforeEach(async ({ page }) => {
        // Login first
        await page.goto('http://localhost:5173/login.html');
        await page.fill('input[name="email"]', 'test@example.com');
        await page.fill('input[name="password"]', 'TestPassword123');
        await page.click('button[type="submit"]');
        
        // Navigate to designer
        await page.goto('http://localhost:5173/infrastructure-designer.html');
    });

    test('should show component palette', async ({ page }) => {
        await expect(page.locator('.component-palette')).toBeVisible();
        
        // Should show AWS components
        await expect(page.locator('[data-component="vpc"]')).toBeVisible();
        await expect(page.locator('[data-component="ec2"]')).toBeVisible();
        await expect(page.locator('[data-component="rds"]')).toBeVisible();
    });

    test('should add VPC to canvas', async ({ page }) => {
        // Drag VPC from palette
        const vpc = page.locator('[data-component="vpc"]');
        const canvas = page.locator('#canvas-container');
        
        await vpc.dragTo(canvas, {
            targetPosition: { x: 200, y: 200 }
        });
        
        // Canvas should show VPC node
        await expect(page.locator('.cy-node[type="vpc"]')).toBeVisible();
    });

    test('should open configuration panel on node click', async ({ page }) => {
        // Add VPC
        await page.locator('[data-component="vpc"]').dragTo(
            page.locator('#canvas-container'),
            { targetPosition: { x: 200, y: 200 } }
        );
        
        // Click VPC node
        await page.locator('.cy-node[type="vpc"]').click();
        
        // Configuration tabs should open
        await expect(page.locator('.configuration-tabs')).toBeVisible();
        await expect(page.locator('input[name="cidr"]')).toBeVisible();
    });

    test('should save architecture', async ({ page }) => {
        // Add some components
        await page.locator('[data-component="vpc"]').dragTo(
            page.locator('#canvas-container')
        );
        
        // Click save button
        await page.click('button#save-btn');
        
        // Should show success message
        await expect(page.locator('.success-message')).toBeVisible();
        await expect(page.locator('.success-message')).toContainText('saved');
    });
});
```

**Running E2E Tests:**

```bash
# Run all E2E tests
npm run test:e2e

# Run with UI (interactive)
npm run test:e2e:ui

# Run specific test
npm run test:e2e -- tests/e2e/auth.spec.js

# Run in headed mode (see browser)
npm run test:e2e -- --headed
```

---

## 4. Cost Estimation System

### 4.1 Cost Calculator

**Data Source: AWS Pricing**

```python
# backend/app/data/aws_constraints.py

from decimal import Decimal
from pydantic import BaseModel
from typing import Dict

class EC2InstanceType(BaseModel):
    """EC2 Instance Type mit Pricing."""
    name: str
    vcpus: int
    memory_gb: float
    price_per_hour_usd: Decimal
    architecture: str  # x86_64, arm64

# US-East-1 Pricing (Stand: 2026-05-16)
EC2_INSTANCE_TYPES: Dict[str, EC2InstanceType] = {
    "t3.nano": EC2InstanceType(
        name="t3.nano",
        vcpus=2,
        memory_gb=0.5,
        price_per_hour_usd=Decimal("0.0052"),
        architecture="x86_64"
    ),
    "t3.micro": EC2InstanceType(
        name="t3.micro",
        vcpus=2,
        memory_gb=1,
        price_per_hour_usd=Decimal("0.0104"),
        architecture="x86_64"
    ),
    "t3.small": EC2InstanceType(
        name="t3.small",
        vcpus=2,
        memory_gb=2,
        price_per_hour_usd=Decimal("0.0208"),
        architecture="x86_64"
    ),
    "t3.medium": EC2InstanceType(
        name="t3.medium",
        vcpus=2,
        memory_gb=4,
        price_per_hour_usd=Decimal("0.0416"),
        architecture="x86_64"
    ),
    # ... mehr Instance Types
}

class RDSInstanceClass(BaseModel):
    """RDS Instance Class mit Pricing."""
    name: str
    vcpus: int
    memory_gb: float
    price_per_hour_usd: Decimal
    price_per_hour_multi_az_usd: Decimal

RDS_INSTANCE_CLASSES: Dict[str, RDSInstanceClass] = {
    "db.t3.micro": RDSInstanceClass(
        name="db.t3.micro",
        vcpus=2,
        memory_gb=1,
        price_per_hour_usd=Decimal("0.017"),
        price_per_hour_multi_az_usd=Decimal("0.034")
    ),
    # ... mehr RDS Classes
}
```

**Cost Calculator Service:**

```python
# backend/app/services/cost_calculator.py

from decimal import Decimal
from typing import List
from pydantic import BaseModel

from app.data.aws_constraints import EC2_INSTANCE_TYPES, RDS_INSTANCE_CLASSES

class CostItem(BaseModel):
    service: str
    resource: str
    amount: Decimal
    unit: str
    quantity: Decimal
    total: Decimal

class CostBreakdown(BaseModel):
    items: List[CostItem]
    subtotal: Decimal
    total: Decimal
    currency: str = "USD"
    period: str = "monthly"
    assumptions: List[str] = []

def calculate_architecture_cost(architecture_json: dict) -> CostBreakdown:
    """Calculate total cost for architecture."""
    
    items = []
    assumptions = []
    
    components = architecture_json.get('components', {})
    
    # Calculate costs for each component type
    for component_id, component in components.items():
        comp_type = component['type']
        config = component['config']
        
        if comp_type == 'ec2':
            item = calculate_ec2_cost(
                instance_type=config['instance_type'],
                count=config.get('count', 1)
            )
            items.append(item)
        
        elif comp_type == 'rds':
            rds_items = calculate_rds_cost(
                instance_class=config['instance_class'],
                engine=config['engine'],
                storage_gb=config['allocated_storage'],
                storage_type=config.get('storage_type', 'gp3'),
                multi_az=config.get('multi_az', False)
            )
            items.extend(rds_items)
        
        elif comp_type == 's3':
            item = calculate_s3_cost(
                storage_gb=config.get('estimated_storage_gb', 100),
                storage_class=config.get('storage_class', 'STANDARD')
            )
            items.append(item)
        
        # ... mehr Component Types
    
    # VPC, Subnets, IGW sind kostenlos
    # NAT Gateway ist teuer
    nat_gateways = [c for c in components.values() if c['type'] == 'nat_gateway']
    if nat_gateways:
        for nat in nat_gateways:
            items.append(CostItem(
                service="VPC",
                resource=f"NAT Gateway ({nat['name']})",
                amount=Decimal("0.045"),  # per hour
                unit="hour",
                quantity=Decimal("730"),  # hours per month
                total=Decimal("32.85")
            ))
    
    # Calculate totals
    subtotal = sum(item.total for item in items)
    
    assumptions.append("Assumes 730 hours/month (24*30.5)")
    assumptions.append("Prices based on US-East-1 region")
    assumptions.append("Data transfer costs not included")
    
    return CostBreakdown(
        items=items,
        subtotal=subtotal,
        total=subtotal,
        assumptions=assumptions
    )
```

**API Endpoint:**

```python
# backend/app/api/costs.py

from fastapi import APIRouter, Depends
from app.services.cost_calculator import calculate_architecture_cost

router = APIRouter()

@router.post("/costs/estimate")
async def estimate_cost(architecture_json: dict):
    """
    Estimate cost for architecture.
    
    Request Body: Architecture JSON (same as Infrastructure Designer state)
    Response: CostBreakdown
    """
    
    breakdown = calculate_architecture_cost(architecture_json)
    
    return breakdown
```

**Frontend Integration:**

```javascript
// frontend/src/js/components/LiveCostPanel.js

export class LiveCostPanel {
    constructor(containerId, architectureState) {
        this.container = document.getElementById(containerId);
        this.state = architectureState;
        this.currentCost = null;
        
        this.render();
        
        // Subscribe to state changes
        this.state.subscribe(this.handleStateChange.bind(this));
        
        // Initial cost calculation
        this.updateCost();
    }
    
    async handleStateChange(changeType, payload, state) {
        // Debounce updates (don't recalculate on every keystroke)
        if (this.updateTimeout) {
            clearTimeout(this.updateTimeout);
        }
        
        this.updateTimeout = setTimeout(() => {
            this.updateCost();
        }, 1000);  // Wait 1 second after last change
    }
    
    async updateCost() {
        try {
            // Call API
            const response = await fetch('/api/v1/costs/estimate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.getAuthToken()}`
                },
                body: JSON.stringify(this.state.state)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            this.currentCost = await response.json();
            this.render();
            
        } catch (error) {
            console.error('Failed to calculate cost:', error);
        }
    }
    
    render() {
        if (!this.currentCost) {
            this.container.innerHTML = `
                <div class="p-4 bg-white rounded-lg shadow">
                    <h3 class="text-lg font-semibold mb-2">Estimated Cost</h3>
                    <p class="text-gray-500">Calculating...</p>
                </div>
            `;
            return;
        }
        
        const { total, currency, period, items, assumptions } = this.currentCost;
        
        this.container.innerHTML = `
            <div class="p-4 bg-white rounded-lg shadow">
                <h3 class="text-lg font-semibold mb-4">Estimated Cost</h3>
                
                <!-- Total Cost -->
                <div class="mb-4 p-3 bg-blue-50 rounded-lg">
                    <div class="text-sm text-gray-600">Monthly Total</div>
                    <div class="text-3xl font-bold text-blue-600">
                        $${total.toFixed(2)} ${currency}
                    </div>
                    <div class="text-xs text-gray-500">per ${period}</div>
                </div>
                
                <!-- Cost Breakdown -->
                <div class="mb-4">
                    <h4 class="text-sm font-semibold mb-2">Breakdown</h4>
                    <div class="space-y-2">
                        ${items.map(item => `
                            <div class="flex justify-between items-center text-sm">
                                <div>
                                    <div class="font-medium">${item.service}: ${item.resource}</div>
                                    <div class="text-xs text-gray-500">
                                        $${item.amount} × ${item.quantity} ${item.unit}
                                    </div>
                                </div>
                                <div class="font-semibold">$${item.total.toFixed(2)}</div>
                            </div>
                        `).join('')}
                    </div>
                </div>
                
                <!-- Assumptions -->
                <div class="text-xs text-gray-500">
                    <div class="font-semibold mb-1">Assumptions:</div>
                    <ul class="list-disc list-inside">
                        ${assumptions.map(a => `<li>${a}</li>`).join('')}
                    </ul>
                </div>
            </div>
        `;
    }
    
    getAuthToken() {
        return localStorage.getItem('overcloud-token');
    }
}
```

---

**Ende Teil 2 - Fortsetzung folgt in den finalen Abschnitten**

Teil 2 umfasst:
- Infrastructure as Code (Terraform für Platform + User Architectures)
- CI/CD Pipeline (GitHub Actions, Backend/Frontend, Security Scanning)
- Testing Strategy (pytest Unit/Integration Tests, Playwright E2E Tests)
- Cost Estimation System (AWS Pricing Data, Calculator, Live Cost Panel)

**Weiter in Teil 3:**
- Monitoring & Logging (CloudWatch, Sentry, Structured Logging)
- Security Architecture (OWASP Top 10, Account Lockout, RBAC)
- Deployment Patterns (Lambda, ECS Fargate, Blue/Green)
- API Reference (Alle Endpoints dokumentiert)
