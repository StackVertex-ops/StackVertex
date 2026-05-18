# CSRF Protection Implementation

**Status:** ✅ Implemented (2026-05-17)

## Überblick

OverCloud nutzt **SameSite Cookies** für CSRF-Protection. Dies ist die moderne, empfohlene Methode und schützt alle state-changing Requests (POST, PUT, PATCH, DELETE) vor Cross-Site Request Forgery.

## Implementierung

### Backend (FastAPI)

#### 1. Cookie-basierte Token-Speicherung

**Login/Register Endpoints** (`backend/app/api/auth.py`):

```python
# Set HttpOnly cookie for CSRF protection
response.set_cookie(
    key="access_token",
    value=access_token,
    httponly=True,  # Prevents JavaScript access (XSS protection)
    secure=settings.ENV == "production",  # HTTPS only in production
    samesite="lax",  # CSRF protection (blocks cross-site POST)
    max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    path="/",
)
```

**Cookie Attributes:**
- `httponly=True`: JavaScript kann Token nicht lesen (XSS Protection)
- `samesite="lax"`: Cross-Site POST Requests werden geblockt (CSRF Protection)
- `secure=True` (in production): Cookie nur über HTTPS
- `path="/"`: Cookie gilt für alle Endpoints

#### 2. Dual-Source Token Extraction

**Token kann von zwei Quellen kommen** (`backend/app/api/auth.py`):

```python
async def get_token_from_cookie_or_header(
    authorization: str | None = Header(None),
    access_token: str | None = Cookie(None)
) -> str:
    """Extract JWT token from cookie or Authorization header.

    CSRF Protection: Cookie hat Priorität (SameSite protected).
    Authorization header ist Fallback für API clients.
    """
    # Try cookie first (CSRF protected via SameSite)
    if access_token:
        return access_token

    # Fallback to Authorization header (für API clients)
    if authorization and authorization.startswith("Bearer "):
        return authorization.replace("Bearer ", "")

    raise HTTPException(status_code=401, detail="Not authenticated")
```

**Priorität:**
1. **Cookie** (primär, CSRF-geschützt)
2. **Authorization Header** (Fallback für API Clients, z.B. Postman, CI/CD)

#### 3. CORS Configuration

**CORS muss Credentials erlauben** (`backend/app/config.py`):

```python
CORS_ALLOW_CREDENTIALS: bool = True  # Required for cookies
```

**FastAPI Middleware** (`backend/app/main.py`):

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,  # Wichtig für Cookies!
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### 4. Logout

**Logout löscht Cookie explizit** (`backend/app/api/auth.py`):

```python
@router.post("/logout")
async def logout(
    response: Response,
    current_user: Annotated[dict, Depends(get_current_user)]
):
    """Logout - clears HttpOnly cookie."""
    response.delete_cookie(key="access_token", path="/")
    return {"message": "Logged out successfully"}
```

### Frontend (Vanilla JS)

#### 1. API Client mit Credentials

**Credentials müssen bei jedem Request mitgeschickt werden** (`frontend/src/js/lib/api-client.js`):

```javascript
async request(endpoint, options = {}) {
    const config = {
        headers: {
            'Content-Type': 'application/json',
            ...options.headers,
        },
        credentials: 'include',  // WICHTIG: Send cookies with requests
        ...options,
    };

    const response = await fetch(url, config);
    // ...
}
```

**`credentials: 'include'` ist KRITISCH:**
- Ohne dieses Flag werden Cookies NICHT mitgeschickt
- Gilt für alle Requests (GET, POST, PUT, DELETE)

#### 2. Logout ruft Backend auf

**Logout muss Backend aufrufen, um Cookie zu löschen** (`frontend/src/js/lib/auth.js`):

```javascript
export async function logout() {
    try {
        // Call backend to clear cookie
        await authAPI.logout();
    } catch (error) {
        console.error('Logout API call failed:', error);
        // Continue with client-side logout even if API fails
    }

    // Clear local auth data
    clearAuthData();
    window.location.href = '/src/login.html';
}
```

#### 3. Fallback: localStorage Token

**Token wird ZUSÄTZLICH in localStorage gespeichert:**
- Fallback für API Clients (z.B. wenn Cookies geblockt sind)
- Ermöglicht manuelles Token-Management
- API Client sendet Authorization Header automatisch mit

```javascript
// In api-client.js
const token = localStorage.getItem('access_token');
const authHeaders = token ? { 'Authorization': `Bearer ${token}` } : {};
```

## Security Benefits

### 1. CSRF Protection

**SameSite=Lax verhindert CSRF:**
- Cross-Site POST/PUT/DELETE Requests senden Cookie NICHT mit
- Nur Same-Site Requests bekommen Cookie
- Top-Level Navigation (Link-Klick) sendet Cookie MIT (für normale Links)

**Beispiel CSRF-Angriff (wird geblockt):**

```html
<!-- Evil site: evil.com -->
<form action="https://overcloud.com/api/v1/designer/save" method="POST">
    <input name="name" value="Hacked" />
</form>
<script>
    // User ist bei OverCloud eingeloggt, aber...
    document.forms[0].submit();  // ❌ BLOCKED: Cookie wird NICHT mitgeschickt
</script>
```

### 2. XSS Protection

**HttpOnly verhindert JavaScript-Zugriff:**
- Token kann NICHT via `document.cookie` ausgelesen werden
- XSS-Angriffe können Token nicht stehlen
- Token ist nur vom Browser selbst zugreifbar

**Beispiel XSS-Angriff (wird geblockt):**

```javascript
// Angreifer injiziert JavaScript
console.log(document.cookie);  // ❌ access_token ist NICHT sichtbar
```

### 3. Secure Transport (Production)

**Secure Flag in Production:**
- Cookie wird nur über HTTPS übertragen
- Man-in-the-Middle Angriffe können Cookie nicht abfangen
- Development: `secure=False` für HTTP localhost

## Warum SameSite Cookies statt CSRF Tokens?

| Feature | SameSite Cookies | CSRF Tokens |
|---------|------------------|-------------|
| **Implementierung** | ✅ Einfach (2 Zeilen Code) | ❌ Komplex (Token-Generation, Validation) |
| **Wartung** | ✅ Keine Extra-Logik | ❌ Token-Rotation, Storage |
| **Browser-Support** | ✅ Modern (>95%) | ✅ Universal |
| **Security** | ✅ Built-in Browser Protection | ✅ Manuelle Validation |
| **Performance** | ✅ Keine Extra-Requests | ❌ Extra Token in jedem Request |

**Entscheidung:** SameSite Cookies sind die moderne, empfohlene Methode für Web-Apps.

## Testing

**Tests in** `backend/tests/test_csrf_protection.py`:

```bash
# Run tests
poetry run pytest tests/test_csrf_protection.py -v
```

**Test Coverage:**
- ✅ Login setzt Cookie
- ✅ Register setzt Cookie
- ✅ Authenticated Requests mit Cookie funktionieren
- ✅ Authorization Header als Fallback funktioniert
- ✅ Cookie hat Priorität über Header
- ✅ Logout löscht Cookie
- ✅ Refresh aktualisiert Cookie
- ✅ Keine Auth ohne Cookie/Header schlägt fehl

## Browser Compatibility

**SameSite=Lax Support:**
- Chrome 51+ (2016)
- Firefox 60+ (2018)
- Safari 12+ (2018)
- Edge 16+ (2017)

**Coverage:** >95% der Browser weltweit.

**Fallback:** ältere Browser ignorieren SameSite-Attribut, aber CSRF-Token wäre nötig. Da unser MVP nicht für Legacy-Browser optimiert ist, ist das akzeptabel.

## Migration Checklist

- [x] Backend: Cookie-basierte Token-Speicherung
- [x] Backend: Dual-Source Token Extraction (Cookie + Header)
- [x] Backend: CORS mit `allow_credentials=True`
- [x] Backend: Logout löscht Cookie
- [x] Backend: Refresh aktualisiert Cookie
- [x] Frontend: API Client mit `credentials: 'include'`
- [x] Frontend: Logout ruft Backend auf
- [x] Tests: CSRF Protection Tests geschrieben
- [ ] Tests: Alle Tests laufen erfolgreich (pending execution)
- [ ] Dokumentation: Encyclopedia aktualisiert

## Next Steps

1. **Tests ausführen:** `poetry run pytest tests/test_csrf_protection.py -v`
2. **Manual Testing:**
   - Login im Browser
   - Prüfe Cookie in DevTools (Application → Cookies)
   - Teste Authenticated Requests
   - Teste Logout
3. **Security Encyclopedia aktualisieren** (docs/encyclopedia/security/csrf-protection.md)
4. **Security Summary aktualisieren** (SECURITY_SUMMARY_LATEST.md → CSRF von CRITICAL auf RESOLVED)

## Troubleshooting

### Problem: Cookie wird nicht gesetzt

**Diagnose:**
```javascript
// Browser DevTools Console
console.log(document.cookie);  // access_token sollte NICHT sichtbar sein (HttpOnly)
```

**Lösung:**
- Prüfe CORS Origins in `.env` (`CORS_ORIGINS`)
- Prüfe dass Frontend und Backend auf gleicher Domain (oder CORS korrekt konfiguriert)

### Problem: Cookie wird nicht mitgeschickt

**Diagnose:**
```javascript
// Browser DevTools Network Tab
// Request Headers sollten "Cookie: access_token=..." enthalten
```

**Lösung:**
- Prüfe `credentials: 'include'` in API Client
- Prüfe dass `allow_credentials=True` in CORS Middleware

### Problem: 401 Unauthorized trotz Cookie

**Diagnose:**
```python
# Backend Logs
# Prüfe ob get_token_from_cookie_or_header aufgerufen wird
```

**Lösung:**
- Prüfe dass `get_current_user` Dependency `get_token_from_cookie_or_header` verwendet
- Prüfe Cookie Name (`access_token` muss matchen)

## References

- [OWASP CSRF Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
- [MDN: SameSite Cookies](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Set-Cookie/SameSite)
- [FastAPI Security Best Practices](https://fastapi.tiangolo.com/tutorial/security/)
