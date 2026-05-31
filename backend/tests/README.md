# StackVertex Backend Tests

## Test Coverage Status

### ✅ Existing Tests

**API Tests:**
- `tests/api/test_faq.py` - FAQ endpoints
- `tests/api/test_feedback.py` - Feedback endpoints
- `tests/api/test_reviews.py` - Reviews endpoints

**Repository Tests:**
- Coverage: ~60% der Repositories

**Utility Tests:**
- Password hashing, validation
- JSON schema validation

### ❌ Missing Tests (High Priority)

**Authentication:**
- [ ] `test_auth.py` - Login, Register, Refresh Token
- [ ] `test_auth_guard.py` - Protected endpoints require auth
- [ ] `test_admin_creation.py` - SuperAdmin creation security

**Core API:**
- [ ] `test_architectures_api.py` - CRUD operations + Auth
- [ ] `test_deployments_api.py` - Deploy, Status, Logs + Auth
- [ ] `test_terraform_api.py` - Generation, Validation + Auth

**Security:**
- [ ] `test_jwt_validation.py` - Token expiry, invalid tokens
- [ ] `test_rbac.py` - Role-based access control
- [ ] `test_rate_limiting.py` - API rate limits

## Running Tests

### All Tests
```bash
cd backend
poetry run pytest
```

### Specific Test File
```bash
poetry run pytest tests/api/test_auth.py -v
```

### With Coverage
```bash
poetry run pytest --cov=app --cov-report=html
open htmlcov/index.html
```

### Integration Tests Only
```bash
poetry run pytest -m integration
```

### Unit Tests Only
```bash
poetry run pytest -m "not integration"
```

## Writing Tests for Auth-Protected Endpoints

### Setup Test Client with Authentication

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.api.dependencies import get_current_user

# Override auth dependency for testing
async def override_get_current_user():
    return {
        "id": "test-user-id",
        "email": "test@example.com",
        "name": "Test User",
        "system_role": "user",
        "status": "active"
    }

@pytest.fixture
def authenticated_client():
    app.dependency_overrides[get_current_user] = override_get_current_user
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()
```

### Example Test

```python
def test_create_architecture_requires_auth(client):
    """Test that creating architecture requires authentication."""
    response = client.post(
        "/architectures",
        json={
            "version": "1.0.0",
            "metadata": {"name": "Test", "provider": "aws"},
            "architecture": {"components": []}
        }
    )
    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"]

def test_create_architecture_authenticated(authenticated_client):
    """Test creating architecture with valid auth."""
    response = authenticated_client.post(
        "/architectures",
        json={
            "version": "1.0.0",
            "metadata": {"name": "Test", "provider": "aws"},
            "architecture": {"components": []}
        }
    )
    assert response.status_code == 201
    assert response.json()["metadata"]["name"] == "Test"
```

## Test Data

### Mock Users

```python
MOCK_ADMIN = {
    "id": "admin-id",
    "email": "admin@stackvertex.io",
    "system_role": "superadmin",
    "status": "active"
}

MOCK_USER = {
    "id": "user-id",
    "email": "user@example.com",
    "system_role": "user",
    "status": "active"
}
```

### Mock Architectures

Use `app.schemas.architecture.ArchitectureCreate` for valid test data.

## CI/CD Integration

### GitHub Actions

Tests run automatically on:
- Every push to `develop`, `staging`, `main`
- Every pull request

### Pre-commit Hooks

Run tests before committing:
```bash
poetry run pytest --maxfail=1
```

## Coverage Goals

- **Critical Paths**: 90%+ (Auth, Deployments, Billing)
- **API Endpoints**: 80%+
- **Repositories**: 80%+
- **Utilities**: 100%

## Known Issues

### DynamoDB Local

Some tests require DynamoDB Local:
```bash
docker run -p 8000:8000 amazon/dynamodb-local
export DYNAMODB_ENDPOINT=http://localhost:8000
```

### AWS Mocking

Use `moto` for mocking AWS services:
```python
from moto import mock_dynamodb, mock_s3

@mock_dynamodb
def test_with_mock_dynamodb():
    # Test code
    pass
```

## Next Steps

1. **Phase 1** (High Priority):
   - Auth tests (login, register, protected endpoints)
   - Architecture API tests
   - Deployment API tests

2. **Phase 2** (Medium Priority):
   - Terraform generation tests
   - Cost estimation tests
   - RBAC tests

3. **Phase 3** (Nice to Have):
   - Performance tests
   - Load tests
   - End-to-end tests

## Contributing

When adding new features:
1. Write tests FIRST (TDD)
2. Ensure 80%+ coverage for new code
3. Add integration tests for critical paths
4. Update this README with new test categories
