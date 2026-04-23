"""Lambda Handler für AWS Lambda Deployment.

Nutzt Mangum um FastAPI ASGI App in Lambda zu wrappen.
"""

import os
import json
import boto3
from mangum import Mangum
from app.main import app

# Database Credentials aus AWS Secrets Manager holen
def get_database_credentials():
    """Holt Database Credentials aus AWS Secrets Manager."""
    secret_arn = os.environ.get("DATABASE_SECRET_ARN")

    if not secret_arn:
        raise ValueError("DATABASE_SECRET_ARN environment variable not set")

    # Secrets Manager Client
    client = boto3.client("secretsmanager")

    try:
        response = client.get_secret_value(SecretId=secret_arn)
        secret = json.loads(response["SecretString"])

        # Setze DATABASE_URL Environment Variable
        database_url = (
            f"postgresql://{secret['username']}:{secret['password']}"
            f"@{secret['host']}:{secret['port']}/{secret['database']}"
        )
        os.environ["DATABASE_URL"] = database_url

        return secret
    except Exception as e:
        print(f"Error fetching database credentials: {e}")
        raise


# Credentials beim Start holen (Cold Start)
get_database_credentials()

# Mangum Handler (FastAPI → Lambda)
handler = Mangum(app, lifespan="off")
