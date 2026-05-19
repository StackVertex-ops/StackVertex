# FAQ System - Dokumentation

## Übersicht

Das FAQ-System ermöglicht die Verwaltung und Darstellung von häufig gestellten Fragen auf der OverCloud-Startseite.

## Features

### Öffentliche Seite (Startseite)

- ✅ **Accordion-Darstellung** mit Kategorien
- ✅ **Suche** in Fragen und Antworten
- ✅ **Kategorien-Filter** (Allgemein, Preise, Technik, Sicherheit, Support)
- ✅ **Markdown-Unterstützung** in Antworten
- ✅ **View-Count-Tracking** (automatisch beim Öffnen)
- ✅ **Smooth Animations**

### Admin-Verwaltung

- ✅ **CRUD-Operationen** für FAQs
- ✅ **Kategorien-Verwaltung**
- ✅ **Drag & Drop Sortierung** (Sortable.js)
- ✅ **Published/Draft Status**
- ✅ **Analytics Dashboard** (Views, Top FAQs)
- ✅ **Markdown-Editor** für Antworten

## Architektur

### Backend

```
backend/
├── app/
│   ├── api/faq.py              # API Endpoints
│   ├── services/faq_service.py # Business Logic
│   └── repositories/faq.py     # DynamoDB Access
└── scripts/
    ├── seed_faq_categories.py  # Default Categories
    └── seed_example_faqs.py    # Example FAQs
```

### Frontend

```
frontend/
├── src/
│   ├── index.html                    # FAQ Section auf Startseite
│   ├── admin-faq.html                # Admin Dashboard
│   └── js/
│       ├── components/FaqAccordion.js # FAQ Component
│       └── pages/admin-faq.js         # Admin Logic
```

### DynamoDB Schema

#### FAQ Item

```
PK: FAQ#{faq_id}
SK: METADATA
Attributes:
  - faq_id: UUID
  - category: string (slug)
  - question: string
  - answer: string (Markdown)
  - status: published/draft
  - sort_order: int
  - view_count: int
  - created_by: string
  - created_at: ISO timestamp
  - updated_at: ISO timestamp

GSI1: faq_category#{category} + sort_order
GSI2: faq_status#{status} + created_at
```

#### Category Item

```
PK: FAQ_CATEGORY#{category_id}
SK: METADATA
Attributes:
  - category_id: UUID
  - name: string
  - slug: string
  - icon: string (Emoji)
  - sort_order: int
  - created_at: ISO timestamp
  - updated_at: ISO timestamp

GSI3: category_list + sort_order
```

## API Endpoints

### Public (keine Auth)

```
GET /api/v1/faq
GET /api/v1/faq/search?q={query}
GET /api/v1/faq/categories
GET /api/v1/faq/{faq_id}  # Tracked view count
```

### Admin (SuperAdmin only)

```
GET    /api/v1/admin/faq
POST   /api/v1/admin/faq
PATCH  /api/v1/admin/faq/{faq_id}
DELETE /api/v1/admin/faq/{faq_id}
POST   /api/v1/admin/faq/reorder
GET    /api/v1/admin/faq/analytics

POST   /api/v1/admin/faq/categories
PATCH  /api/v1/admin/faq/categories/{category_id}
DELETE /api/v1/admin/faq/categories/{category_id}
```

## Setup & Deployment

### 1. Kategorien erstellen

```bash
cd backend
python scripts/seed_faq_categories.py
```

Default-Kategorien:
- 📌 Allgemein
- 💰 Preise
- ⚙️ Technik
- 🔐 Sicherheit
- 💬 Support

### 2. Beispiel-FAQs erstellen (optional)

```bash
python scripts/seed_example_faqs.py
```

Erstellt 10 Beispiel-FAQs in allen Kategorien.

### 3. Frontend testen

```bash
cd frontend
npm run dev
```

- **Startseite**: http://localhost:5173/
- **Admin**: http://localhost:5173/admin-faq.html

## Nutzung

### Als Admin: FAQ erstellen

1. Login als SuperAdmin
2. Gehe zu `/admin-faq.html`
3. Klicke "+ Neues FAQ"
4. Fülle aus:
   - **Kategorie**: Wähle aus vorhandenen
   - **Frage**: Kurz und prägnant (5-500 Zeichen)
   - **Antwort**: Markdown-formatiert
   - **Status**: Draft oder Published

### Markdown-Syntax

```markdown
**fett**
*kursiv*
`code`
[Link](https://example.com)

- Liste
- Punkt 2

1. Nummeriert
2. Liste
```

### Sortierung ändern

Drag & Drop in der Admin-Liste → Automatische Speicherung

### Analytics

Im Admin-Dashboard:
- Gesamt FAQs
- Veröffentlicht vs. Entwürfe
- Gesamt Views
- Top 10 meist angesehene FAQs

## Best Practices

### Fragen schreiben

✅ **Kurz und spezifisch**
- "Was kostet OverCloud?" ✅
- "Pricing-Informationen" ❌

✅ **User-Perspektive**
- "Wie erreiche ich den Support?" ✅
- "Support-Kontakt" ❌

### Antworten schreiben

✅ **Strukturiert mit Markdown**
```markdown
OverCloud nutzt ein **nutzungsbasiertes** Pricing:

- Free Tier: 3 Architekturen
- Pro: €29/Monat
- Enterprise: Custom

Mehr Details: [Preise](https://overcloud.io/pricing)
```

✅ **Kurz und prägnant** (max. 300 Wörter)

✅ **Visuelle Elemente** nutzen (Emojis, Listen, Code-Blocks)

### Kategorien

- **Allgemein**: "Was ist X?", "Für wen?"
- **Preise**: Kosten, Billing, Limits
- **Technik**: Wie funktioniert X?, Integration
- **Sicherheit**: Datenschutz, Compliance
- **Support**: Kontakt, Troubleshooting

## Troubleshooting

### FAQs werden nicht angezeigt

1. Prüfe ob Status = "published"
2. Prüfe Browser Console (Netzwerk-Fehler?)
3. Prüfe Backend-Logs

### View Count wird nicht getrackt

- Public Endpoint `/faq/{id}` trackt automatisch
- Admin-Preview trackt NICHT

### Sortierung funktioniert nicht

- Prüfe ob alle FAQs in derselben Kategorie
- Prüfe Browser Console (Sortable.js geladen?)
- Reload Seite

## Erweiterungen (geplant)

- [ ] **Mehrsprachigkeit** (DE/EN)
- [ ] **FAQ Voting** (Hilfreich? Ja/Nein)
- [ ] **Related FAQs** (Automatische Vorschläge)
- [ ] **FAQ Export** (PDF, Markdown)
- [ ] **FAQ Import** (CSV, JSON)
- [ ] **Rich Media** (Screenshots, Videos)
- [ ] **Versioning** (Änderungshistorie)

## Testing

### Manual Testing Checklist

#### Frontend (Startseite)

- [ ] FAQs laden korrekt
- [ ] Accordion öffnet/schließt
- [ ] Suche funktioniert
- [ ] Kategorien-Filter funktioniert
- [ ] Markdown rendert korrekt
- [ ] Mobile-Responsive

#### Admin

- [ ] Login als SuperAdmin
- [ ] FAQ erstellen
- [ ] FAQ bearbeiten
- [ ] FAQ löschen
- [ ] Drag & Drop Sortierung
- [ ] Kategorie erstellen
- [ ] Analytics laden

#### API

```bash
# Public
curl http://localhost:8000/api/v1/faq

# Search
curl "http://localhost:8000/api/v1/faq/search?q=preis"

# Admin (mit Token)
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/admin/faq
```

## Performance

- **Query Efficiency**: GSI1 & GSI2 für schnelle Lookups
- **Caching**: Frontend cacht FAQs für 5 Minuten
- **Pagination**: Backend limitiert auf 1000 Items (für Admin)
- **View Tracking**: Async, blockiert nicht UI

## Security

- ✅ Admin-Endpunkte erfordern SuperAdmin-Auth
- ✅ Input-Validation (Pydantic)
- ✅ XSS-Protection (Markdown sanitized)
- ✅ Rate Limiting (SlowAPI)

## Maintenance

### Monatliche Aufgaben

- Review Analytics → Ungenutzte FAQs löschen
- Top FAQs optimieren (bessere Antworten)
- Neue User-Fragen → FAQs hinzufügen

### Bei größeren Updates

- JSON-Schema-Migration für DynamoDB
- Frontend-Component-Update
- Seed-Scripts aktualisieren

---

**Letzte Aktualisierung**: 2026-05-19
**Version**: 1.0.0
