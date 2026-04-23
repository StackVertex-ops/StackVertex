# JSON Schema Validation API - Beispiele

## Übersicht

Die Validation API ermöglicht es, Architekturdefinitionen gegen das OverCloud JSON Schema zu validieren.

## Endpoints

### Health Check

**GET** `/api/v1/validate/health`

Prüft ob der Validation Service funktioniert und das Schema geladen werden kann.

```bash
curl http://localhost:8000/api/v1/validate/health
```

**Response:**
```json
{
  "status": "healthy",
  "schema_loaded": true,
  "schema_version": "https://overcloud.io/schemas/architecture/v1.0.0",
  "schema_title": "OverCloud Architecture Definition"
}
```

---

### Validate Architecture

**POST** `/api/v1/validate/architecture`

Validiert eine JSON-Architekturdefinition gegen das OverCloud Schema v1.0.0.

#### Erfolgreiche Validierung

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/validate/architecture \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "version": "1.0.0",
      "metadata": {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "name": "Test Architecture",
        "provider": "aws",
        "created_at": "2024-03-24T10:00:00Z",
        "updated_at": "2024-03-24T10:00:00Z"
      },
      "requirements": {},
      "architecture": {
        "components": [],
        "relationships": []
      }
    }
  }'
```

**Response:**
```json
{
  "valid": true,
  "message": "Validierung erfolgreich",
  "errors": [],
  "error_count": 0
}
```

#### Fehlgeschlagene Validierung

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/validate/architecture \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "version": "invalid-version",
      "metadata": {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "name": "",
        "provider": "invalid-provider",
        "created_at": "2024-03-24T10:00:00Z",
        "updated_at": "2024-03-24T10:00:00Z"
      },
      "requirements": {},
      "architecture": {
        "components": [],
        "relationships": []
      }
    }
  }'
```

**Response:**
```json
{
  "valid": false,
  "message": "Validierung fehlgeschlagen",
  "errors": [
    {
      "message": "'invalid-version' does not match '^\\d+\\.\\d+\\.\\d+$'",
      "path": "$.version",
      "schema_path": "$.properties.version.pattern",
      "validator": "pattern",
      "validator_value": "^\\d+\\.\\d+\\.\\d+$",
      "context": null
    },
    {
      "message": "'' should be non-empty",
      "path": "$.metadata.name",
      "schema_path": "$.properties.metadata.properties.name.minLength",
      "validator": "minLength",
      "validator_value": 1,
      "context": null
    },
    {
      "message": "'invalid-provider' is not one of ['aws', 'azure', 'gcp']",
      "path": "$.metadata.provider",
      "schema_path": "$.properties.metadata.properties.provider.enum",
      "validator": "enum",
      "validator_value": ["aws", "azure", "gcp"],
      "context": null
    }
  ],
  "error_count": 3
}
```

## Error Response Format

Jeder Validierungsfehler enthält folgende Felder:

- **message**: Lesbare Fehlerbeschreibung
- **path**: JSON-Pfad zum fehlerhaften Feld (z.B. `$.metadata.name`)
- **schema_path**: Pfad zur Constraint im Schema
- **validator**: Name des Validators der fehlgeschlagen ist (z.B. `pattern`, `enum`, `required`)
- **validator_value**: Erwarteter Wert oder Constraint
- **context**: Optionaler zusätzlicher Kontext bei verschachtelten Fehlern

## Integration in andere Anwendungen

### Python

```python
import requests

data = {
    "data": {
        "version": "1.0.0",
        "metadata": {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "name": "My Architecture",
            "provider": "aws",
            "created_at": "2024-03-24T10:00:00Z",
            "updated_at": "2024-03-24T10:00:00Z"
        },
        "requirements": {},
        "architecture": {
            "components": [],
            "relationships": []
        }
    }
}

response = requests.post(
    "http://localhost:8000/api/v1/validate/architecture",
    json=data
)

result = response.json()

if result["valid"]:
    print("✓ Validierung erfolgreich")
else:
    print(f"✗ Validierung fehlgeschlagen: {result['error_count']} Fehler")
    for error in result["errors"]:
        print(f"  - {error['path']}: {error['message']}")
```

### JavaScript/TypeScript

```typescript
const data = {
  data: {
    version: "1.0.0",
    metadata: {
      id: "123e4567-e89b-12d3-a456-426614174000",
      name: "My Architecture",
      provider: "aws",
      created_at: "2024-03-24T10:00:00Z",
      updated_at: "2024-03-24T10:00:00Z"
    },
    requirements: {},
    architecture: {
      components: [],
      relationships: []
    }
  }
};

const response = await fetch("http://localhost:8000/api/v1/validate/architecture", {
  method: "POST",
  headers: {
    "Content-Type": "application/json"
  },
  body: JSON.stringify(data)
});

const result = await response.json();

if (result.valid) {
  console.log("✓ Validierung erfolgreich");
} else {
  console.log(`✗ Validierung fehlgeschlagen: ${result.error_count} Fehler`);
  result.errors.forEach(error => {
    console.log(`  - ${error.path}: ${error.message}`);
  });
}
```

## API Dokumentation

Die vollständige API-Dokumentation ist verfügbar unter:

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **OpenAPI JSON**: http://localhost:8000/api/openapi.json
