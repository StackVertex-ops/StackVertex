"""Unit Tests für Voucher Service."""

import pytest
from unittest.mock import Mock, MagicMock
from uuid import uuid4
from datetime import datetime

from app.services.voucher_service import VoucherService
from app.repositories.voucher import VoucherRepository
from app.repositories.subscription import SubscriptionRepository


@pytest.fixture
def mock_voucher_repo():
    """Mock VoucherRepository."""
    return Mock(spec=VoucherRepository)


@pytest.fixture
def mock_subscription_repo():
    """Mock SubscriptionRepository."""
    return Mock(spec=SubscriptionRepository)


@pytest.fixture
def voucher_service(mock_voucher_repo, mock_subscription_repo):
    """VoucherService mit Mocks."""
    return VoucherService(
        voucher_repo=mock_voucher_repo,
        subscription_repo=mock_subscription_repo
    )


def test_validate_voucher_success(voucher_service, mock_voucher_repo):
    """Test erfolgreiche Validierung."""
    user_id = uuid4()
    mock_voucher_repo.validate.return_value = {
        "valid": True,
        "code": "FRIEND2026",
        "discount_type": "percentage",
        "discount_value": 50,
        "applies_to": "both",
        "remaining_uses": 10
    }

    result = voucher_service.validate_voucher("FRIEND2026", user_id)

    assert result["valid"] is True
    assert result["code"] == "FRIEND2026"
    mock_voucher_repo.validate.assert_called_once_with("FRIEND2026", user_id)


def test_validate_voucher_invalid(voucher_service, mock_voucher_repo):
    """Test Validierung schlägt fehl."""
    user_id = uuid4()
    mock_voucher_repo.validate.side_effect = ValueError("Voucher expired")

    with pytest.raises(ValueError, match="expired"):
        voucher_service.validate_voucher("EXPIRED", user_id)


def test_apply_discount_no_voucher(voucher_service):
    """Test Discount-Berechnung ohne Voucher."""
    result = voucher_service.apply_discount(
        base_price=50.0,
        aws_costs=100.0,
        aws_percentage=10.0,
        voucher_code=None,
        user_id=None
    )

    assert result["base_price"] == 50.0
    assert result["aws_costs"] == 100.0
    assert result["aws_markup"] == 10.0  # 10% von 100
    assert result["subtotal"] == 60.0
    assert result["discount_applied"] is False
    assert result["discount_amount"] == 0.0
    assert result["final_subtotal"] == 60.0


def test_apply_discount_percentage_base_fee(voucher_service, mock_voucher_repo):
    """Test Percentage Discount auf Base Fee."""
    user_id = uuid4()

    mock_voucher_repo.validate.return_value = {
        "valid": True,
        "code": "BASE50",
        "discount_type": "percentage",
        "discount_value": 50,
        "applies_to": "base_fee",
        "remaining_uses": 10
    }

    result = voucher_service.apply_discount(
        base_price=100.0,
        aws_costs=200.0,
        aws_percentage=10.0,  # 10% von 200 = 20
        voucher_code="BASE50",
        user_id=user_id
    )

    # Base: 100, AWS Markup: 20, Total: 120
    # Discount: 50% von Base (100) = 50
    # Final: 120 - 50 = 70

    assert result["base_price"] == 100.0
    assert result["aws_markup"] == 20.0
    assert result["subtotal"] == 120.0
    assert result["discount_applied"] is True
    assert result["discount_type"] == "percentage"
    assert result["discount_value"] == 50
    assert result["discount_amount"] == 50.0
    assert result["applies_to"] == "base_fee"
    assert result["final_subtotal"] == 70.0


def test_apply_discount_percentage_aws_percentage(voucher_service, mock_voucher_repo):
    """Test Percentage Discount auf AWS Markup."""
    user_id = uuid4()

    mock_voucher_repo.validate.return_value = {
        "valid": True,
        "code": "AWS25",
        "discount_type": "percentage",
        "discount_value": 25,
        "applies_to": "aws_percentage",
        "remaining_uses": 10
    }

    result = voucher_service.apply_discount(
        base_price=50.0,
        aws_costs=100.0,
        aws_percentage=20.0,  # 20% von 100 = 20
        voucher_code="AWS25",
        user_id=user_id
    )

    # Base: 50, AWS Markup: 20, Total: 70
    # Discount: 25% von AWS Markup (20) = 5
    # Final: 70 - 5 = 65

    assert result["subtotal"] == 70.0
    assert result["discount_amount"] == 5.0
    assert result["final_subtotal"] == 65.0


def test_apply_discount_percentage_both(voucher_service, mock_voucher_repo):
    """Test Percentage Discount auf beide."""
    user_id = uuid4()

    mock_voucher_repo.validate.return_value = {
        "valid": True,
        "code": "BOTH50",
        "discount_type": "percentage",
        "discount_value": 50,
        "applies_to": "both",
        "remaining_uses": 10
    }

    result = voucher_service.apply_discount(
        base_price=100.0,
        aws_costs=200.0,
        aws_percentage=10.0,  # 10% von 200 = 20
        voucher_code="BOTH50",
        user_id=user_id
    )

    # Base: 100, AWS Markup: 20, Total: 120
    # Discount: 50% von Total (120) = 60
    # Final: 120 - 60 = 60

    assert result["subtotal"] == 120.0
    assert result["discount_amount"] == 60.0
    assert result["final_subtotal"] == 60.0


def test_apply_discount_fixed_amount(voucher_service, mock_voucher_repo):
    """Test Fixed Amount Discount."""
    user_id = uuid4()

    mock_voucher_repo.validate.return_value = {
        "valid": True,
        "code": "FIXED25",
        "discount_type": "fixed",
        "discount_value": 25,
        "applies_to": "both",
        "remaining_uses": 10
    }

    result = voucher_service.apply_discount(
        base_price=50.0,
        aws_costs=100.0,
        aws_percentage=10.0,  # 10% von 100 = 10
        voucher_code="FIXED25",
        user_id=user_id
    )

    # Base: 50, AWS Markup: 10, Total: 60
    # Discount: Fixed 25 EUR
    # Final: 60 - 25 = 35

    assert result["subtotal"] == 60.0
    assert result["discount_type"] == "fixed"
    assert result["discount_amount"] == 25.0
    assert result["final_subtotal"] == 35.0


def test_apply_discount_fixed_amount_exceeds_target(voucher_service, mock_voucher_repo):
    """Test Fixed Discount größer als Target (sollte auf Target begrenzt werden)."""
    user_id = uuid4()

    mock_voucher_repo.validate.return_value = {
        "valid": True,
        "code": "FIXED100",
        "discount_type": "fixed",
        "discount_value": 100,
        "applies_to": "base_fee",
        "remaining_uses": 10
    }

    result = voucher_service.apply_discount(
        base_price=50.0,  # Target ist nur 50
        aws_costs=100.0,
        aws_percentage=10.0,
        voucher_code="FIXED100",
        user_id=user_id
    )

    # Discount sollte auf Base Fee (50) begrenzt werden
    assert result["discount_amount"] == 50.0
    assert result["final_subtotal"] == 10.0  # 60 - 50 = 10


def test_apply_discount_100_percent(voucher_service, mock_voucher_repo):
    """Test 100% Discount (kostenfrei)."""
    user_id = uuid4()

    mock_voucher_repo.validate.return_value = {
        "valid": True,
        "code": "BETA100",
        "discount_type": "percentage",
        "discount_value": 100,
        "applies_to": "both",
        "remaining_uses": 50
    }

    result = voucher_service.apply_discount(
        base_price=50.0,
        aws_costs=100.0,
        aws_percentage=10.0,
        voucher_code="BETA100",
        user_id=user_id
    )

    # 100% Discount = 60 EUR Rabatt
    assert result["discount_amount"] == 60.0
    assert result["final_subtotal"] == 0.0


def test_apply_discount_invalid_voucher_returns_no_discount(voucher_service, mock_voucher_repo):
    """Test dass bei ungültigem Voucher kein Rabatt angewendet wird."""
    user_id = uuid4()

    mock_voucher_repo.validate.side_effect = ValueError("Voucher expired")

    result = voucher_service.apply_discount(
        base_price=50.0,
        aws_costs=100.0,
        aws_percentage=10.0,
        voucher_code="EXPIRED",
        user_id=user_id
    )

    # Sollte ohne Rabatt zurückkommen (aber kein Exception werfen)
    assert result["discount_applied"] is False
    assert result["final_subtotal"] == 60.0
    assert "voucher_error" in result


def test_redeem_voucher_success(voucher_service, mock_voucher_repo, mock_subscription_repo):
    """Test erfolgreiche Voucher-Verwendung."""
    user_id = uuid4()
    org_id = uuid4()

    # Mock validate
    mock_voucher_repo.validate.return_value = {
        "valid": True,
        "code": "FRIEND2026",
        "discount_type": "percentage",
        "discount_value": 50,
        "applies_to": "both",
        "remaining_uses": 10
    }

    # Mock get_by_org
    mock_subscription_repo.get_by_org.return_value = {
        "id": "sub123",
        "org_id": str(org_id),
        "tier": "pro",
        "base_price": 50.0,
        "voucher_code": None  # Kein Voucher bisher
    }

    # Mock _update_item
    mock_subscription_repo._update_item.return_value = {
        "id": "sub123",
        "voucher_code": "FRIEND2026"
    }

    result = voucher_service.redeem_voucher("FRIEND2026", user_id, org_id)

    # Asserts
    mock_voucher_repo.validate.assert_called_once()
    mock_voucher_repo.redeem.assert_called_once_with("FRIEND2026", user_id)
    mock_subscription_repo._update_item.assert_called_once()

    assert result["voucher_code"] == "FRIEND2026"


def test_redeem_voucher_no_subscription(voucher_service, mock_voucher_repo, mock_subscription_repo):
    """Test Redeem schlägt fehl wenn keine Subscription existiert."""
    user_id = uuid4()
    org_id = uuid4()

    mock_voucher_repo.validate.return_value = {"valid": True}
    mock_subscription_repo.get_by_org.return_value = None

    with pytest.raises(ValueError, match="No subscription found"):
        voucher_service.redeem_voucher("CODE", user_id, org_id)


def test_redeem_voucher_already_has_voucher(voucher_service, mock_voucher_repo, mock_subscription_repo):
    """Test Redeem schlägt fehl wenn Subscription bereits Voucher hat."""
    user_id = uuid4()
    org_id = uuid4()

    mock_voucher_repo.validate.return_value = {"valid": True}
    mock_subscription_repo.get_by_org.return_value = {
        "id": "sub123",
        "voucher_code": "EXISTING"  # Bereits ein Voucher vorhanden
    }

    with pytest.raises(ValueError, match="already has voucher"):
        voucher_service.redeem_voucher("NEWCODE", user_id, org_id)


def test_remove_voucher_from_subscription(voucher_service, mock_subscription_repo):
    """Test Voucher-Entfernung von Subscription."""
    org_id = uuid4()

    mock_subscription_repo.get_by_org.return_value = {
        "id": "sub123",
        "voucher_code": "FRIEND2026"
    }

    mock_subscription_repo._update_item.return_value = {
        "id": "sub123",
        "voucher_code": None
    }

    result = voucher_service.remove_voucher_from_subscription(org_id)

    mock_subscription_repo._update_item.assert_called_once()
    assert result["voucher_code"] is None


def test_calculate_subscription_price_with_voucher(voucher_service, mock_subscription_repo, mock_voucher_repo):
    """Test Gesamtberechnung mit Voucher."""
    org_id = uuid4()
    user_id = uuid4()

    # Mock subscription mit Voucher
    mock_subscription_repo.get_by_org.return_value = {
        "id": "sub123",
        "base_price": 50.0,
        "aws_cost_percentage": 10.0,
        "voucher_code": "FRIEND2026",
        "voucher_discount_type": "percentage",
        "voucher_discount_value": 50,
        "voucher_applies_to": "both",
        "voucher_applied_by": str(user_id)
    }

    # Mock validate
    mock_voucher_repo.validate.return_value = {
        "valid": True,
        "code": "FRIEND2026",
        "discount_type": "percentage",
        "discount_value": 50,
        "applies_to": "both",
        "remaining_uses": 5
    }

    result = voucher_service.calculate_subscription_price_with_voucher(
        org_id=org_id,
        aws_costs=100.0
    )

    # Base: 50, AWS Markup: 10, Total: 60
    # Discount: 50% = 30
    # Final: 30

    assert result["subtotal"] == 60.0
    assert result["discount_amount"] == 30.0
    assert result["final_subtotal"] == 30.0
