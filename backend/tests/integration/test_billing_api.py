"""Integration tests für Billing & Stripe Integration."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client(mock_dynamodb_table, mock_s3_bucket, mock_secrets_manager):
    """TestClient mit gemockten Dependencies."""
    from app.db.dynamodb import get_dynamodb_table
    from app.db.s3_storage import get_s3_storage, S3Storage

    app.dependency_overrides[get_dynamodb_table] = lambda: mock_dynamodb_table
    app.dependency_overrides[get_s3_storage] = lambda: S3Storage(bucket_name="overcloud-test-bucket")

    # Disable rate limiting for tests
    app.state.limiter.enabled = False

    yield TestClient(app)

    app.dependency_overrides.clear()
    app.state.limiter.enabled = True


class TestBillingPricing:
    """Tests für Pricing Endpoint."""

    def test_get_pricing(self, client):
        """Test pricing endpoint (public, no auth required)."""
        response = client.get("/api/v1/billing/pricing")

        assert response.status_code == 200
        data = response.json()

        # Should have 3 plans
        assert len(data) == 3

        # Check FREE plan
        free_plan = next(p for p in data if p["plan"] == "free")
        assert free_plan["monthly_price_eur"] == 0.0
        assert free_plan["yearly_price_eur"] == 0.0
        assert free_plan["yearly_discount_percent"] == 0.0

        # Check PRO plan
        pro_plan = next(p for p in data if p["plan"] == "pro")
        assert pro_plan["monthly_price_eur"] == 29.0
        assert pro_plan["yearly_price_eur"] == 290.0
        assert pro_plan["yearly_discount_percent"] > 16.0  # ~17% discount

        # Check ENTERPRISE plan
        enterprise_plan = next(p for p in data if p["plan"] == "enterprise")
        assert enterprise_plan["monthly_price_eur"] == 149.0
        assert enterprise_plan["yearly_price_eur"] == 1491.0
        assert enterprise_plan["yearly_discount_percent"] > 16.0


class TestBillingCheckout:
    """Tests für Checkout Endpoint."""

    def test_checkout_requires_auth(self, client):
        """Test checkout without auth returns 401."""
        response = client.post(
            "/api/v1/billing/00000000-0000-0000-0000-000000000000/checkout",
            json={
                "plan": "pro",
                "interval": "monthly",
                "auto_renewal": False,
                "success_url": "http://localhost/success",
                "cancel_url": "http://localhost/cancel"
            }
        )

        assert response.status_code == 401

    def test_checkout_stripe_disabled(self, client, monkeypatch):
        """Test checkout when Stripe is disabled."""
        # Register user
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "billing-test@example.com",
                "name": "Billing Test",
                "password": "Test1234!"
            }
        )
        assert register_response.status_code == 201

        token = register_response.json()["access_token"]
        user = register_response.json()["user"]
        org_id = user["personal_org_id"]

        # Disable Stripe
        from app import config
        monkeypatch.setattr(config.settings, "STRIPE_ENABLED", False)

        # Try checkout
        response = client.post(
            f"/api/v1/billing/{org_id}/checkout",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "plan": "pro",
                "interval": "monthly",
                "auto_renewal": False,
                "success_url": "http://localhost/success",
                "cancel_url": "http://localhost/cancel"
            }
        )

        assert response.status_code == 503
        assert "disabled" in response.json()["detail"].lower()

    def test_checkout_cannot_purchase_free_plan(self, client, monkeypatch):
        """Test that FREE plan cannot be purchased."""
        # Register user
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "free-test@example.com",
                "name": "Free Test",
                "password": "Test1234!"
            }
        )

        token = register_response.json()["access_token"]
        user = register_response.json()["user"]
        org_id = user["personal_org_id"]

        # Enable Stripe for test
        from app import config
        monkeypatch.setattr(config.settings, "STRIPE_ENABLED", True)

        # Try to "buy" FREE plan
        response = client.post(
            f"/api/v1/billing/{org_id}/checkout",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "plan": "free",
                "interval": "monthly",
                "auto_renewal": False,
                "success_url": "http://localhost/success",
                "cancel_url": "http://localhost/cancel"
            }
        )

        assert response.status_code == 400
        assert "cannot purchase free plan" in response.json()["detail"].lower()


class TestBillingSubscription:
    """Tests für Subscription Status."""

    def test_get_subscription_no_subscription(self, client):
        """Test subscription status when no subscription exists."""
        # Register user
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "nosub-test@example.com",
                "name": "NoSub Test",
                "password": "Test1234!"
            }
        )

        token = register_response.json()["access_token"]
        user = register_response.json()["user"]
        org_id = user["personal_org_id"]

        # Get subscription status
        response = client.get(
            f"/api/v1/billing/{org_id}/subscription",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["has_subscription"] is False
        assert data["plan"] == "free"
