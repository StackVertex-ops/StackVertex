"""
Static Website Blueprint

S3 + CloudFront + Route53 für statische Websites
Perfekt für: Landing Pages, Dokumentation, Portfolios, Marketing Sites
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

STATIC_WEBSITE = Blueprint(
    metadata=BlueprintMetadata(
        id="static-website",
        name="Static Website",
        description="S3-hosted static website mit CloudFront CDN und optionaler Custom Domain",
        category=BlueprintCategory.STATIC,
        difficulty=BlueprintDifficulty.BEGINNER,
        estimated_cost=CostEstimate(
            min_usd=1.0,
            typical_usd=5.0,
            max_usd=20.0,
            breakdown={
                "S3 Storage (50GB)": 1.15,
                "CloudFront (1TB traffic)": 85.0,
                "Route53 Hosted Zone": 0.50,
                "Data Transfer": 10.0,
            },
            assumptions=[
                "~50GB gespeicherte Dateien",
                "~1TB Traffic pro Monat",
                "PriceClass_100 (USA + Europa)",
                "Standard S3 Storage Class",
            ],
        ),
        setup_time_minutes=10,
        use_cases=[
            "Landing Pages und Marketing Websites",
            "Technische Dokumentation (z.B. via MkDocs, Docusaurus)",
            "Portfolio Websites",
            "Event-Websites",
            "Product Launch Pages",
        ],
        features=[
            "HTTPS via CloudFront",
            "Global CDN Distribution",
            "Automatisches Caching",
            "Custom Domain Support (optional)",
            "Index.html Routing",
            "Gzip/Brotli Compression",
        ],
        limitations=[
            "Keine serverseitige Logik (nur statische Dateien)",
            "Kein Backend oder Datenbank",
            "CloudFront Propagation dauert ~15-20 Minuten",
        ],
        icon="web",
    ),
    form_schema=[
        BlueprintFormField(
            name="website_name",
            type=FieldType.TEXT,
            label="Website Name",
            description="Name für deine Website (wird in S3 Bucket Name verwendet)",
            required=True,
            validation=FieldValidation(
                pattern=r"^[a-z0-9][a-z0-9-]{1,61}[a-z0-9]$",
            ),
        ),
        BlueprintFormField(
            name="domain_name",
            type=FieldType.TEXT,
            label="Custom Domain (optional)",
            description="z.B. www.example.com - leer lassen für CloudFront-URL",
            required=False,
            default=None,
            validation=FieldValidation(
                pattern=r"^([a-z0-9]+(-[a-z0-9]+)*\.)+[a-z]{2,}$",
            ),
        ),
        BlueprintFormField(
            name="cloudfront_price_class",
            type=FieldType.SELECT,
            label="CloudFront Price Class",
            description="Wo soll deine Website schnell sein?",
            required=True,
            default="PriceClass_100",
            validation=FieldValidation(
                options=[
                    SelectOption(
                        value="PriceClass_All",
                        label="Weltweit (alle Edge Locations)",
                        description="Beste Performance global, höchste Kosten",
                        price_factor=1.5,
                    ),
                    SelectOption(
                        value="PriceClass_200",
                        label="USA, Europa, Asien, Naher Osten, Afrika",
                        description="Gute globale Abdeckung",
                        price_factor=1.2,
                    ),
                    SelectOption(
                        value="PriceClass_100",
                        label="USA, Europa (günstigste)",
                        description="Gut für westliche Zielgruppe",
                        price_factor=1.0,
                    ),
                ],
            ),
        ),
        BlueprintFormField(
            name="enable_versioning",
            type=FieldType.TOGGLE,
            label="S3 Versioning aktivieren",
            description="Behalte alte Versionen deiner Dateien (Rollback möglich)",
            required=False,
            default=False,
        ),
        BlueprintFormField(
            name="index_document",
            type=FieldType.TEXT,
            label="Index Document",
            description="Standard-Datei (meist index.html)",
            required=True,
            default="index.html",
        ),
        BlueprintFormField(
            name="error_document",
            type=FieldType.TEXT,
            label="Error Document",
            description="Fehlerseite (z.B. 404.html)",
            required=False,
            default="404.html",
        ),
        BlueprintFormField(
            name="enable_compression",
            type=FieldType.TOGGLE,
            label="Compression aktivieren",
            description="CloudFront komprimiert Dateien automatisch (Gzip/Brotli)",
            required=False,
            default=True,
        ),
    ],
    aws_resources=[
        "S3",
        "CloudFront",
        "Route53",
        "ACM",  # für HTTPS Certificate
    ],
    terraform_templates=[
        "blueprints/static_website/s3.tf.j2",
        "blueprints/static_website/cloudfront.tf.j2",
        "blueprints/static_website/route53.tf.j2",
        "blueprints/static_website/acm.tf.j2",
    ],
    deployment_guide="""
## Deployment Guide: Static Website

### 1. Dateien hochladen
Nach dem Terraform Apply:
```bash
aws s3 sync ./build s3://your-bucket-name/ --delete
```

### 2. CloudFront Cache invalidieren
```bash
aws cloudfront create-invalidation \\
  --distribution-id YOUR_DISTRIBUTION_ID \\
  --paths "/*"
```

### 3. DNS konfigurieren (bei Custom Domain)
Erstelle einen CNAME Record bei deinem DNS Provider:
```
CNAME www.example.com -> d111111abcdef8.cloudfront.net
```

### 4. Fertig!
Deine Website ist jetzt live unter:
- CloudFront URL: https://d111111abcdef8.cloudfront.net
- Custom Domain: https://www.example.com (wenn konfiguriert)

### Tipps:
- Cache-Control Headers setzen für bessere Performance
- CloudFront Invalidation kostet Geld (erste 1000 Pfade/Monat gratis)
- S3 Lifecycle Rules nutzen für alte Versionen
""",
)
