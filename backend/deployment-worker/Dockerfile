# Dockerfile für ECS Deployment Worker
# Führt Terraform Deployments aus (on-demand, lange Laufzeit >10 Min)

FROM python:3.11-slim

WORKDIR /app

# System Dependencies installieren
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        wget \
        unzip \
        ca-certificates \
        git \
    && rm -rf /var/lib/apt/lists/*

# Terraform installieren
ARG TERRAFORM_VERSION=1.6.0
RUN wget https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip && \
    unzip terraform_${TERRAFORM_VERSION}_linux_amd64.zip && \
    mv terraform /usr/local/bin/ && \
    rm terraform_${TERRAFORM_VERSION}_linux_amd64.zip && \
    terraform --version

# Poetry installieren
RUN pip install --no-cache-dir poetry==1.7.1

# Python Dependencies
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false && \
    poetry install --only main --no-interaction --no-ansi

# Application Code
COPY app/ ./app/
COPY deployment-worker/worker.py ./

# Healthcheck (optional, für ECS Task Health)
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Run Worker
CMD ["python", "worker.py"]
