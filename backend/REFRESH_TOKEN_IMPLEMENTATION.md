# Refresh Token Pattern Implementation

## Übersicht

Implementierung eines sicheren Refresh Token Patterns mit Token Rotation für JWT Authentication.

### Ziele
- **Kurze Access Tokens** (15 Min) = weniger Schaden bei Token-Leak
- **Lange Refresh Tokens** (7 Tage) = gute UX (User bleibt eingeloggt)
- **Token Rotation** = verhindert Replay-Attacks

## Backend Changes

### 1. Config (`app/config.py`)
```python
ACCESS_TOKEN_EXPIRE_MINUTES: int = 15  # 15 minutes (was 60)
REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # 7 days
CORS_ALLOW_CREDENTIALS: bool = True  # Required for cookies
```

### 2. Refresh Token Repository (`app/repositories/refresh_token.py`)

Neues Repository für Refresh Token Management in DynamoDB.

**Features:**
- Token Hashing (SHA256) - Tokens werden gehasht gespeichert, nicht im Klartext
- Token Rotation - Jeder Refresh gibt neues Refresh Token
- Automatic TTL - DynamoDB löscht abgelaufene Tokens automatisch
- Revocation - Tokens können invalidiert werden (z.B. bei Logout)

**DynamoDB Schema:**
```
PK: USER#{user_id}
SK: REFRESH_TOKEN#{token_id}

GSI1PK: REFRESH_TOKEN#{token_hash}  # For token lookup
GSI1SK: METADATA

Attributes:
- id: UUID
- user_id: User UUID
- token_hash: SHA256 hash of JWT
- expires_at: ISO datetime
- revoked: boolean
- ttl: Unix timestamp (for automatic cleanup)
```

**Methods:**
- `create()` - Speichert neues Refresh Token
- `get_by_token()` - Findet Token via Hash (GSI1)
- `revoke()` - Invalidiert einzelnes Token
- `revoke_all_for_user()` - Logout from all devices

### 3. Auth API Updates (`app/api/auth.py`)

**New Helper Functions:**
- `create_access_token()` - Creates 15 min token with `type: "access"`
- `create_refresh_token()` - Creates 7 day token with `type: "refresh"`
- `verify_refresh_token()` - Validates refresh token and checks type

**Updated Endpoints:**

#### POST `/api/v1/auth/register`
- Returns Access + Refresh Token
- Sets both as HttpOnly cookies
- Stores Refresh Token in DynamoDB

#### POST `/api/v1/auth/login`
- Returns Access + Refresh Token
- Sets both as HttpOnly cookies
- Stores Refresh Token in DynamoDB

#### POST `/api/v1/auth/refresh` (NEW IMPLEMENTATION)
```python
# Input: Refresh Token (via cookie)
# Output: New Access Token + New Refresh Token

Steps:
1. Verify Refresh Token JWT
2. Check token exists in DB and is not revoked
3. Get user and verify active status
4. REVOKE old Refresh Token (Token Rotation)
5. Create NEW Access Token + NEW Refresh Token
6. Store new Refresh Token in DB
7. Set new cookies
```

#### POST `/api/v1/auth/logout`
- Revokes ALL refresh tokens for user (logout from all devices)
- Clears cookies

## Frontend Changes

### API Client (`frontend/src/js/lib/api-client.js`)

**New Features:**
- `credentials: 'include'` - Sendet Cookies mit jedem Request
- Automatic Token Refresh - Bei 401 Error wird automatisch Refresh Token verwendet
- Deduplication - Nur ein Refresh zur Zeit (parallel requests warten)

**Flow:**
```
1. Request fails with 401
2. Check if already refreshing -> if yes, wait
3. Call POST /api/v1/auth/refresh (automatic via cookie)
4. Retry original request
5. If refresh fails -> redirect to /login.html
```

**Implementation:**
```javascript
async request(endpoint, options = {}) {
    try {
        return await this._makeRequest(endpoint, options);
    } catch (error) {
        // If 401 and not already refreshing, try refresh
        if (error.message.includes('401') && !this.isRefreshing) {
            return await this._retryWithRefresh(endpoint, options);
        }
        throw error;
    }
}
```

### Auth API (`frontend/src/js/api/auth.js`)

**Updated Methods:**
- `refreshToken()` - No parameters needed (automatic via cookies)
- `logout()` - Revokes all tokens

## Security Features

### Token Security
✅ **Short-lived Access Tokens** - 15 min (vs. 60 min before)
✅ **Long-lived Refresh Tokens** - 7 days (good UX)
✅ **Token Rotation** - Old refresh token invalidated after use
✅ **Token Hashing** - Tokens stored as SHA256 hash
✅ **HttpOnly Cookies** - Prevents XSS attacks
✅ **SameSite Cookies** - Prevents CSRF attacks

### Database Security
✅ **Automatic TTL** - DynamoDB cleans up expired tokens
✅ **Revocation** - Tokens can be invalidated immediately
✅ **Multi-device support** - Users can have multiple refresh tokens

### CORS Configuration
✅ **Credentials allowed** - `allow_credentials=True`
✅ **Specific origins** - Not wildcard (*)
✅ **Secure cookies** - In production only HTTPS

## Testing

### Unit Tests (`tests/unit/test_refresh_token_repository.py`)
- Token creation
- Token hashing
- Token lookup via hash
- Token expiry
- Token revocation
- Revoke all for user

### Integration Tests (`tests/integration/test_refresh_token_flow.py`)
- Login returns refresh token
- Refresh endpoint works
- Token rotation (old token invalidated)
- Logout revokes all tokens
- Multiple refresh tokens per user (multi-device)
- Expired token handling
- Inactive user handling

## Running Tests

```bash
# Unit tests
cd backend
.venv/bin/pytest tests/unit/test_refresh_token_repository.py -v

# Integration tests
.venv/bin/pytest tests/integration/test_refresh_token_flow.py -v

# All auth tests
.venv/bin/pytest tests/ -k "refresh" -v
```

## Migration Notes

### Database
- **No migration needed** - GSI1 already exists in DynamoDB table
- TTL column already configured

### Frontend
- **No breaking changes** - Old code continues to work
- Cookies are now used instead of localStorage (more secure)
- Automatic token refresh improves UX (no manual refresh needed)

### Environment Variables
Add to `.env`:
```bash
# JWT Token Settings (already in config.py with defaults)
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
```

## Deployment Checklist

Backend:
- [x] Config: ACCESS_TOKEN_EXPIRE_MINUTES = 15
- [x] Config: REFRESH_TOKEN_EXPIRE_DAYS = 7
- [x] RefreshTokenRepository created
- [x] Auth endpoints updated (register, login, refresh, logout)
- [x] Token creation helpers (access + refresh)
- [x] Token verification helper
- [x] Unit tests created
- [x] Integration tests created

Frontend:
- [x] API Client: credentials: 'include'
- [x] API Client: Automatic token refresh
- [x] API Client: Deduplication logic
- [x] Auth API: Updated logout method

Infrastructure:
- [x] DynamoDB: GSI1 exists (for token lookup)
- [x] DynamoDB: TTL configured

Documentation:
- [x] Implementation guide (this file)
- [x] Security features documented
- [x] Testing guide
- [x] Migration notes

## Next Steps

1. **Test manually:**
   ```bash
   # Start backend
   cd backend
   .venv/bin/uvicorn app.main:app --reload
   
   # Start frontend
   cd frontend
   npm run dev
   
   # Test flow:
   1. Register/Login
   2. Wait 15 minutes (or change config to 1 min for testing)
   3. Make API request -> should auto-refresh
   4. Logout -> should clear all tokens
   ```

2. **Monitor in production:**
   - CloudWatch logs for refresh attempts
   - DynamoDB metrics for token queries
   - Failed refresh attempts (potential attacks)

3. **Optional enhancements:**
   - Refresh token usage tracking (detect suspicious activity)
   - Device fingerprinting (limit tokens per device)
   - Refresh token blacklist (for compromised tokens)
   - Email notification on new device login

## Security Considerations

### What this protects against:
✅ **XSS** - HttpOnly cookies prevent JavaScript access
✅ **CSRF** - SameSite cookies + CORS protection
✅ **Token theft** - Short-lived access tokens limit damage
✅ **Replay attacks** - Token rotation invalidates old tokens
✅ **Long-lived sessions** - Automatic logout after 7 days

### What this does NOT protect against:
❌ **Man-in-the-middle** - Requires HTTPS (enforced in production)
❌ **Compromised user credentials** - Use 2FA (future enhancement)
❌ **Device theft** - Require re-authentication for sensitive actions
❌ **Social engineering** - User education required

## References

- [OWASP JWT Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html)
- [RFC 6749 - OAuth 2.0](https://tools.ietf.org/html/rfc6749)
- [Auth0 - Refresh Tokens](https://auth0.com/docs/secure/tokens/refresh-tokens)

---

**Status:** ✅ Implementation Complete
**Author:** Claude Sonnet 4.5 + Andy
**Date:** 2026-05-17
