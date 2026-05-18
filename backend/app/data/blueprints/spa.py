"""
Single Page Application (SPA) Blueprint

S3 + CloudFront + API Gateway + Lambda für moderne Web Apps
Perfekt für: React, Vue, Angular Apps mit serverless Backend
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

SPA = Blueprint(
    metadata=BlueprintMetadata(
        id="spa",
        name="Single Page Application (SPA)",
        description="Serverlose SPA mit S3 Frontend, CloudFront CDN und Lambda Backend API",
        category=BlueprintCategory.WEBAPP,
        difficulty=BlueprintDifficulty.BEGINNER,
        estimated_cost=CostEstimate(
            min_usd=2.0,
            typical_usd=25.0,
            max_usd=150.0,
            breakdown={
                "S3 Storage (10GB Frontend)": 0.23,
                "CloudFront (1TB traffic)": 85.0,
                "API Gateway (5M requests)": 17.50,
                "Lambda (5M invocations, 512MB)": 41.65,
                "DynamoDB (10GB + 5M reads/writes)": 15.00,
                "Route53 Hosted Zone": 0.50,
            },
            assumptions=[
                "~10GB Frontend Assets",
                "~1TB CloudFront Traffic pro Monat",
                "~5M API Requests pro Monat",
                "512MB Lambda Memory, ~200ms Runtime",
                "DynamoDB On-Demand Pricing",
            ],
        ),
        setup_time_minutes=15,
        use_cases=[
            "React/Vue/Angular Single Page Applications",
            "Progressive Web Apps (PWA)",
            "Dashboards & Admin Panels",
            "SaaS Frontends mit serverless Backend",
            "Mobile App Backends (REST API)",
        ],
        features=[
            "Vollständig serverless (keine Server zu managen)",
            "Auto-Scaling (Frontend & Backend)",
            "Global CDN Distribution",
            "HTTPS inklusive",
            "API Gateway mit CORS-Unterstützung",
            "DynamoDB für Datenspeicherung",
            "Pay-per-Use (niedrige Kosten bei wenig Traffic)",
        ],
        limitations=[
            "Lambda Cold Starts (~300ms bei erster Anfrage)",
            "API Gateway Timeout max 29 Sekunden",
            "Kein WebSocket in diesem Blueprint (nutze 'serverless-app')",
            "DynamoDB NoSQL (kein SQL/Joins)",
        ],
        icon="spa",
    ),
    form_schema=[
        BlueprintFormField(
            name="app_name",
            type=FieldType.TEXT,
            label="App Name",
            description="Name deiner SPA (z.B. 'my-dashboard')",
            required=True,
            validation=FieldValidation(
                pattern=r"^[a-z0-9][a-z0-9-]{1,61}[a-z0-9]$",
            ),
        ),
        BlueprintFormField(
            name="domain_name",
            type=FieldType.TEXT,
            label="Domain Name",
            description="z.B. app.example.com",
            required=True,
            validation=FieldValidation(
                pattern=r"^([a-z0-9]+(-[a-z0-9]+)*\.)+[a-z]{2,}$",
            ),
        ),
        BlueprintFormField(
            name="frontend_framework",
            type=FieldType.SELECT,
            label="Frontend Framework",
            description="Welches Framework nutzt du?",
            required=True,
            default="react",
            validation=FieldValidation(
                options=[
                    SelectOption(value="react", label="React"),
                    SelectOption(value="vue", label="Vue.js"),
                    SelectOption(value="angular", label="Angular"),
                    SelectOption(value="svelte", label="Svelte"),
                    SelectOption(value="nextjs", label="Next.js (Static Export)"),
                ],
            ),
        ),
        BlueprintFormField(
            name="api_lambda_runtime",
            type=FieldType.SELECT,
            label="Backend Runtime",
            description="Programmiersprache für Lambda Backend",
            required=True,
            default="nodejs20.x",
            validation=FieldValidation(
                options=[
                    SelectOption(value="nodejs20.x", label="Node.js 20 (empfohlen für JS Frontends)"),
                    SelectOption(value="python3.12", label="Python 3.12"),
                    SelectOption(value="python3.11", label="Python 3.11"),
                ],
            ),
        ),
        BlueprintFormField(
            name="lambda_memory_mb",
            type=FieldType.NUMBER,
            label="Lambda Memory (MB)",
            description="512MB ist ein guter Start (128-3008 MB)",
            required=True,
            default=512,
            validation=FieldValidation(min=128, max=3008),
            constraints="aws.lambda.memory",
        ),
        BlueprintFormField(
            name="cloudfront_price_class",
            type=FieldType.SELECT,
            label="CloudFront Price Class",
            description="Wo sind deine Nutzer?",
            required=True,
            default="PriceClass_100",
            validation=FieldValidation(
                options=[
                    SelectOption(
                        value="PriceClass_All",
                        label="Weltweit",
                        description="Beste Performance global",
                        price_factor=1.5,
                    ),
                    SelectOption(
                        value="PriceClass_200",
                        label="USA, Europa, Asien",
                        price_factor=1.2,
                    ),
                    SelectOption(
                        value="PriceClass_100",
                        label="USA, Europa",
                        price_factor=1.0,
                    ),
                ],
            ),
        ),
        BlueprintFormField(
            name="enable_auth",
            type=FieldType.TOGGLE,
            label="Cognito Authentication aktivieren",
            description="User Registration/Login mit AWS Cognito",
            required=False,
            default=False,
        ),
        BlueprintFormField(
            name="enable_cicd",
            type=FieldType.TOGGLE,
            label="CI/CD Pipeline aktivieren",
            description="Automatisches Deployment via GitHub Actions",
            required=False,
            default=True,
        ),
    ],
    aws_resources=[
        "S3",
        "CloudFront",
        "API Gateway",
        "Lambda",
        "DynamoDB",
        "Route53",
        "ACM",
        "Cognito (optional)",
        "CodePipeline (optional)",
    ],
    terraform_templates=[
        "blueprints/spa/s3_frontend.tf.j2",
        "blueprints/spa/cloudfront.tf.j2",
        "blueprints/spa/api_gateway.tf.j2",
        "blueprints/spa/lambda.tf.j2",
        "blueprints/spa/dynamodb.tf.j2",
        "blueprints/spa/route53.tf.j2",
        "blueprints/spa/cognito.tf.j2",
        "blueprints/spa/cicd.tf.j2",
    ],
    deployment_guide="""
## Deployment Guide: Single Page Application (SPA)

### 1. Frontend builden & deployen

#### React Example:
```bash
# Build production bundle
npm run build
# oder: yarn build

# Deploy zu S3
aws s3 sync build/ s3://YOUR_BUCKET_NAME/ --delete

# CloudFront Cache invalidieren
aws cloudfront create-invalidation \\
  --distribution-id YOUR_DISTRIBUTION_ID \\
  --paths "/*"
```

#### Vue.js Example:
```bash
npm run build
aws s3 sync dist/ s3://YOUR_BUCKET_NAME/ --delete
```

### 2. Backend API deployen

#### Node.js Lambda:
```javascript
// handler.js
export const handler = async (event) => {
  const { httpMethod, path, body } = event;

  // CORS Headers
  const headers = {
    'Access-Control-Allow-Origin': 'https://YOUR_DOMAIN',
    'Content-Type': 'application/json',
  };

  // GET /api/items
  if (httpMethod === 'GET' && path === '/api/items') {
    // DynamoDB Query...
    return {
      statusCode: 200,
      headers,
      body: JSON.stringify({ items: [...] }),
    };
  }

  // POST /api/items
  if (httpMethod === 'POST' && path === '/api/items') {
    const data = JSON.parse(body);
    // DynamoDB PutItem...
    return {
      statusCode: 201,
      headers,
      body: JSON.stringify({ message: 'Created' }),
    };
  }

  return {
    statusCode: 404,
    headers,
    body: JSON.stringify({ error: 'Not Found' }),
  };
};
```

```bash
# Deploy Lambda
zip function.zip handler.js
aws lambda update-function-code \\
  --function-name YOUR_FUNCTION_NAME \\
  --zip-file fileb://function.zip
```

### 3. Environment Variables konfigurieren

#### Frontend (.env):
```bash
REACT_APP_API_URL=https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/prod
REACT_APP_COGNITO_USER_POOL_ID=us-east-1_ABC123
REACT_APP_COGNITO_CLIENT_ID=abc123def456
```

#### Backend (Lambda Environment Variables):
```bash
aws lambda update-function-configuration \\
  --function-name YOUR_FUNCTION_NAME \\
  --environment Variables="{DYNAMODB_TABLE=your-table,CORS_ORIGIN=https://YOUR_DOMAIN}"
```

### 4. CI/CD mit GitHub Actions

`.github/workflows/deploy.yml`:
```yaml
name: Deploy SPA

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node
        uses: actions/setup-node@v3
        with:
          node-version: 20

      - name: Install & Build
        run: |
          npm install
          npm run build

      - name: Deploy to S3
        run: |
          aws s3 sync build/ s3://${{ secrets.S3_BUCKET }}/ --delete
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          AWS_REGION: us-east-1

      - name: Invalidate CloudFront
        run: |
          aws cloudfront create-invalidation \\
            --distribution-id ${{ secrets.CLOUDFRONT_ID }} \\
            --paths "/*"
```

### 5. Cognito Authentication Setup (optional)

#### Frontend Integration (React):
```bash
npm install aws-amplify
```

```javascript
// App.js
import { Amplify } from 'aws-amplify';

Amplify.configure({
  Auth: {
    region: 'us-east-1',
    userPoolId: 'us-east-1_ABC123',
    userPoolWebClientId: 'abc123def456',
  }
});

// Login Component
import { signIn } from 'aws-amplify/auth';

async function handleLogin(email, password) {
  await signIn({ username: email, password });
}
```

### 6. Testing

```bash
# Frontend lokal testen
npm start

# API Gateway testen
curl https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/prod/api/items

# Mit Auth Header (Cognito)
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \\
  https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/prod/api/items
```

### 7. Monitoring

CloudWatch Dashboards:
- **Frontend:** CloudFront Requests, Bytes Downloaded, Error Rate
- **Backend:** Lambda Invocations, Duration, Errors, Throttles
- **Database:** DynamoDB Read/Write Capacity, Throttles

### Best Practices:

**Frontend:**
- Code Splitting (React.lazy, Vue Async Components)
- Asset Optimization (Webpack Bundle Analyzer)
- Service Worker für Offline Support
- Lighthouse Score > 90

**Backend:**
- Lambda Layer für Dependencies (reduziert Deployment Size)
- DynamoDB Single Table Design
- API Gateway Caching für GET Requests
- CloudWatch Alarms für Errors

**Security:**
- CloudFront mit WAF (Web Application Firewall)
- API Gateway API Keys + Usage Plans
- Cognito MFA aktivieren
- Secrets in AWS Secrets Manager

### Troubleshooting:

**CORS Errors:**
- Prüfe API Gateway CORS Settings
- Lambda muss CORS Headers zurückgeben
- Preflight OPTIONS Requests aktivieren

**CloudFront zeigt alte Version:**
- Cache Invalidation erstellen (siehe oben)
- Oder: Cache-Control Headers im Build setzen

**Lambda Cold Starts:**
- Provisioned Concurrency aktivieren (+Kosten)
- Lambda Memory erhöhen (schnellere CPU)
- Keep-Alive mit CloudWatch Events (alle 5min trigger)

**Build-Fehler:**
- Node Modules cache leeren: `rm -rf node_modules && npm install`
- Prüfe .env Variablen
""",
)
