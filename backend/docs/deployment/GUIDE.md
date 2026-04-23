# OverCloud Deployment Guide

## Prerequisites

### System Requirements
- **Python:** 3.11 or higher
- **Poetry:** 1.8+ (dependency management)
- **Terraform:** 1.5+ (for actual AWS deployments)
- **Node.js:** 18+ (for frontend, separate guide)
- **Database:** SQLite (development) / PostgreSQL (production)

### AWS Requirements (for deployments)
- AWS Account
- IAM User with programmatic access
- Permissions: EC2, VPC, RDS, S3, Lambda (depending on architecture)

---

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/overcloud.git
cd overcloud/backend
```

### 2. Install Poetry

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

### 3. Install Dependencies

```bash
poetry install
```

This creates a virtual environment and installs all dependencies from `pyproject.toml`.

### 4. Activate Virtual Environment

```bash
poetry shell
```

Or prefix commands with `poetry run`:

```bash
poetry run pytest
```

---

## Configuration

### Environment Variables

Create `.env` file in `backend/` directory:

```bash
# Database
DATABASE_URL=sqlite:///./overcloud.db  # Development
# DATABASE_URL=postgresql://user:pass@localhost/overcloud  # Production

# CORS (Frontend URL)
CORS_ORIGINS=["http://localhost:5173"]

# Terraform
TERRAFORM_BINARY=terraform
TERRAFORM_WORKSPACE_DIR=/tmp/overcloud/deployments
TERRAFORM_TEMPLATE_DIR=backend/templates/terraform

# Pricing Data
PRICING_DATA_DIR=backend/data/aws_pricing

# Schema Version
CURRENT_SCHEMA_VERSION=1.0.0

# Log Level
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

### Database Setup

#### Development (SQLite)

```bash
# Create database and run migrations
poetry run alembic upgrade head
```

#### Production (PostgreSQL)

```bash
# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Create database
sudo -u postgres psql
CREATE DATABASE overcloud;
CREATE USER overcloud_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE overcloud TO overcloud_user;
\q

# Update DATABASE_URL in .env
DATABASE_URL=postgresql://overcloud_user:your_password@localhost/overcloud

# Run migrations
poetry run alembic upgrade head
```

---

## Running the Application

### Development Server

```bash
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Flags:**
- `--reload` - Auto-reload on code changes
- `--host 0.0.0.0` - Accept connections from any IP
- `--port 8000` - Port number

**Access:**
- API: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`

### Production Server

```bash
# With Gunicorn + Uvicorn workers
poetry run gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
```

**Workers:** Set to `(2 * CPU cores) + 1`

---

## Testing

### Run All Tests

```bash
poetry run pytest
```

### Run with Coverage

```bash
poetry run pytest --cov=app --cov-report=html
```

View coverage report: `open htmlcov/index.html`

### Run Specific Tests

```bash
# Single file
poetry run pytest tests/test_terraform_generator.py

# Single test
poetry run pytest tests/test_terraform_generator.py::TestTerraformGenerator::test_generate_vpc

# By marker
poetry run pytest -m "not slow"
```

### Coverage Target

**Goal:** 80%+ coverage across all modules.

**Current Coverage:** ~75% (237 passing tests)

---

## Database Migrations

### Create New Migration

```bash
poetry run alembic revision --autogenerate -m "Description of changes"
```

### Apply Migrations

```bash
poetry run alembic upgrade head
```

### Rollback Migration

```bash
poetry run alembic downgrade -1  # Rollback 1 migration
alembic downgrade base           # Rollback all
```

### Migration History

```bash
poetry run alembic history
poetry run alembic current
```

---

## Deployment Options

### 1. Docker Deployment

#### Build Image

```bash
# From backend/ directory
docker build -t overcloud-backend:latest .
```

#### Run Container

```bash
docker run -d \
  --name overcloud-backend \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql://... \
  -e CORS_ORIGINS='["http://localhost:5173"]' \
  -v /var/overcloud/deployments:/tmp/overcloud/deployments \
  overcloud-backend:latest
```

#### Docker Compose

```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/overcloud
      - CORS_ORIGINS=["http://localhost:5173"]
    volumes:
      - ./deployments:/tmp/overcloud/deployments
    depends_on:
      - db
  
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=overcloud
      - POSTGRES_PASSWORD=password
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

Run: `docker-compose up -d`

---

### 2. AWS EC2 Deployment

#### Launch EC2 Instance

1. **AMI:** Ubuntu 22.04 LTS
2. **Instance Type:** t3.small (minimum)
3. **Security Group:** Allow ports 22 (SSH), 8000 (API)
4. **Storage:** 20 GB GP3

#### Setup Script

```bash
#!/bin/bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install software-properties-common -y
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt install python3.11 python3.11-venv python3-pip -y

# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Install Terraform
wget https://releases.hashicorp.com/terraform/1.5.0/terraform_1.5.0_linux_amd64.zip
unzip terraform_1.5.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/
rm terraform_1.5.0_linux_amd64.zip

# Clone repo
git clone https://github.com/yourusername/overcloud.git
cd overcloud/backend

# Install dependencies
poetry install --no-dev

# Setup database
poetry run alembic upgrade head

# Create systemd service
sudo tee /etc/systemd/system/overcloud.service > /dev/null <<EOF
[Unit]
Description=OverCloud Backend
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/overcloud/backend
Environment="PATH=/home/ubuntu/.local/bin:/usr/bin"
ExecStart=/home/ubuntu/.local/bin/poetry run gunicorn app.main:app \\
  --workers 4 \\
  --worker-class uvicorn.workers.UvicornWorker \\
  --bind 0.0.0.0:8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Start service
sudo systemctl daemon-reload
sudo systemctl enable overcloud
sudo systemctl start overcloud
```

#### Verify

```bash
curl http://<EC2_PUBLIC_IP>:8000/health
```

---

### 3. AWS Lambda Deployment (Serverless)

#### Install Mangum

```bash
poetry add mangum
```

#### Update `app/main.py`

```python
from mangum import Mangum

app = FastAPI(...)

# Lambda handler
lambda_handler = Mangum(app)
```

#### Deploy with AWS SAM

```yaml
# template.yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Resources:
  OverCloudFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: backend/
      Handler: app.main.lambda_handler
      Runtime: python3.11
      Timeout: 30
      MemorySize: 512
      Environment:
        Variables:
          DATABASE_URL: !Ref DatabaseURL
      Events:
        ApiEvent:
          Type: Api
          Properties:
            Path: /{proxy+}
            Method: ANY
```

**Deploy:**
```bash
sam build
sam deploy --guided
```

---

### 4. Heroku Deployment

#### Create `Procfile`

```
web: gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
```

#### Deploy

```bash
heroku create overcloud-backend
heroku addons:create heroku-postgresql:hobby-dev
git push heroku main
heroku run alembic upgrade head
```

---

## Monitoring & Logging

### Application Logs

#### Development

```bash
# Logs printed to console (uvicorn --reload)
```

#### Production

```bash
# Systemd service logs
journalctl -u overcloud -f

# Docker logs
docker logs -f overcloud-backend
```

### Structured Logging

Configure in `app/main.py`:

```python
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### CloudWatch Integration (AWS)

```bash
# Install CloudWatch agent
sudo yum install amazon-cloudwatch-agent -y

# Configure log forwarding
/opt/aws/amazon-cloudwatch-agent/etc/config.json
```

---

## Security Hardening

### 1. Environment Variables

Never commit `.env` files. Use:
- **AWS Secrets Manager** (production)
- **HashiCorp Vault** (enterprise)
- **Environment variables** (containers)

### 2. HTTPS

Use reverse proxy (Nginx/Traefik) with Let's Encrypt:

```nginx
server {
    listen 443 ssl;
    server_name api.overcloud.com;
    
    ssl_certificate /etc/letsencrypt/live/api.overcloud.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.overcloud.com/privkey.pem;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 3. Rate Limiting

Use **slowapi** or **nginx limit_req**:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.get("/api/v1/architectures")
@limiter.limit("100/minute")
def list_architectures():
    ...
```

### 4. CORS Configuration

Production CORS:

```python
# app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app.overcloud.com",  # Production frontend
        "http://localhost:5173"       # Development only
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

---

## Backup & Recovery

### Database Backups

#### PostgreSQL

```bash
# Manual backup
pg_dump overcloud > backup_$(date +%Y%m%d).sql

# Automated (cron)
0 2 * * * pg_dump overcloud | gzip > /backups/overcloud_$(date +\%Y\%m\%d).sql.gz
```

#### Restore

```bash
psql overcloud < backup_20260418.sql
```

### Deployment Workspaces

Workspaces stored in `TERRAFORM_WORKSPACE_DIR` for 30 days (configurable).

**Backup strategy:**
- Sync to S3 bucket (versioned)
- Retain for compliance (90 days)

```bash
aws s3 sync /tmp/overcloud/deployments s3://overcloud-deployments-backup/
```

---

## Troubleshooting

### Issue: Database connection fails

**Solution:**
```bash
# Check PostgreSQL running
sudo systemctl status postgresql

# Check connection string
echo $DATABASE_URL

# Test connection
psql $DATABASE_URL
```

---

### Issue: Terraform command not found

**Solution:**
```bash
# Install Terraform
wget https://releases.hashicorp.com/terraform/1.5.0/terraform_1.5.0_linux_amd64.zip
unzip terraform_1.5.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/
terraform version
```

---

### Issue: Deployment fails with AWS credentials error

**Solution:**
- Check `aws_credentials` passed in request body
- Verify IAM permissions (EC2, VPC, etc.)
- Test credentials: `aws sts get-caller-identity`

---

### Issue: Tests failing with "no such table"

**Solution:**
```bash
# Run migrations
poetry run alembic upgrade head

# Clear test cache
rm -rf .pytest_cache

# Re-run tests
poetry run pytest
```

---

## Performance Tuning

### 1. Database Connection Pooling

```python
# app/models/database.py
engine = create_engine(
    DATABASE_URL,
    pool_size=20,          # Max connections
    max_overflow=10,       # Extra connections under load
    pool_pre_ping=True     # Check connection health
)
```

### 2. Async Database Queries (Future)

Use **SQLAlchemy async** + **asyncpg**:

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

engine = create_async_engine("postgresql+asyncpg://...")
```

### 3. Caching

Add Redis caching for:
- Cost estimates (TTL: 1 hour)
- Architecture lookups (TTL: 5 minutes)

```python
from redis import Redis
cache = Redis(host='localhost', port=6379, db=0)

def get_architecture(id):
    cached = cache.get(f"arch:{id}")
    if cached:
        return json.loads(cached)
    ...
```

---

## Scaling

### Horizontal Scaling

Run multiple instances behind load balancer (ALB/ELB):

```
         ┌────────────┐
         │    ALB     │
         └─────┬──────┘
               │
      ┌────────┴────────┐
      │                 │
┌─────▼─────┐    ┌──────▼────┐
│ Instance 1│    │Instance 2 │
└───────────┘    └───────────┘
```

### Vertical Scaling

Increase instance size (t3.small → t3.medium → t3.large).

### Database Scaling

- **Read Replicas:** Offload read queries
- **Connection Pooling:** PgBouncer
- **Partitioning:** Shard by owner/region

---

## Maintenance

### Update Dependencies

```bash
poetry update
poetry show --outdated
```

### Security Updates

```bash
poetry add package@latest
```

### Log Rotation

```bash
# logrotate config
/var/log/overcloud/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
}
```

---

## Conclusion

OverCloud backend is designed for **production-readiness** with:
- Multiple deployment options (Docker, EC2, Lambda, Heroku)
- Database migrations (Alembic)
- Comprehensive testing (75%+ coverage)
- Security hardening (HTTPS, CORS, secrets management)
- Monitoring & logging (CloudWatch, structured logs)

For API usage, see [API Documentation](../api/README.md).  
For architecture details, see [Services Documentation](../services/README.md).

---

## Support

- **Issues:** https://github.com/yourusername/overcloud/issues
- **Docs:** https://docs.overcloud.com
- **Email:** support@overcloud.com
