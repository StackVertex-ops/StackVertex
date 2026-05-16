# Blueprint Architecture Builder - Integration Documentation

## Überblick

Der Blueprint Architecture Builder ist ein 3-Step-Wizard, der Blueprints mit Smart Forms integriert und User durch den Prozess führt:

1. **Blueprint Selection** - User wählt vorkonfigurierte Architektur
2. **Configuration** - Smart Forms für Blueprint-Parameter + Live Cost Estimation
3. **Review & Deploy** - Zusammenfassung, Terraform Preview, Deployment

## Dateien

### Frontend

#### HTML
- `/blueprint-architecture-builder.html` - Hauptseite mit allen 3 Steps

#### JavaScript
- `/js/pages/blueprint-builder.js` - Main Logic Class `BlueprintArchitectureBuilder`
- `/js/components/forms/FormBuilder.js` - Orchestriert Smart Form Fields
- `/js/components/forms/SmartFormField.js` - Basis-Field mit Validation
- `/js/components/forms/NumberField.js` - Numeric Input mit Bounds
- `/js/components/forms/StorageSizeField.js` - Storage mit Unit Conversion
- `/js/components/forms/InstanceTypeField.js` - EC2/RDS Instance Selector
- `/js/components/forms/CIDRField.js` - CIDR Notation mit Validation

#### CSS
- `/css/components/step-indicator.css` - Step Progress UI
- `/css/components/architecture-builder.css` - Builder-spezifische Styles
- `/css/main.css` - Importiert alle Component Styles

### Backend

#### API Endpoints
- `/api/v1/blueprints` - Liste aller Blueprints
- `/api/v1/blueprints/{id}` - Einzelner Blueprint mit `form_schema`
- `/api/v1/costs/estimate-blueprint` - Kostenberechnung (POST)
- `/api/v1/terraform/generate` - Terraform Code Generierung (POST)
- `/api/v1/deployments` - Deployment starten (POST)

#### Services
- `/app/services/terraform_generator.py` - Jinja2-basierte Terraform-Generierung
- `/app/services/cost_calculator.py` - Blueprint Cost Calculation

#### Templates
- `/templates/terraform/{blueprint_id}.tf.j2` - Jinja2 Templates für Terraform HCL

## Flow

### 1. Blueprint Selection

User kommt auf die Seite:
- **Von Blueprints-Seite**: `?blueprint={id}` in URL → direkt zu Step 2
- **Direkter Aufruf**: Lädt alle Blueprints und zeigt Grid

```javascript
// blueprints.js Link
onclick="window.location.href='/blueprint-architecture-builder.html?blueprint=${metadata.id}'"
```

### 2. Configuration

FormBuilder initialisiert sich aus `blueprint.form_schema`:

```json
{
  "form_schema": [
    {
      "name": "bucket_name",
      "type": "text",
      "label": "Bucket Name",
      "required": true,
      "validation": {
        "pattern": "^[a-z0-9-]+$"
      }
    },
    {
      "name": "storage_size",
      "type": "storage",
      "label": "Storage Size",
      "default": 20,
      "unit": "GB"
    }
  ]
}
```

**Live Cost Calculation:**
- Bei jedem Field-Change → API Call zu `/costs/estimate-blueprint`
- Response wird in Cost Panel gerendert
- Breakdown nach Services + Total

### 3. Review & Deploy

- **Validation**: `formBuilder.validateAll()` vor Navigation
- **Terraform Generation**: API Call zu `/terraform/generate`
- **Summary**: Zeigt alle User-Inputs + Kosten
- **Terraform Preview**: Syntax-Highlighted HCL Code
- **Actions**:
  - Download Terraform (`.tf` File)
  - Copy to Clipboard
  - Deploy (startet Deployment-Prozess)

## API Contracts

### POST /api/v1/costs/estimate-blueprint

**Request:**
```json
{
  "blueprint_id": "static-website",
  "configuration": {
    "bucket_name": "my-website",
    "region": "eu-central-1",
    "enable_cdn": true,
    "storage_size": 50
  }
}
```

**Response:**
```json
{
  "items": [
    {
      "service": "S3 Storage",
      "resource": "s3://my-website",
      "amount": 1.15,
      "unit": "50 GB/month",
      "quantity": 50,
      "total": 1.15
    },
    {
      "service": "CloudFront",
      "resource": "CDN Distribution",
      "amount": 85.0,
      "unit": "1 TB traffic",
      "quantity": 1024,
      "total": 85.0
    }
  ],
  "subtotal": 86.15,
  "tax": 0.0,
  "total": 86.15,
  "currency": "USD",
  "period": "monthly"
}
```

### POST /api/v1/terraform/generate

**Request:**
```json
{
  "blueprint_id": "static-website",
  "configuration": {
    "bucket_name": "my-website",
    "region": "eu-central-1",
    "enable_cdn": true
  }
}
```

**Response:**
```json
{
  "terraform_code": "terraform {\n  required_version = \">= 1.0\"\n...",
  "blueprint_id": "static-website",
  "generated_at": "2026-05-16T10:30:00Z"
}
```

## Terraform Templates

Templates liegen in `/backend/templates/terraform/{blueprint_id}.tf.j2`.

**Jinja2 Features:**
- Variable Substitution: `{{ bucket_name }}`
- Conditionals: `{% if enable_cdn %}...{% endif %}`
- Filters: `{{ bucket_name | to_kebab_case }}`
- Loops: `{% for item in items %}...{% endfor %}`

**Beispiel:**
```jinja2
resource "aws_s3_bucket" "website" {
  bucket = "{{ bucket_name | to_kebab_case }}"

  tags = {
    Name = "{{ bucket_name }}"
    ManagedBy = "OverCloud"
  }
}

{% if enable_cdn %}
resource "aws_cloudfront_distribution" "website" {
  enabled = true
  # ...
}
{% endif %}
```

## Validation

### Frontend (Smart Forms)

Jedes Field validiert sich selbst:
- **Required**: `field.config.required`
- **Pattern**: `field.config.validation.pattern`
- **Min/Max**: `field.config.validation.min/max`
- **Custom**: `field.config.validation.custom`

```javascript
async validate() {
    this.clearMessages();

    if (this.config.required && !this.getValue()) {
        this.addError('Dieses Feld ist erforderlich');
        return false;
    }

    // Pattern validation
    if (this.config.validation?.pattern) {
        const pattern = new RegExp(this.config.validation.pattern);
        if (!pattern.test(this.getValue())) {
            this.addError(this.config.validation.message || 'Ungültiges Format');
            return false;
        }
    }

    return true;
}
```

### Backend

- **Blueprint Config Validation**: Schema-basiert
- **Terraform Validation**: Basic Syntax Checks (TODO: `terraform fmt -check`)
- **Cost Calculation**: Bounds Checks für Inputs

## Erweiterung um neue Blueprints

### 1. Blueprint JSON erstellen

```json
{
  "metadata": {
    "id": "my-new-blueprint",
    "name": "My New Blueprint",
    "category": "webapp",
    "difficulty": "intermediate"
  },
  "form_schema": [
    {
      "name": "instance_type",
      "type": "instance_type",
      "label": "EC2 Instance Type",
      "required": true,
      "use_case": "web"
    }
  ]
}
```

### 2. Terraform Template erstellen

`/backend/templates/terraform/my-new-blueprint.tf.j2`:

```jinja2
resource "aws_instance" "app" {
  ami           = "ami-123456"
  instance_type = "{{ instance_type }}"

  tags = {
    Name = "{{ app_name }}"
  }
}
```

### 3. Cost Calculation Logic

In `/app/services/cost_calculator.py`:

```python
def calculate_my_new_blueprint_cost(config):
    # EC2 Instance Cost
    instance_cost = get_ec2_pricing(config['instance_type'], config['region'])

    return CostBreakdown(
        items=[
            CostItem(
                service="EC2",
                resource=config['instance_type'],
                amount=instance_cost,
                unit="per hour"
            )
        ],
        total=instance_cost * 730  # monthly
    )
```

### 4. Backend registrieren

In `/app/data/blueprints/my-new-blueprint.json` speichern.

## Testing

### Frontend

```bash
cd frontend
npm run dev
```

Öffne `http://localhost:5173/blueprint-architecture-builder.html?blueprint=static-website`

### Backend

```bash
cd backend
poetry run uvicorn app.main:app --reload
```

Test Endpoints:
```bash
# Get Blueprint
curl http://localhost:8000/api/v1/blueprints/static-website

# Estimate Costs
curl -X POST http://localhost:8000/api/v1/costs/estimate-blueprint \
  -H "Content-Type: application/json" \
  -d '{
    "blueprint_id": "static-website",
    "configuration": {"bucket_name": "test", "region": "eu-central-1"}
  }'

# Generate Terraform
curl -X POST http://localhost:8000/api/v1/terraform/generate \
  -H "Content-Type: application/json" \
  -d '{
    "blueprint_id": "static-website",
    "configuration": {"bucket_name": "test", "region": "eu-central-1"}
  }'
```

## Troubleshooting

### "Blueprint not found"
- Prüfe ob `/app/data/blueprints/{id}.json` existiert
- Prüfe ob Blueprint-ID korrekt ist

### "Template not found"
- Prüfe ob `/backend/templates/terraform/{id}.tf.j2` existiert
- Prüfe Dateiname-Matching (Underscores vs. Hyphens)

### Cost Calculation Fehler
- Prüfe ob alle required Fields im `configuration` Object sind
- Prüfe Backend Logs für Details

### Form Validation schlägt fehl
- Console öffnen und `formBuilder.getAllErrors()` prüfen
- Jedes Field einzeln mit `field.validate()` testen

## Best Practices

1. **Immer Validation vor API Calls**
   ```javascript
   if (await formBuilder.validateAll()) {
       // Make API call
   }
   ```

2. **Loading States zeigen**
   ```javascript
   this.showCostLoading();
   try {
       await updateCostEstimate();
   } finally {
       this.hideCostLoading();
   }
   ```

3. **Error Handling**
   ```javascript
   try {
       const response = await fetch(...);
       if (!response.ok) throw new Error(`HTTP ${response.status}`);
   } catch (error) {
       console.error('Fehler:', error);
       showErrorMessage(error.message);
   }
   ```

4. **Terraform Templates sauber halten**
   - Kommentare für Sections
   - Consistent Naming (snake_case für Resources)
   - Tags immer setzen (ManagedBy: OverCloud)

---

**Zuletzt aktualisiert:** 2026-05-16
