# StackVertex - Testing Best Practices & Lessons Learned

> Dokumentation der wichtigsten Testing-Erkenntnisse aus der Test-Suite-Bereinigung (Mai 2026)

---

## Übersicht

Nach umfassender Bereinigung der Test-Suite (12 FAILED → 0 FAILED, 643 PASSED):
- **Organisation Type Field Fix**
- **JWT Token Uniqueness**  
- **Billing Decimal Type Safety**
- **CSRF Protection Tests**
- **User Status Update**

Diese Dokumentation fasst die wichtigsten Erkenntnisse und Best Practices zusammen.

---

## 1. Pydantic Schema & FastAPI Serialisierung

### Problem: KeyError bei API Responses

**Symptom:**
```python
# Test schlägt fehl
assert data["type"] == "team"  # KeyError: 'type'
```

**Ursache:**
- Pydantic Schema hatte Feld mit Alias: `type: OrganisationType = Field(alias="organisation_type")`
- Datenbank speichert als `organisation_type`
- FastAPI serialisiert mit `by_alias=True` → verwendet Alias statt Feldname
- Response enthält `organisation_type` statt erwartetem `type`

**Lösung:**
```python
# 1. Schema-Feld direkt benennen (kein Alias)
class OrganisationBase(BaseModel):
    name: str
    type: OrganisationType  # Kein alias mehr!

# 2. Mapping-Funktion für DB → API Response
def map_org_type_field(org_dict: dict) -> dict:
    """Map organisation_type field from DB to type field for API response."""
    if "organisation_type" in org_dict:
        org_dict["type"] = org_dict.pop("organisation_type")
    return org_dict

# 3. In allen API-Responses verwenden
org_without_quota = {k: v for k, v in org.items() if k != "quota"}
org_without_quota = map_org_type_field(org_without_quota)
return OrganisationResponse(**org_without_quota, quota=quota_response)
```

**Best Practice:**
- ✅ Bei Feldname-Mismatch zwischen DB und API: Explizites Mapping verwenden
- ✅ Keine Aliases verwenden, wenn Konsistenz nicht garantiert ist
- ✅ Mapping-Funktion für wiederverwendbare Transformationen
- ❌ Nicht auf `populate_by_name` + `by_alias` Kombinationen verlassen

---

## 2. JWT Token Uniqueness

### Problem: Identische Tokens bei schnellen Requests

**Symptom:**
```python
# Login -> Refresh innerhalb der gleichen Sekunde
assert new_access_token != old_access_token  # AssertionError!
```

**Ursache:**
- JWT verwendet Unix Timestamps (Sekunden-Präzision)
- `exp` (expiration) wird auf Sekunden gerundet
- Bei schnellen Tests: Login und Refresh in der gleichen Sekunde
- Identische Claims (`sub`, `email`, `exp`, `type`) = identischer Token!

**Lösung:**
```python
def create_access_token(data: dict) -> str:
    """Create short-lived JWT access token (15 minutes)."""
    from uuid import uuid4
    
    to_encode = data.copy()
    now = datetime.utcnow()
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "iat": now,              # Issued At (Standard JWT Claim)
        "jti": str(uuid4()),     # JWT ID (garantiert Uniqueness!)
        "type": "access"
    })

    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
```

**Best Practice:**
- ✅ **Immer `jti` (JWT ID) mit UUID verwenden** → garantiert eindeutige Tokens
- ✅ **`iat` (issued at)** hinzufügen für Audit-Zwecke
- ✅ Bei Token-Rotation: Neue UUID für jeden Token
- ❌ Nicht auf Timestamp-Präzision für Uniqueness verlassen

---

## 3. Decimal vs Float in DynamoDB

### Problem: TypeError bei Billing-Berechnungen

**Symptom:**
```python
# TypeError: unsupported operand type(s) for *: 'float' and 'decimal.Decimal'
markup_fee = aws_costs * (Decimal(str(markup_percentage)) / Decimal("100"))
```

**Ursache:**
- DynamoDB unterstützt KEINE Python `float` Type
- Alle numerischen Werte müssen `Decimal` sein
- Tests übergeben oft `float` (z.B. `200.00`)
- Python verbietet `float * Decimal` Operationen

**Lösung:**
```python
from decimal import Decimal

def calculate_monthly_cost_example(
    tier: BillingTier,
    aws_costs: Decimal,  # Type Hint sagt Decimal
    num_deployments: int = 0
) -> Dict[str, Decimal]:
    """Calculate example monthly cost for tier."""
    
    # WICHTIG: Defensive Konvertierung
    if not isinstance(aws_costs, Decimal):
        aws_costs = Decimal(str(aws_costs))
    
    config = get_tier_config(tier)
    base_price = config["base_price_monthly"]  # Bereits Decimal
    markup_percentage = config["aws_cost_percentage"]  # int
    
    # Alle Berechnungen mit Decimal
    markup_fee = aws_costs * (Decimal(str(markup_percentage)) / Decimal("100"))
    total = base_price + markup_fee
    
    return {
        "base_price": base_price.quantize(Decimal("0.01")),
        "markup_fee": markup_fee.quantize(Decimal("0.01")),
        "total": total.quantize(Decimal("0.01"))
    }
```

**Test-Anpassungen:**
```python
# ❌ FALSCH: Vergleich Decimal mit float
assert result["tax"] == 13.30

# ✅ RICHTIG: float() Konvertierung für pytest.approx()
assert float(result["tax"]) == pytest.approx(13.30, rel=0.01)

# ✅ ODER: Direkt Decimal-Vergleich
assert result["tax"] == Decimal("13.30")
```

**Best Practice:**
- ✅ **Immer Decimal für Geld/Preise verwenden**
- ✅ **Defensive Konvertierung am Funktions-Eingang**: `if not isinstance(x, Decimal): x = Decimal(str(x))`
- ✅ **`.quantize(Decimal("0.01"))` für Cent-Präzision**
- ✅ **In Tests**: `float()` für `pytest.approx()`, ODER direkt `Decimal()` vergleichen
- ❌ Niemals `float` mit `Decimal` mischen

---

## 4. TestClient Cookie Persistence

### Problem: Tests schlagen fehl wegen Cookie-Pollution

**Symptom:**
```python
# User 1 registriert → Cookie gesetzt
# User 2 registriert → Cookie überschrieben
# User 1 versucht Request mit Token → 200 statt 403 (Cookie ist noch da!)
```

**Ursache:**
- FastAPI `TestClient` speichert Cookies automatisch
- Nachfolgende Requests verwenden gespeicherte Cookies
- Security-Tests wollen nur Bearer Token testen, aber Cookie hat Priorität

**Lösung:**
```python
def test_update_other_user_forbidden(self, client):
    # User 1 registrieren
    response1 = client.post("/api/v1/auth/register", json={...})
    token1 = response1.json()["access_token"]
    
    # User 2 registrieren
    response2 = client.post("/api/v1/auth/register", json={...})
    user2_id = response2.json()["user"]["id"]
    
    # ✅ WICHTIG: Cookies löschen vor kritischen Security-Tests!
    client.cookies.clear()
    
    # User 1 versucht User 2 zu updaten (nur mit Token)
    response = client.patch(
        f"/api/v1/users/{user2_id}",
        headers={"Authorization": f"Bearer {token1}"},
        json={"name": "Hacked Name"}
    )
    
    assert response.status_code == 403  # Jetzt korrekt!
```

**Best Practice:**
- ✅ **`client.cookies.clear()` vor Security-Tests** (IDOR, Permission-Checks)
- ✅ In Fixtures: Nach User-Erstellung Cookies clearen
- ✅ Wenn NUR Bearer Token getestet werden soll: Cookies löschen
- ✅ Dokumentieren: Welche Auth-Methode wird getestet (Cookie vs Token)
- ❌ Nicht auf implizites Cookie-Handling verlassen

---

## 5. Pytest Fixtures & Scope

### Problem: Fixture-Reuse führt zu "User already member" Fehlern

**Symptom:**
```python
# Test 1: add_member_as_owner → OK
# Test 2: add_member_as_admin → 400 "User is already a member"
```

**Ursache:**
- Shared Fixture `member_user` wird in mehreren Tests wiederverwendet
- Test 1 fügt User zur Organisation hinzu
- Test 2 versucht den gleichen User nochmal hinzuzufügen → Fehler

**Lösung:**
```python
# ❌ FALSCH: Shared Fixture
@pytest.fixture
def member_user(client):
    response = client.post("/api/v1/auth/register", ...)
    return response.json()

def test_add_member_as_owner(self, client, owner_user, member_user):
    # Fügt member_user hinzu
    ...

def test_add_member_as_admin(self, client, admin_user, member_user):
    # Versucht member_user nochmal hinzuzufügen → FEHLER!
    ...

# ✅ RICHTIG: Fresh User pro Test
def test_add_member_as_owner(self, client, owner_user):
    # Fresh member nur für diesen Test
    member_response = client.post("/api/v1/auth/register", json={
        "email": "fresh_member_owner@example.com",
        "name": "Fresh Member",
        "password": "SecurePass123!"
    })
    member_id = member_response.json()["user"]["id"]
    
    client.cookies.clear()
    
    # Jetzt hinzufügen
    response = client.post(f"/api/v1/organisations/{org_id}/members", ...)
```

**Best Practice:**
- ✅ **Stateful Operations**: Fresh Fixtures pro Test
- ✅ **Read-Only Operations**: Shared Fixtures OK
- ✅ **Fixture Scope bewusst wählen**: `function` (default) vs `session`
- ✅ **Unique Emails/IDs**: `f"user_{uuid4()}@example.com"`
- ❌ Nicht Fixtures für Entities sharen, die Modified werden

---

## 6. Repository Method Signatures

### Problem: TypeError bei update() Aufrufen

**Symptom:**
```python
user_repo.update(user_id, status="inactive")
# TypeError: update() got an unexpected keyword argument 'status'
```

**Ursache:**
- Repository `update()` Methode erwartet: `update(id: UUID, updates: dict)`
- Test übergibt keyword arguments statt Dict

**Lösung:**
```python
# ❌ FALSCH
user_repo.update(user_id, status="inactive", name="Updated")

# ✅ RICHTIG
user_repo.update(user_id, {"status": "inactive", "name": "Updated"})

# ✅ ODER: Explizite Parameter
user_repo.update(
    user_id=user_id,
    updates={"status": "inactive"}
)
```

**Best Practice:**
- ✅ **Repository Methods**: Immer `updates: dict` Parameter
- ✅ **Type Hints**: `def update(self, id: UUID, updates: dict) -> Optional[dict]`
- ✅ **Tests**: Prüfen mit verschiedenen update-Kombinationen
- ✅ **Dokumentation**: Beispiel-Aufrufe in Docstrings

---

## 7. Pydantic Schema Validation

### Problem: 422 Unprocessable Entity wegen ungültiger Felder

**Symptom:**
```python
# Registration schlägt fehl
response = client.post("/api/v1/auth/register", json={
    "email": "test@example.com",
    "password": "SecurePass123!",
    "name": "Test User",
    "auth_provider": "local"  # ❌ Feld existiert nicht!
})
# Status: 422
```

**Ursache:**
- Request enthält Feld, das nicht im Pydantic Schema definiert ist
- FastAPI validiert gegen Schema → wirft 422 Error
- Oft in alten Tests, die noch veraltete Felder verwenden

**Lösung:**
```python
# 1. Schema überprüfen
class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str
    # Kein 'auth_provider' Feld!

# 2. Request anpassen
response = client.post("/api/v1/auth/register", json={
    "email": "test@example.com",
    "password": "SecurePass123!",
    "name": "Test User"
    # auth_provider entfernt
})
```

**Best Practice:**
- ✅ **Bei 422 Errors**: Schema gegen Request-Body prüfen
- ✅ **Pydantic V2**: `model_dump()` statt `dict()` verwenden
- ✅ **Extra Fields**: `model_config = ConfigDict(extra='forbid')` für strikte Validation
- ✅ **Tests**: Negative Tests für ungültige Felder
- ❌ Nicht auf `extra='allow'` verlassen (versteckt Fehler)

---

## 8. Test Isolation & Cleanup

### Problem: Tests beeinflussen sich gegenseitig

**Symptom:**
- Test 1 alleine: ✅ PASS
- Test 1 + Test 2 zusammen: ❌ FAIL
- Grund: Shared State, nicht aufgeräumte Daten

**Best Practice:**
```python
# ✅ Fixture mit Cleanup
@pytest.fixture
def test_organisation(client, test_user):
    # Setup
    response = client.post("/api/v1/organisations", ...)
    org_id = response.json()["id"]
    
    yield org_id
    
    # Cleanup (nach Test)
    client.delete(f"/api/v1/organisations/{org_id}")

# ✅ Mock-Reset
@pytest.fixture(autouse=True)
def reset_mocks():
    yield
    # Nach jedem Test
    mock.reset_mock()

# ✅ DynamoDB Mock: Fresh Table pro Test
@pytest.fixture(scope="function")  # Nicht session!
def mock_dynamodb_table():
    with mock_aws():
        dynamodb = boto3.resource('dynamodb', ...)
        table = dynamodb.create_table(...)
        yield table
        # Automatisches Cleanup durch mock_aws Context
```

---

## 9. Integration vs Unit Tests

### Wann welcher Test-Typ?

**Unit Tests** (schnell, isoliert):
```python
# ✅ Reine Business Logic
def test_calculate_markup_fee():
    fee = calculate_markup_fee(
        aws_costs=Decimal("100.00"),
        percentage=10
    )
    assert fee == Decimal("10.00")

# ✅ Utility Functions
def test_map_org_type_field():
    result = map_org_type_field({"organisation_type": "team"})
    assert result["type"] == "team"
```

**Integration Tests** (langsamer, realistisch):
```python
# ✅ API Endpoints mit DB
def test_create_organisation(client, authenticated_user):
    response = client.post("/api/v1/organisations", ...)
    assert response.status_code == 201

# ✅ Security Flows (IDOR, Permissions)
def test_user_cannot_delete_other_user(client, user_a, user_b):
    response = client.delete(
        f"/api/v1/users/{user_b['id']}",
        headers={"Authorization": f"Bearer {user_a['token']}"}
    )
    assert response.status_code == 403
```

**Best Practice:**
- ✅ **70% Unit, 30% Integration** (Pyramide)
- ✅ **Unit**: Business Logic, Utilities, Calculations
- ✅ **Integration**: API Flows, Security, DB Interactions
- ✅ **E2E**: Kritische User Journeys (Login → Dashboard → Deploy)
- ❌ Nicht alles mit Integration Tests testen (zu langsam)

---

## 10. Test Maintenance Checklist

### Beim Hinzufügen neuer Features:

- [ ] **Unit Tests** für neue Business Logic
- [ ] **Integration Tests** für neue API Endpoints
- [ ] **Security Tests** wenn Permissions betroffen
- [ ] **Negative Tests** (Invalid Input, Edge Cases)
- [ ] **Fixtures dokumentieren** (Scope, Purpose, Cleanup)
- [ ] **Skipped Tests aktualisieren** wenn Feature implementiert

### Bei Test-Failures:

1. **Isolieren**: Test alleine laufen lassen
2. **Logs prüfen**: `pytest -v -s --tb=short`
3. **Fixture-State**: Cookies cleared? Fresh Data?
4. **Schema-Mismatch**: Request vs Pydantic Schema
5. **Type-Fehler**: float vs Decimal, str vs UUID
6. **Zeitabhängig**: Timestamps, Uniqueness (jti!)

---

## Zusammenfassung: Top 10 Test Best Practices

1. ✅ **JWT Tokens**: Immer `jti` (UUID) für Uniqueness
2. ✅ **Decimal Types**: Defensive Konvertierung, nie float mischen
3. ✅ **Cookie Handling**: `client.cookies.clear()` vor Security-Tests
4. ✅ **Fresh Fixtures**: Stateful Entities nicht sharen
5. ✅ **Schema Validation**: Request-Body gegen Pydantic Schema prüfen
6. ✅ **Explicit Mapping**: Bei DB ↔ API Field-Mismatch
7. ✅ **Repository Calls**: `update(id, dict)` nicht `update(id, **kwargs)`
8. ✅ **Test Isolation**: Cleanup in Fixtures, Fresh Mocks
9. ✅ **Test Pyramid**: 70% Unit, 30% Integration
10. ✅ **Documentation**: Fixtures dokumentieren, Skipped Tests begründen

---

## Finale Statistik

**Test Suite Status (2026-05-17):**
- ✅ **643 PASSED**
- ⏭️ **26 SKIPPED** (valide Gründe dokumentiert)
- ❌ **0 FAILED**

**Fixes in diesem Sprint:**
- Organisation Type Field (1 Test)
- JWT Token Uniqueness (1 Test)
- Billing Decimal (3 Tests)
- User Status Update (1 Test)
- CSRF Protection (8 Tests)

**Total: 12 → 0 Failures** 🎉

---

*Dokumentiert: 2026-05-17*
*Autor: Claude (AI Assistant) + Andy Schwarz*
*Status: Production Ready ✅*
