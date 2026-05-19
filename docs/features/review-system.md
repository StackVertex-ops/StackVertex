# Review System - Dokumentation

## Übersicht

Das Review-System ermöglicht Nutzern, 5-Sterne-Bewertungen mit Kommentaren auf der OverCloud-Startseite zu hinterlassen. Alle Reviews werden vor Veröffentlichung moderiert.

## Features

### Öffentliche Seite (Startseite)

- ✅ **5-Sterne-Rating** (interaktive Star-Komponente)
- ✅ **Kommentar-Funktion** (10-1000 Zeichen)
- ✅ **Rating-Statistik** anzeigen (Durchschnitt, Verteilung)
- ✅ **Spam-Detection** (zu viele URLs, ALL CAPS)
- ✅ **Nur genehmigte Reviews** sichtbar
- ✅ **Anonymisierung** (keine Email/IP öffentlich)

### Admin-Moderation

- ✅ **Pending Reviews** mit vollständigen Metadaten (Email, IP, User-Agent)
- ✅ **Approve/Reject/Spam** Aktionen
- ✅ **Bulk-Approve** (mehrere Reviews gleichzeitig genehmigen)
- ✅ **Filter nach Status** (pending, approved, rejected, spam)
- ✅ **Delete-Funktion** (permanentes Löschen)
- ✅ **Rating-Distribution** (1-5 Sterne Verteilung)

## Architektur

### Backend

```
backend/
├── app/
│   ├── api/reviews.py              # API Endpoints (Public + Admin)
│   ├── services/review_service.py  # Business Logic + Spam Detection
│   ├── repositories/review.py      # DynamoDB Access
│   └── schemas/review.py           # Pydantic Schemas
└── tests/
    ├── api/test_reviews.py         # 34 API Tests
    ├── services/test_review_service.py # 27 Service Tests
    └── repositories/test_review.py # 28 Repository Tests
```

### Frontend

```
frontend/
├── src/
│   ├── index.html                           # Review Section auf Startseite
│   ├── admin-reviews.html                   # Admin Moderation Dashboard
│   └── js/
│       ├── components/StarRating.js         # Wiederverwendbare Star-Komponente
│       └── lib/api-reviews.js               # API Client
```

## DynamoDB Schema

### Primary Keys

```
PK: REVIEW#{review_id}
SK: METADATA
```

### GSI1 - Status Index

```
GSI1PK: review_status#{status}
GSI1SK: {created_at}
```

**Zweck:** Reviews nach Status filtern (pending, approved, rejected, spam)

### GSI2 - Rating Index

```
GSI2PK: review_rating#{rating}
GSI2SK: {created_at}
```

**Zweck:** Reviews nach Rating filtern (1-5 Sterne)

### Attribute

```python
{
    "PK": "REVIEW#550e8400-e29b-41d4-a716-446655440000",
    "SK": "METADATA",
    "GSI1PK": "review_status#approved",
    "GSI1SK": "2026-05-19T10:30:00Z",
    "GSI2PK": "review_rating#5",
    "GSI2SK": "2026-05-19T10:30:00Z",
    "name": "Max Mustermann",
    "email": "max@example.com",  # Nur für Admin sichtbar
    "rating": 5,
    "comment": "Tolles Tool, sehr übersichtlich!",
    "status": "approved",
    "ip_address": "192.168.1.1",  # Nur für Admin sichtbar
    "user_agent": "Mozilla/5.0...",  # Nur für Admin sichtbar
    "created_at": "2026-05-19T10:30:00Z",
    "updated_at": "2026-05-19T10:35:00Z"
}
```

## API Endpoints

### Public Endpoints

#### `POST /api/v1/reviews` - Submit Review

**Request:**
```json
{
    "name": "Max Mustermann",
    "email": "max@example.com",
    "rating": 5,
    "comment": "Sehr gutes Tool!"
}
```

**Response:** `201 Created`
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "pending",
    "message": "Review submitted for moderation"
}
```

**Validierung:**
- Name: 2-100 Zeichen
- Email: Valide Email-Adresse
- Rating: 1-5
- Comment: 10-1000 Zeichen

**Spam Detection:**
- ❌ Mehr als 2 URLs im Kommentar
- ❌ Mehr als 70% Großbuchstaben
- ❌ Kommentar zu kurz (<10) oder zu lang (>1000)

#### `GET /api/v1/reviews` - Get Public Reviews

**Response:** `200 OK`
```json
{
    "reviews": [
        {
            "id": "...",
            "name": "Max Mustermann",
            "rating": 5,
            "comment": "Sehr gutes Tool!",
            "created_at": "2026-05-19T10:30:00Z"
        }
    ],
    "stats": {
        "average_rating": 4.5,
        "total_count": 12,
        "distribution": {
            "1": 0,
            "2": 1,
            "3": 1,
            "4": 2,
            "5": 8
        }
    }
}
```

**Filter:**
- `status`: Nur approved Reviews (automatisch)
- `limit`: Max. Anzahl (default: 20, max: 100)

**Hinweis:** Email, IP-Adresse und User-Agent werden NICHT zurückgegeben.

### Admin Endpoints

Alle Admin-Endpoints erfordern SuperAdmin-Berechtigung.

#### `GET /api/v1/admin/reviews` - Get All Reviews

**Query Params:**
- `status`: Filter nach Status (pending, approved, rejected, spam, all)
- `limit`: Max. Anzahl

**Response:** `200 OK`
```json
{
    "reviews": [
        {
            "id": "...",
            "name": "Max Mustermann",
            "email": "max@example.com",
            "rating": 5,
            "comment": "Sehr gutes Tool!",
            "status": "pending",
            "ip_address": "192.168.1.1",
            "user_agent": "Mozilla/5.0...",
            "created_at": "2026-05-19T10:30:00Z",
            "updated_at": "2026-05-19T10:35:00Z"
        }
    ]
}
```

#### `PATCH /api/v1/admin/reviews/{review_id}/approve` - Approve Review

**Response:** `200 OK`

#### `PATCH /api/v1/admin/reviews/{review_id}/reject` - Reject Review

**Response:** `200 OK`

#### `POST /api/v1/admin/reviews/bulk-approve` - Bulk Approve

**Request:**
```json
{
    "review_ids": ["id1", "id2", "id3"]
}
```

**Response:** `200 OK`
```json
{
    "approved": 3,
    "failed": 0
}
```

#### `DELETE /api/v1/admin/reviews/{review_id}` - Delete Review

**Response:** `204 No Content`

**Hinweis:** Idempotent - gibt auch 204 zurück wenn Review nicht existiert.

#### `GET /api/v1/admin/reviews/stats` - Get Rating Stats

**Response:** `200 OK`
```json
{
    "average_rating": 4.5,
    "total_count": 12,
    "by_status": {
        "approved": 8,
        "pending": 3,
        "rejected": 1,
        "spam": 0
    },
    "distribution": {
        "1": 0,
        "2": 1,
        "3": 1,
        "4": 2,
        "5": 8
    }
}
```

## Spam Detection Rules

```python
def is_spam(comment: str) -> bool:
    # Zu viele URLs
    if len(re.findall(r'https?://', comment)) > 2:
        return True
    
    # Zu kurz
    if len(comment) < 10:
        return True
    
    # Zu lang
    if len(comment) > 1000:
        return True
    
    # ALL CAPS
    if comment.isupper() and len(comment) > 20:
        return True
    
    # Excessive CAPS (>70%)
    caps_ratio = sum(1 for c in comment if c.isupper()) / len(comment)
    if caps_ratio > 0.7:
        return True
    
    return False
```

## Test Coverage

- **Repository Tests:** 28 (100% passing)
- **Service Tests:** 27 (100% passing)
- **API Tests:** 34 (33 passing, 1 skipped - Rate Limit)

**Coverage:** 98%

## Security

- ✅ **Email Normalization** (lowercase vor Speicherung)
- ✅ **IP-Adresse** nur für Admin sichtbar
- ✅ **User-Agent** nur für Admin sichtbar
- ✅ **Rate Limiting** (SlowAPI - konfigurierbar)
- ✅ **Admin-Only Moderation** (SuperAdmin RBAC)
- ✅ **Spam Detection** (automatisch)

## Deployment Checklist

- [ ] DynamoDB Table mit GSI1 (status) und GSI2 (rating) erstellt
- [ ] S3 Bucket für Frontend Static Files
- [ ] Admin User mit SuperAdmin-Rolle erstellt
- [ ] Rate Limiting konfiguriert
- [ ] Frontend `admin-reviews.html` deployed
- [ ] Startpage Review-Sektion aktiviert

## Zukünftige Erweiterungen

- [ ] Antworten auf Reviews (Admin → User)
- [ ] Review-Kategorien (Feature-Bewertungen, Support, etc.)
- [ ] Hilfreiche Reviews markieren (Upvote/Downvote)
- [ ] Email-Notification bei Approval/Rejection
- [ ] Export Reviews als CSV
