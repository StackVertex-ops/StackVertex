# Voucher API Documentation

**Version:** 1.0.0  
**Base URL:** `/api/v1`  
**Authentication:** JWT Bearer Token (alle Endpoints)

---

## Übersicht

Die Voucher API ermöglicht:
- **Public Endpoints:** Voucher validieren, einlösen, entfernen (Authenticated Users)
- **Admin Endpoints:** Voucher erstellen, verwalten, Stats abrufen (SuperAdmin only)

---

## Public Endpoints

### 1. Validate Voucher

Validiert ob ein Voucher-Code gültig und verwendbar ist.

**Endpoint:**
```
POST /api/v1/voucher/validate
```

**Headers:**
```
Authorization: Bearer {jwt_token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "code": "FRIEND2026"
}
```

**Response (200 OK - Valid):**
```json
{
  "valid": true,
  "code": "FRIEND2026",
  "discount_type": "percentage",
  "discount_value": 50,
  "applies_to": "both",
  "remaining_uses": 58,
  "message": "Voucher is valid and can be used"
}
```

**Response (400 Bad Request - Invalid):**
```json
{
  "detail": "Voucher expired on 2026-01-01"
}
```

**Mögliche Fehler:**
- `404 Not Found`: Voucher existiert nicht
- `400 Bad Request`: 
  - "Voucher is inactive"
  - "Voucher expired on {date}"
  - "Voucher has not started yet"
  - "Voucher usage limit reached"
  - "You have already used this voucher"

**Rate Limit:** 10 Requests/Minute

---

### 2. Redeem Voucher

Löst einen Voucher-Code ein und wendet ihn auf eine Subscription an.

**Endpoint:**
```
POST /api/v1/voucher/redeem
```

**Headers:**
```
Authorization: Bearer {jwt_token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "code": "FRIEND2026",
  "org_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Voucher FRIEND2026 successfully applied to subscription",
  "voucher_code": "FRIEND2026",
  "org_id": "550e8400-e29b-41d4-a716-446655440000",
  "subscription": {
    "id": "sub-550e8400-e29b-41d4-a716-446655440000",
    "tier": "pro",
    "base_price": 50.0,
    "aws_markup_percentage": 0.10,
    "voucher_code": "FRIEND2026",
    "voucher_discount_type": "percentage",
    "voucher_discount_value": 50,
    "voucher_applies_to": "both",
    "voucher_redeemed_at": "2026-05-17T10:30:00Z"
  }
}
```

**Response (400 Bad Request):**
```json
{
  "detail": "Subscription already has a voucher. Remove it first."
}
```

**Mögliche Fehler:**
- `404 Not Found`: Subscription nicht gefunden
- `403 Forbidden`: User ist kein Member der Organisation
- `400 Bad Request`: 
  - Alle Validation-Fehler von `/validate`
  - "Subscription already has a voucher"
  - "Voucher usage limit reached"

**Nebenwirkungen:**
- `voucher.current_uses` wird inkrementiert
- `voucher.used_by` Array wird um `user_id` erweitert
- Subscription wird mit Voucher-Details aktualisiert
- Audit Log Event: `voucher.redeem`

**Rate Limit:** 5 Requests/Minute

---

### 3. Remove Voucher

Entfernt einen Voucher von einer Subscription.

**Endpoint:**
```
DELETE /api/v1/voucher/remove/{org_id}
```

**Headers:**
```
Authorization: Bearer {jwt_token}
```

**Path Parameters:**
- `org_id` (UUID): Organisation ID

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Voucher removed from subscription"
}
```

**Response (404 Not Found):**
```json
{
  "detail": "Subscription not found"
}
```

**Mögliche Fehler:**
- `404 Not Found`: Subscription nicht gefunden
- `403 Forbidden`: User ist kein Member der Organisation
- `400 Bad Request`: "No voucher to remove"

**Nebenwirkungen:**
- Subscription: `voucher_code`, `voucher_*` Felder werden auf `null` gesetzt
- Audit Log Event: `voucher.remove`
- **Wichtig:** `voucher.current_uses` wird NICHT dekrementiert (Redemption bleibt bestehen)

**Rate Limit:** 5 Requests/Minute

---

## Admin Endpoints

Alle Admin-Endpoints erfordern **SuperAdmin-Rolle** (`system_role = "superadmin"`).

### 4. Create Voucher

Erstellt einen neuen Voucher.

**Endpoint:**
```
POST /api/v1/admin/vouchers
```

**Headers:**
```
Authorization: Bearer {superadmin_token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "code": "BETA100",
  "discount_type": "percentage",
  "discount_value": 100,
  "applies_to": "both",
  "max_uses": 50,
  "valid_from": "2026-05-01T00:00:00Z",
  "valid_until": "2026-06-30T23:59:59Z"
}
```

**Field Constraints:**
- `code`: 4-32 Zeichen, nur A-Z und 0-9, unique (case-insensitive)
- `discount_type`: `"percentage"` oder `"fixed"`
- `discount_value`: 
  - Bei `percentage`: 1-100
  - Bei `fixed`: > 0 (EUR)
- `applies_to`: `"base_fee"`, `"aws_percentage"`, oder `"both"`
- `max_uses`: > 0 oder -1 (unlimited)
- `valid_from`: Optional, ISO 8601 Timestamp
- `valid_until`: Optional, ISO 8601 Timestamp (muss > now sein)

**Response (201 Created):**
```json
{
  "code": "BETA100",
  "discount_type": "percentage",
  "discount_value": 100,
  "applies_to": "both",
  "max_uses": 50,
  "current_uses": 0,
  "is_active": true,
  "valid_from": "2026-05-01T00:00:00",
  "valid_until": "2026-06-30T23:59:59",
  "created_at": "2026-05-17T12:00:00",
  "created_by": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response (400 Bad Request):**
```json
{
  "detail": "Voucher with code BETA100 already exists"
}
```

**Mögliche Fehler:**
- `400 Bad Request`: 
  - "Voucher with code {code} already exists"
  - "Invalid code format" (nicht alphanumerisch)
  - "Discount value must be between 1 and 100 for percentage type"
  - "Valid until must be in the future"
- `403 Forbidden`: User ist kein SuperAdmin

**Nebenwirkungen:**
- Audit Log Event: `admin.create_voucher`

**Rate Limit:** 20 Requests/Minute

---

### 5. List Vouchers

Gibt alle Vouchers zurück (mit optionalem Filter).

**Endpoint:**
```
GET /api/v1/admin/vouchers?include_inactive=false
```

**Headers:**
```
Authorization: Bearer {superadmin_token}
```

**Query Parameters:**
- `include_inactive` (boolean, optional): Include deaktivierte Vouchers (default: `false`)

**Response (200 OK):**
```json
{
  "vouchers": [
    {
      "code": "FRIEND2026",
      "discount_type": "percentage",
      "discount_value": 50,
      "applies_to": "both",
      "max_uses": 100,
      "current_uses": 42,
      "is_active": true,
      "valid_from": null,
      "valid_until": "2026-12-31T23:59:59",
      "created_at": "2026-01-01T00:00:00",
      "created_by": "admin-uuid"
    },
    {
      "code": "BETA100",
      "discount_type": "percentage",
      "discount_value": 100,
      "applies_to": "both",
      "max_uses": 50,
      "current_uses": 23,
      "is_active": true,
      "valid_until": "2026-06-30T23:59:59",
      "created_at": "2026-05-17T12:00:00",
      "created_by": "admin-uuid"
    }
  ],
  "total": 2
}
```

**Response (403 Forbidden):**
```json
{
  "detail": "SuperAdmin access required"
}
```

**Rate Limit:** 20 Requests/Minute

---

### 6. Get Voucher Details

Gibt Details eines spezifischen Vouchers zurück.

**Endpoint:**
```
GET /api/v1/admin/vouchers/{code}
```

**Headers:**
```
Authorization: Bearer {superadmin_token}
```

**Path Parameters:**
- `code` (string): Voucher Code (case-insensitive)

**Response (200 OK):**
```json
{
  "code": "FRIEND2026",
  "discount_type": "percentage",
  "discount_value": 50,
  "applies_to": "both",
  "max_uses": 100,
  "current_uses": 42,
  "used_by": [
    "user-uuid-1",
    "user-uuid-2",
    "..."
  ],
  "is_active": true,
  "valid_from": null,
  "valid_until": "2026-12-31T23:59:59",
  "created_at": "2026-01-01T00:00:00",
  "created_by": "admin-uuid",
  "updated_at": "2026-05-17T10:30:00"
}
```

**Response (404 Not Found):**
```json
{
  "detail": "Voucher not found"
}
```

**Rate Limit:** 20 Requests/Minute

---

### 7. Get Voucher Stats

Gibt Nutzungsstatistiken für einen Voucher zurück.

**Endpoint:**
```
GET /api/v1/admin/vouchers/{code}/stats
```

**Headers:**
```
Authorization: Bearer {superadmin_token}
```

**Path Parameters:**
- `code` (string): Voucher Code

**Response (200 OK):**
```json
{
  "code": "FRIEND2026",
  "current_uses": 42,
  "max_uses": 100,
  "usage_percentage": 42.0,
  "unique_users": 42,
  "is_active": true,
  "valid_from": null,
  "valid_until": "2026-12-31T23:59:59",
  "days_remaining": 228,
  "created_at": "2026-01-01T00:00:00"
}
```

**Response (404 Not Found):**
```json
{
  "detail": "Voucher not found"
}
```

**Rate Limit:** 20 Requests/Minute

---

### 8. Deactivate Voucher

Deaktiviert einen Voucher (Soft Delete).

**Endpoint:**
```
DELETE /api/v1/admin/vouchers/{code}
```

**Headers:**
```
Authorization: Bearer {superadmin_token}
```

**Path Parameters:**
- `code` (string): Voucher Code

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Voucher FRIEND2026 deactivated"
}
```

**Response (404 Not Found):**
```json
{
  "detail": "Voucher not found"
}
```

**Nebenwirkungen:**
- `voucher.is_active` wird auf `false` gesetzt
- Voucher kann nicht mehr eingelöst werden
- Bestehende Subscriptions mit diesem Voucher behalten ihn (bis User entfernt)
- Audit Log Event: `admin.deactivate_voucher`

**Rate Limit:** 10 Requests/Minute

---

### 9. Reactivate Voucher

Reaktiviert einen deaktivierten Voucher.

**Endpoint:**
```
POST /api/v1/admin/vouchers/{code}/reactivate
```

**Headers:**
```
Authorization: Bearer {superadmin_token}
Content-Type: application/json
```

**Path Parameters:**
- `code` (string): Voucher Code

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Voucher FRIEND2026 reactivated"
}
```

**Response (404 Not Found):**
```json
{
  "detail": "Voucher not found"
}
```

**Nebenwirkungen:**
- `voucher.is_active` wird auf `true` gesetzt
- Voucher kann wieder eingelöst werden (sofern valid_until nicht abgelaufen)
- Audit Log Event: `admin.reactivate_voucher`

**Rate Limit:** 10 Requests/Minute

---

## Error Codes

### Standard HTTP Error Codes

| Code | Bedeutung | Beispiel |
|------|-----------|----------|
| 200 | OK | Erfolgreiche Operation |
| 201 | Created | Voucher erfolgreich erstellt |
| 400 | Bad Request | Validation-Fehler, Voucher abgelaufen |
| 401 | Unauthorized | JWT Token fehlt oder ungültig |
| 403 | Forbidden | User ist kein SuperAdmin |
| 404 | Not Found | Voucher/Subscription nicht gefunden |
| 429 | Too Many Requests | Rate Limit überschritten |
| 500 | Internal Server Error | Unerwarteter Serverfehler |

### Voucher-spezifische Error Messages

| Error Message | Bedeutung |
|---------------|-----------|
| `Voucher not found` | Code existiert nicht |
| `Voucher is inactive` | Voucher wurde deaktiviert |
| `Voucher expired on {date}` | valid_until überschritten |
| `Voucher has not started yet` | valid_from noch nicht erreicht |
| `Voucher usage limit reached` | max_uses erreicht |
| `You have already used this voucher` | User hat bereits eingelöst |
| `Subscription already has a voucher` | Subscription hat bereits einen anderen Voucher |
| `Voucher with code {code} already exists` | Code bereits vergeben |

---

## Code-Beispiele

### JavaScript (Frontend)

```javascript
// Voucher API Client
class VoucherAPI {
    constructor(apiClient) {
        this.client = apiClient;
    }
    
    // Validate Voucher
    async validateVoucher(code) {
        return await this.client.post('/api/v1/voucher/validate', { code });
    }
    
    // Redeem Voucher
    async redeemVoucher(code, orgId) {
        return await this.client.post('/api/v1/voucher/redeem', {
            code,
            org_id: orgId
        });
    }
    
    // Remove Voucher
    async removeVoucher(orgId) {
        return await this.client.delete(`/api/v1/voucher/remove/${orgId}`);
    }
    
    // Admin: Create Voucher
    async createVoucher(voucherData) {
        return await this.client.post('/api/v1/admin/vouchers', voucherData);
    }
    
    // Admin: List Vouchers
    async listVouchers(includeInactive = false) {
        return await this.client.get(`/api/v1/admin/vouchers?include_inactive=${includeInactive}`);
    }
    
    // Admin: Get Voucher Stats
    async getVoucherStats(code) {
        return await this.client.get(`/api/v1/admin/vouchers/${code}/stats`);
    }
    
    // Admin: Deactivate Voucher
    async deactivateVoucher(code) {
        return await this.client.delete(`/api/v1/admin/vouchers/${code}`);
    }
    
    // Admin: Reactivate Voucher
    async reactivateVoucher(code) {
        return await this.client.post(`/api/v1/admin/vouchers/${code}/reactivate`);
    }
}

// Usage
const voucherAPI = new VoucherAPI(apiClient);

try {
    const result = await voucherAPI.validateVoucher('FRIEND2026');
    if (result.valid) {
        console.log(`Voucher valid: ${result.discount_value}% off`);
    }
} catch (error) {
    console.error('Validation failed:', error.detail);
}
```

### Python (Backend Integration)

```python
from app.services.voucher_service import VoucherService
from app.repositories.voucher import VoucherRepository

# Initialize
voucher_repo = VoucherRepository(table=dynamodb_table)
voucher_service = VoucherService(
    voucher_repo=voucher_repo,
    subscription_repo=subscription_repo
)

# Validate Voucher
is_valid, error_msg = voucher_repo.validate("FRIEND2026", user_id)
if not is_valid:
    raise HTTPException(400, error_msg)

# Redeem Voucher
result = voucher_service.redeem_voucher(
    code="FRIEND2026",
    org_id=org_id,
    user_id=user_id
)

# Calculate Discount
voucher = voucher_repo.get_by_code("FRIEND2026")
discount = VoucherService.calculate_discount(
    voucher=voucher,
    base_price=50.0,
    aws_markup=20.0
)
# → discount = 35.0 (50% of 70)
```

### cURL

```bash
# Validate Voucher
curl -X POST http://localhost:8000/api/v1/voucher/validate \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"code": "FRIEND2026"}'

# Redeem Voucher
curl -X POST http://localhost:8000/api/v1/voucher/redeem \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "FRIEND2026",
    "org_id": "550e8400-e29b-41d4-a716-446655440000"
  }'

# Admin: Create Voucher
curl -X POST http://localhost:8000/api/v1/admin/vouchers \
  -H "Authorization: Bearer SUPERADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "BETA100",
    "discount_type": "percentage",
    "discount_value": 100,
    "applies_to": "both",
    "max_uses": 50,
    "valid_until": "2026-06-30T23:59:59Z"
  }'

# Admin: List Vouchers
curl http://localhost:8000/api/v1/admin/vouchers?include_inactive=false \
  -H "Authorization: Bearer SUPERADMIN_TOKEN"
```

---

## Rate Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| `/voucher/validate` | 10 | 1 Minute |
| `/voucher/redeem` | 5 | 1 Minute |
| `/voucher/remove` | 5 | 1 Minute |
| `/admin/vouchers` (POST) | 20 | 1 Minute |
| `/admin/vouchers` (GET) | 20 | 1 Minute |
| `/admin/vouchers/{code}` | 20 | 1 Minute |
| `/admin/vouchers/{code}/stats` | 20 | 1 Minute |
| `/admin/vouchers/{code}` (DELETE) | 10 | 1 Minute |
| `/admin/vouchers/{code}/reactivate` | 10 | 1 Minute |

Rate Limits werden pro User (via JWT Token) und pro IP-Adresse angewendet.

**Response bei Rate Limit:**
```json
{
  "detail": "Rate limit exceeded. Try again in 42 seconds."
}
```

---

## Changelog

### Version 1.0.0 (2026-05-17)
- Initial API Release
- Public Endpoints: validate, redeem, remove
- Admin Endpoints: create, list, get, stats, deactivate, reactivate
- Rate Limiting implementiert
- Audit Logging für alle Operationen

---

## Support

Bei Fragen oder Problemen:
- **API-Dokumentation:** Dieses Dokument
- **Implementierung:** `backend/app/api/voucher.py`
- **Tests:** `backend/tests/test_voucher_*.py`

**Entwickler:** Claude Sonnet 4.5 via OverCloud Agent Team  
**Projekt:** OverCloud - Cloud Infrastructure Management Platform
