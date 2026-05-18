"""
Simple API Blueprint

API Gateway + Lambda + DynamoDB für REST APIs
Perfekt für: Serverlose APIs, Microservices, MVP Backends
"""

from .base import (
    Blueprint,
    BlueprintCategory,
    BlueprintDifficulty,
    BlueprintFormField,
    BlueprintMetadata,
    CostEstimate,
    FieldType,
    FieldValidation,
    SelectOption,
)

SIMPLE_API = Blueprint(
    metadata=BlueprintMetadata(
        id="simple-api",
        name="Simple REST API",
        description="Serverlose REST API mit API Gateway, Lambda Functions und DynamoDB",
        category=BlueprintCategory.API,
        difficulty=BlueprintDifficulty.BEGINNER,
        estimated_cost=CostEstimate(
            min_usd=0.0,
            typical_usd=15.0,
            max_usd=100.0,
            breakdown={
                "API Gateway (1M requests)": 3.50,
                "Lambda (1M invocations, 512MB)": 8.33,
                "DynamoDB (25GB storage + 1M reads/writes)": 7.50,
                "CloudWatch Logs": 2.00,
            },
            assumptions=[
                "~1M API Requests pro Monat",
                "~256ms durchschnittliche Lambda-Laufzeit",
                "512MB Lambda Memory",
                "DynamoDB On-Demand Pricing",
                "25GB DynamoDB Daten",
            ],
        ),
        setup_time_minutes=15,
        use_cases=[
            "REST APIs für Web/Mobile Apps",
            "Serverlose Microservices",
            "Webhook Endpoints",
            "CRUD APIs für einfache Datenmodelle",
            "MVP Backends",
        ],
        features=[
            "Auto-Scaling (0 bis unbegrenzt)",
            "Pay-per-Use (keine Fixkosten)",
            "Integrierte CORS-Unterstützung",
            "API Keys & Usage Plans",
            "Request/Response Transformation",
            "CloudWatch Monitoring",
        ],
        limitations=[
            "Lambda Timeout max 15 Minuten",
            "API Gateway Timeout max 29 Sekunden",
            "Cold Starts (erste Anfrage langsam)",
            "Keine WebSocket-Unterstützung in diesem Blueprint (nutze 'serverless-app')",
        ],
        icon="api",
    ),
    form_schema=[
        BlueprintFormField(
            name="api_name",
            type=FieldType.TEXT,
            label="API Name",
            description="Name für deine API (z.B. 'my-api')",
            required=True,
            validation=FieldValidation(
                pattern=r"^[a-z0-9][a-z0-9-]{1,61}[a-z0-9]$",
            ),
        ),
        BlueprintFormField(
            name="lambda_runtime",
            type=FieldType.SELECT,
            label="Lambda Runtime",
            description="Programmiersprache für deine Lambda Functions",
            required=True,
            default="python3.11",
            validation=FieldValidation(
                options=[
                    SelectOption(value="nodejs20.x", label="Node.js 20"),
                    SelectOption(value="nodejs18.x", label="Node.js 18"),
                    SelectOption(value="python3.12", label="Python 3.12"),
                    SelectOption(value="python3.11", label="Python 3.11"),
                    SelectOption(value="python3.10", label="Python 3.10"),
                    SelectOption(value="java17", label="Java 17"),
                    SelectOption(value="dotnet8", label=".NET 8"),
                    SelectOption(value="go1.x", label="Go 1.x"),
                ],
            ),
        ),
        BlueprintFormField(
            name="lambda_memory_mb",
            type=FieldType.NUMBER,
            label="Lambda Memory (MB)",
            description="Mehr Memory = schneller aber teurer (128-10240 MB)",
            required=True,
            default=512,
            validation=FieldValidation(min=128, max=10240),
            constraints="aws.lambda.memory",
        ),
        BlueprintFormField(
            name="lambda_timeout_seconds",
            type=FieldType.NUMBER,
            label="Lambda Timeout (Sekunden)",
            description="Max Laufzeit pro Request (3-900 Sekunden)",
            required=True,
            default=30,
            validation=FieldValidation(min=3, max=900),
            constraints="aws.lambda.timeout",
        ),
        BlueprintFormField(
            name="dynamodb_table_name",
            type=FieldType.TEXT,
            label="DynamoDB Table Name",
            description="Name der DynamoDB Tabelle",
            required=True,
            validation=FieldValidation(
                pattern=r"^[a-zA-Z0-9_.-]{3,255}$",
            ),
        ),
        BlueprintFormField(
            name="dynamodb_billing_mode",
            type=FieldType.SELECT,
            label="DynamoDB Billing Mode",
            description="On-Demand (flexibel) oder Provisioned (günstiger bei konstanter Last)",
            required=True,
            default="PAY_PER_REQUEST",
            validation=FieldValidation(
                options=[
                    SelectOption(
                        value="PAY_PER_REQUEST",
                        label="On-Demand (Pay per Request)",
                        description="Gut für variable/unvorhersehbare Last",
                        price_factor=1.25,
                    ),
                    SelectOption(
                        value="PROVISIONED",
                        label="Provisioned Capacity",
                        description="Günstiger bei konstanter Last, erfordert Planung",
                        price_factor=1.0,
                    ),
                ],
            ),
        ),
        BlueprintFormField(
            name="enable_cors",
            type=FieldType.TOGGLE,
            label="CORS aktivieren",
            description="Erlaubt Browser-Zugriffe von anderen Domains",
            required=False,
            default=True,
        ),
        BlueprintFormField(
            name="api_key_required",
            type=FieldType.TOGGLE,
            label="API Key erforderlich",
            description="Schütze deine API mit API Keys",
            required=False,
            default=False,
        ),
        BlueprintFormField(
            name="enable_cloudwatch_logs",
            type=FieldType.TOGGLE,
            label="CloudWatch Logs aktivieren",
            description="Logging für Debugging (kostet ~$2/Monat bei 10GB Logs)",
            required=False,
            default=True,
        ),
    ],
    aws_resources=[
        "API Gateway",
        "Lambda",
        "DynamoDB",
        "IAM",
        "CloudWatch Logs",
    ],
    terraform_templates=[
        "blueprints/simple_api/lambda.tf.j2",
        "blueprints/simple_api/api_gateway.tf.j2",
        "blueprints/simple_api/dynamodb.tf.j2",
        "blueprints/simple_api/iam.tf.j2",
    ],
    deployment_guide="""
## Deployment Guide: Simple REST API

### 1. Lambda Code vorbereiten
Erstelle deine Lambda Function (Beispiel Python):

```python
# lambda_handler.py
import json
import boto3

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('YOUR_TABLE_NAME')

def lambda_handler(event, context):
    # GET /items
    if event['httpMethod'] == 'GET':
        response = table.scan()
        return {
            'statusCode': 200,
            'body': json.dumps(response['Items'])
        }

    # POST /items
    elif event['httpMethod'] == 'POST':
        item = json.loads(event['body'])
        table.put_item(Item=item)
        return {
            'statusCode': 201,
            'body': json.dumps({'message': 'Created'})
        }
```

### 2. Code deployen
```bash
# Zippe den Code
zip function.zip lambda_handler.py

# Upload zu Lambda
aws lambda update-function-code \\
  --function-name YOUR_FUNCTION_NAME \\
  --zip-file fileb://function.zip
```

### 3. API testen
```bash
# Mit curl
curl https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/prod/items

# Mit API Key (falls aktiviert)
curl -H "x-api-key: YOUR_API_KEY" \\
  https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/prod/items
```

### 4. CloudWatch Logs prüfen
```bash
aws logs tail /aws/lambda/YOUR_FUNCTION_NAME --follow
```

### Best Practices:
- Environment Variables für Secrets nutzen (nie hardcoden!)
- Lambda Layers für Dependencies (z.B. requests, boto3 updates)
- API Gateway Throttling konfigurieren (Schutz vor DDoS)
- CloudWatch Alarms für Errors einrichten
""",
)
