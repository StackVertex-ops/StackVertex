"""Lambda Handler für API Gateway.

Verwendet Mangum um FastAPI in AWS Lambda zu wrappen.
Handelt alle HTTP Requests via API Gateway HTTP API.

Hybrid Serverless Architecture:
- Lambda (99% Traffic): API Requests, schnelle Operationen
- ECS (1% Traffic): Lange Terraform Deployments (>15 Min)
"""

import logging
import os

from mangum import Mangum

from app.main import app

# Logger konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Detect Lambda Environment
IS_LAMBDA = os.environ.get("AWS_LAMBDA_FUNCTION_NAME") is not None

if IS_LAMBDA:
    logger.info("Running in AWS Lambda environment")
else:
    logger.info("Running in local/container environment")

# Mangum Adapter: FastAPI → Lambda
# lifespan="off" da Lambda keine Background Tasks während Idle unterstützt
handler = Mangum(app, lifespan="off")

logger.info("Lambda Handler initialisiert - FastAPI via Mangum")
