# Smart Form System

Intelligentes Formular-System mit Live-Validation und AWS-Constraint-Checking für OverCloud.

## Features

- **Live Validation** - Echtzeit-Validierung gegen Backend-APIs
- **AWS Constraints** - Kennt AWS Service Limits (RDS, EC2, VPC, Lambda, etc.)
- **Smart Feedback** - Errors, Warnings, Suggestions
- **Cost Estimation** - Zeigt geschätzte Kosten in Echtzeit
- **Field Dependencies** - Fields können aufeinander reagieren (z.B. RDS Engine → Storage Limits)
- **Type-Safe** - Validiert gegen AWS-spezifische Regeln

## Architektur

```
FormBuilder (Orchestrator)
├── SmartFormField (Base Class)
│   ├── NumberField
│   ├── StorageSizeField
│   ├── InstanceTypeField
│   └── CIDRField
└── Backend Validation API
    ├── /validate-storage
    ├── /validate-instance-type
    ├── /validate-cidr
    └── /validate-lambda
```

## Verwendung

### 1. Einfaches Beispiel

```javascript
import { FormBuilder } from './components/forms/FormBuilder.js';

const blueprint = {
    id: 'my-blueprint',
    name: 'Mein Blueprint',
    form_schema: [
        {
            name: 'storage_size',
            label: 'Storage Size',
            type: 'storage',
            serviceType: 'rds',
            unit: 'GB',
            default: 20,
            description: 'RDS Storage in GB',
            engine: 'mysql'
        },
        {
            name: 'instance_type',
            label: 'Instance Type',
            type: 'instance_type',
            default: 't3.micro',
            useCase: 'web-server'
        }
    ]
};

const formBuilder = new FormBuilder(blueprint);
const formElement = formBuilder.render();

document.getElementById('container').appendChild(formElement);
```

### 2. Validation

```javascript
// Validate all fields
const isValid = await formBuilder.validateAll();

if (isValid) {
    const data = formBuilder.getData();
    console.log('Form data:', data);
} else {
    const errors = formBuilder.getAllErrors();
    console.error('Errors:', errors);
}
```

### 3. Live Updates

```javascript
// Listen to field changes
formBuilder.onChange((field, allData) => {
    console.log(`${field.config.name} changed:`, field.getValue());
    
    // Update cost estimate
    updateCostEstimate(allData);
});
```

### 4. Field Dependencies

Fields können automatisch aufeinander reagieren:

```javascript
// Wenn RDS Engine sich ändert, wird Storage Field neu validiert
{
    name: 'rds_engine',
    type: 'select',
    options: [...]
}
// → Triggert automatisch Re-Validation von storage_size Field
```

## Field Types

### `storage`

Storage Size Field mit AWS Service Limits.

```javascript
{
    name: 'storage_size',
    label: 'Storage Size',
    type: 'storage',
    serviceType: 'rds',  // rds, ebs, s3
    unit: 'GB',          // GB, TB
    default: 20,
    engine: 'mysql'      // Nur für RDS
}
```

**Features:**
- Validiert gegen AWS RDS/EBS/S3 Limits
- Zeigt monatliche Kosten
- Gibt Warnungen für Production-Workloads

### `instance_type`

EC2/RDS Instance Type Selector mit Autocomplete.

```javascript
{
    name: 'instance_type',
    label: 'Instance Type',
    type: 'instance_type',
    default: 't3.micro',
    useCase: 'database'  // Optional: für Empfehlungen
}
```

**Features:**
- Dropdown mit allen Instance Types
- Zeigt vCPUs, RAM, Network, Preis
- Use-Case basierte Empfehlungen
- Live Cost Calculation

### `cidr`

VPC/Subnet CIDR Block Validator.

```javascript
{
    name: 'vpc_cidr',
    label: 'VPC CIDR Block',
    type: 'cidr',
    default: '10.0.0.0/16'
}
```

**Features:**
- Validiert CIDR Format
- Prüft AWS VPC Constraints (/16 - /28)
- Berechnet Total IPs und Usable IPs
- Zeigt AWS Reserved IPs (5 pro Subnet)

### `number`

Number Input mit Min/Max Validation.

```javascript
{
    name: 'timeout',
    label: 'Timeout (Sekunden)',
    type: 'number',
    default: 30,
    validation: {
        min: 1,
        max: 900
    },
    step: 1
}
```

### `text`, `email`, `url`

Standard Text Inputs mit Pattern Validation.

```javascript
{
    name: 'database_name',
    label: 'Database Name',
    type: 'text',
    default: 'mydb',
    validation: {
        required: true,
        pattern: '^[a-z0-9-]+$',
        minLength: 3,
        maxLength: 63
    }
}
```

### `select`

Dropdown/Select Field.

```javascript
{
    name: 'engine',
    label: 'Database Engine',
    type: 'select',
    default: 'mysql',
    options: [
        { value: 'mysql', label: 'MySQL 8.0' },
        { value: 'postgres', label: 'PostgreSQL 15' }
    ]
}
```

## Validation Response Format

Backend APIs geben folgendes Format zurück:

```json
{
    "valid": true,
    "errors": [],
    "warnings": ["Niedrige Memory-Konfiguration"],
    "suggestions": ["Erwäge R5-Instances für Datenbanken"],
    "metadata": {
        "estimated_monthly_cost_usd": 12.45,
        "vcpus": 2,
        "memory_gb": 8
    }
}
```

## Styling

Das System verwendet Tailwind CSS. Custom Styles in `css/components/smart-form.css`.

### Message Types

- **Errors** (rot) - Blocker, Field ist invalid
- **Warnings** (gelb) - Field ist valid, aber suboptimal
- **Suggestions** (blau) - Verbesserungsvorschläge
- **Cost** (grün) - Kostenindikator

## Backend Integration

### Required API Endpoints

```
POST /api/v1/validate-storage
POST /api/v1/validate-instance-type
POST /api/v1/validate-cidr
POST /api/v1/validate-lambda

GET /api/v1/instance-types
GET /api/v1/rds-engines
GET /api/v1/rds-instance-classes
```

Siehe `backend/app/api/validation.py` für Implementation.

## Erweiterung

### Neuer Field Type

1. Erstelle neue Class in `components/forms/`:

```javascript
import { SmartFormField } from './SmartFormField.js';

export class MyCustomField extends SmartFormField {
    async validate() {
        const result = await this.callValidationAPI('/validate-my-field', {
            value: this.value
        });
        
        this.errors = result.errors || [];
        this.warnings = result.warnings || [];
        
        return result.valid;
    }
}
```

2. Registriere in `FormBuilder.createField()`:

```javascript
case 'my_custom_type':
    field = new MyCustomField(config);
    break;
```

3. Erstelle Backend Validation Endpoint

## Beispiele

Siehe `examples/smart-form-demo.js` für komplette Beispiele:

- RDS Database Blueprint Form
- Lambda Function Blueprint Form

## Best Practices

1. **Validation Strategie**
   - Client-Side: Format, Required, Min/Max
   - Server-Side: AWS Constraints, Business Logic

2. **Performance**
   - Validation nur bei `blur`, nicht bei jedem `input`
   - Debounce für Live Cost Calculation

3. **UX**
   - Zeige Errors erst nach Blur/Submit
   - Warnings können immer sichtbar sein
   - Suggestions als Tooltips oder unterhalb

4. **Accessibility**
   - Labels immer vorhanden
   - Error-Messages mit `aria-describedby`
   - Keyboard-Navigation funktioniert

## Testing

```javascript
// Unit Tests
import { StorageSizeField } from './StorageSizeField.js';

test('validates RDS minimum storage', async () => {
    const field = new StorageSizeField({
        name: 'storage',
        serviceType: 'rds',
        engine: 'mysql'
    });
    
    field.setValue(10); // Unter Minimum (20 GB)
    const isValid = await field.validate();
    
    expect(isValid).toBe(false);
    expect(field.errors.length).toBeGreaterThan(0);
});
```

## Roadmap

- [ ] Lazy Loading für Instance Types (erst bei Focus)
- [ ] Caching von Validation Results
- [ ] Field-Level Permissions (Read-Only, Hidden)
- [ ] Multi-Step Forms (Wizard)
- [ ] Form State Persistence (LocalStorage)
- [ ] Undo/Redo Support
- [ ] Keyboard Shortcuts

## Troubleshooting

### Validation API nicht erreichbar

```javascript
// Check API_BASE_URL in SmartFormField.js
const API_BASE_URL = '/api/v1';
```

### Styling nicht geladen

```css
/* Prüfe ob smart-form.css in main.css importiert ist */
@import "./components/smart-form.css";
```

### Instance Types Dropdown leer

```javascript
// Prüfe ob API Response korrekt ist
const response = await fetch('/api/v1/instance-types');
const data = await response.json();
console.log(data);
```

## Support

Bei Problemen:
1. Check Browser Console
2. Check Network Tab (API Calls)
3. Prüfe Backend Logs
4. Siehe Beispiele in `examples/smart-form-demo.js`
