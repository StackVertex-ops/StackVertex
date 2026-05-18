"""Unit Tests für Voucher Repository."""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from moto import mock_aws
import boto3

from app.repositories.voucher import VoucherRepository


@pytest.fixture
def dynamodb_table():
    """Create mock DynamoDB table."""
    with mock_aws():
        # Create DynamoDB resource
        dynamodb = boto3.resource('dynamodb', region_name='eu-central-1')

        # Create table
        table = dynamodb.create_table(
            TableName='overcloud-test',
            KeySchema=[
                {'AttributeName': 'PK', 'KeyType': 'HASH'},
                {'AttributeName': 'SK', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'PK', 'AttributeType': 'S'},
                {'AttributeName': 'SK', 'AttributeType': 'S'},
                {'AttributeName': 'GSI1PK', 'AttributeType': 'S'},
                {'AttributeName': 'GSI1SK', 'AttributeType': 'S'},
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'GSI1',
                    'KeySchema': [
                        {'AttributeName': 'GSI1PK', 'KeyType': 'HASH'},
                        {'AttributeName': 'GSI1SK', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )

        yield table


@pytest.fixture
def voucher_repo(dynamodb_table):
    """Create VoucherRepository instance."""
    return VoucherRepository(table=dynamodb_table)


def test_create_voucher_success(voucher_repo):
    """Test erfolgreiche Voucher-Erstellung."""
    admin_id = uuid4()

    voucher = voucher_repo.create(
        code="FRIEND2026",
        discount_type="percentage",
        discount_value=50,
        applies_to="both",
        max_uses=100,
        created_by=admin_id
    )

    assert voucher["code"] == "FRIEND2026"
    assert voucher["discount_type"] == "percentage"
    assert voucher["discount_value"] == 50
    assert voucher["applies_to"] == "both"
    assert voucher["max_uses"] == 100
    assert voucher["current_uses"] == 0
    assert voucher["is_active"] is True
    assert voucher["created_by"] == str(admin_id)


def test_create_voucher_uppercase_conversion(voucher_repo):
    """Test dass Code automatisch uppercase wird."""
    voucher = voucher_repo.create(
        code="friend2026",
        discount_type="percentage",
        discount_value=25,
        applies_to="base_fee",
        max_uses=1
    )

    assert voucher["code"] == "FRIEND2026"


def test_create_voucher_duplicate_code(voucher_repo):
    """Test dass duplicate Code rejected wird."""
    voucher_repo.create(
        code="DUPLICATE",
        discount_type="percentage",
        discount_value=10,
        applies_to="base_fee",
        max_uses=1
    )

    # Zweiter Versuch sollte fehlschlagen
    with pytest.raises(ValueError, match="already exists"):
        voucher_repo.create(
            code="DUPLICATE",
            discount_type="percentage",
            discount_value=20,
            applies_to="both",
            max_uses=1
        )


def test_create_voucher_invalid_code_length(voucher_repo):
    """Test Validierung der Code-Länge."""
    # Zu kurz
    with pytest.raises(ValueError, match="between 4 and 32 characters"):
        voucher_repo.create(
            code="ABC",
            discount_type="percentage",
            discount_value=10,
            applies_to="base_fee",
            max_uses=1
        )

    # Zu lang
    with pytest.raises(ValueError, match="between 4 and 32 characters"):
        voucher_repo.create(
            code="A" * 33,
            discount_type="percentage",
            discount_value=10,
            applies_to="base_fee",
            max_uses=1
        )


def test_create_voucher_invalid_characters(voucher_repo):
    """Test dass nur alphanumerische Zeichen erlaubt sind."""
    with pytest.raises(ValueError, match="only A-Z and 0-9"):
        voucher_repo.create(
            code="FRIEND-2026",  # Bindestrich nicht erlaubt
            discount_type="percentage",
            discount_value=10,
            applies_to="base_fee",
            max_uses=1
        )


def test_create_voucher_invalid_discount_value(voucher_repo):
    """Test Validierung des Discount-Wertes."""
    # Negativ
    with pytest.raises(ValueError, match="greater than 0"):
        voucher_repo.create(
            code="INVALID",
            discount_type="percentage",
            discount_value=-10,
            applies_to="base_fee",
            max_uses=1
        )

    # Percentage über 100%
    with pytest.raises(ValueError, match="cannot exceed 100%"):
        voucher_repo.create(
            code="INVALID",
            discount_type="percentage",
            discount_value=150,
            applies_to="base_fee",
            max_uses=1
        )


def test_create_voucher_with_date_range(voucher_repo):
    """Test Voucher mit Zeitfenster."""
    valid_from = datetime(2026, 6, 1)
    valid_until = datetime(2026, 12, 31)

    voucher = voucher_repo.create(
        code="SUMMER2026",
        discount_type="percentage",
        discount_value=25,
        applies_to="both",
        max_uses=-1,  # Unbegrenzt
        valid_from=valid_from,
        valid_until=valid_until
    )

    assert voucher["valid_from"] == valid_from.isoformat()
    assert voucher["valid_until"] == valid_until.isoformat()


def test_get_by_code_case_insensitive(voucher_repo):
    """Test case-insensitive Lookup."""
    voucher_repo.create(
        code="TESTCODE",
        discount_type="percentage",
        discount_value=10,
        applies_to="base_fee",
        max_uses=1
    )

    # Alle Varianten sollten funktionieren
    assert voucher_repo.get_by_code("TESTCODE") is not None
    assert voucher_repo.get_by_code("testcode") is not None
    assert voucher_repo.get_by_code("TestCode") is not None


def test_validate_voucher_success(voucher_repo):
    """Test erfolgreiche Validierung."""
    user_id = uuid4()

    voucher_repo.create(
        code="VALID",
        discount_type="percentage",
        discount_value=50,
        applies_to="both",
        max_uses=10
    )

    result = voucher_repo.validate("VALID", user_id)

    assert result["valid"] is True
    assert result["code"] == "VALID"
    assert result["discount_value"] == 50
    assert result["remaining_uses"] == 10


def test_validate_voucher_not_found(voucher_repo):
    """Test Validierung für nicht existierenden Code."""
    with pytest.raises(ValueError, match="not found"):
        voucher_repo.validate("NOTEXIST", uuid4())


def test_validate_voucher_inactive(voucher_repo):
    """Test dass inaktiver Voucher rejected wird."""
    user_id = uuid4()

    voucher_repo.create(
        code="INACTIVE",
        discount_type="percentage",
        discount_value=10,
        applies_to="base_fee",
        max_uses=1
    )

    # Deaktiviere Voucher
    voucher_repo.deactivate("INACTIVE")

    # Validierung sollte fehlschlagen
    with pytest.raises(ValueError, match="deactivated"):
        voucher_repo.validate("INACTIVE", user_id)


def test_validate_voucher_expired(voucher_repo):
    """Test dass abgelaufener Voucher rejected wird."""
    user_id = uuid4()

    # Erstelle Voucher direkt in DynamoDB (bypass validation)
    expired_date = datetime.utcnow() - timedelta(days=1)
    voucher_repo.table.put_item(
        Item={
            'PK': 'VOUCHER#EXPIRED',
            'SK': 'METADATA',
            'code': 'EXPIRED',
            'discount_type': 'percentage',
            'discount_value': 10,
            'applies_to': 'base_fee',
            'max_uses': 1,
            'current_uses': 0,
            'is_active': True,
            'valid_until': expired_date.isoformat(),
            'created_at': datetime.utcnow().isoformat(),
            'used_by': [],
            'GSI1PK': 'VOUCHERS',
            'GSI1SK': 'EXPIRED'
        }
    )

    with pytest.raises(ValueError, match="expired"):
        voucher_repo.validate("EXPIRED", user_id)


def test_validate_voucher_not_yet_valid(voucher_repo):
    """Test dass zukünftiger Voucher rejected wird."""
    user_id = uuid4()

    # Voucher der erst morgen gültig wird
    voucher_repo.create(
        code="FUTURE",
        discount_type="percentage",
        discount_value=10,
        applies_to="base_fee",
        max_uses=1,
        valid_from=datetime.utcnow() + timedelta(days=1)
    )

    with pytest.raises(ValueError, match="not yet valid"):
        voucher_repo.validate("FUTURE", user_id)


def test_validate_voucher_usage_limit_reached(voucher_repo):
    """Test dass Voucher mit erreichtem Limit rejected wird."""
    user1 = uuid4()
    user2 = uuid4()

    voucher_repo.create(
        code="LIMITED",
        discount_type="percentage",
        discount_value=10,
        applies_to="base_fee",
        max_uses=1
    )

    # Erster User verwendet Voucher
    voucher_repo.redeem("LIMITED", user1)

    # Zweiter User sollte nicht mehr verwenden können
    with pytest.raises(ValueError, match="usage limit reached"):
        voucher_repo.validate("LIMITED", user2)


def test_validate_voucher_already_used_by_user(voucher_repo):
    """Test dass User Voucher nicht zweimal verwenden kann."""
    user_id = uuid4()

    voucher_repo.create(
        code="ONCEPER",
        discount_type="percentage",
        discount_value=10,
        applies_to="base_fee",
        max_uses=100  # Viele Uses, aber User darf nur 1x
    )

    # Erster Redeem
    voucher_repo.redeem("ONCEPER", user_id)

    # Zweiter Versuch sollte fehlschlagen
    with pytest.raises(ValueError, match="already used"):
        voucher_repo.validate("ONCEPER", user_id)


def test_redeem_voucher_success(voucher_repo):
    """Test erfolgreiche Voucher-Verwendung."""
    user_id = uuid4()

    voucher_repo.create(
        code="REDEEM",
        discount_type="percentage",
        discount_value=25,
        applies_to="both",
        max_uses=10
    )

    updated = voucher_repo.redeem("REDEEM", user_id)

    assert updated["current_uses"] == 1
    assert str(user_id) in updated["used_by"]
    assert "last_used_at" in updated


def test_redeem_voucher_increments_uses(voucher_repo):
    """Test dass current_uses korrekt inkrementiert wird."""
    voucher_repo.create(
        code="MULTI",
        discount_type="percentage",
        discount_value=10,
        applies_to="base_fee",
        max_uses=3
    )

    # 3 verschiedene User verwenden Voucher
    for i in range(3):
        user_id = uuid4()
        voucher_repo.redeem("MULTI", user_id)

    voucher = voucher_repo.get_by_code("MULTI")
    assert voucher["current_uses"] == 3

    # 4. Versuch sollte fehlschlagen
    with pytest.raises(ValueError, match="usage limit reached"):
        voucher_repo.validate("MULTI", uuid4())


def test_list_all_vouchers(voucher_repo):
    """Test Listing aller Vouchers."""
    # Erstelle mehrere Vouchers
    voucher_repo.create(code="VOUCHER1", discount_type="percentage", discount_value=10, applies_to="base_fee", max_uses=1)
    voucher_repo.create(code="VOUCHER2", discount_type="percentage", discount_value=25, applies_to="both", max_uses=1)
    voucher_repo.create(code="VOUCHER3", discount_type="fixed", discount_value=50, applies_to="base_fee", max_uses=1)

    vouchers, total = voucher_repo.list_all()

    assert len(vouchers) == 3
    assert total == 3


def test_list_all_vouchers_exclude_inactive(voucher_repo):
    """Test dass inaktive Vouchers standardmäßig nicht gelistet werden."""
    voucher_repo.create(code="ACTIVE", discount_type="percentage", discount_value=10, applies_to="base_fee", max_uses=1)
    voucher_repo.create(code="INACTIVE", discount_type="percentage", discount_value=25, applies_to="both", max_uses=1)

    # Deaktiviere einen
    voucher_repo.deactivate("INACTIVE")

    # Ohne include_inactive sollte nur ACTIVE kommen
    vouchers, total = voucher_repo.list_all(include_inactive=False)
    assert len(vouchers) == 1
    assert vouchers[0]["code"] == "ACTIVE"

    # Mit include_inactive sollten beide kommen
    vouchers, total = voucher_repo.list_all(include_inactive=True)
    assert len(vouchers) == 2


def test_deactivate_voucher(voucher_repo):
    """Test Voucher-Deaktivierung."""
    voucher_repo.create(code="DEACT", discount_type="percentage", discount_value=10, applies_to="base_fee", max_uses=1)

    updated = voucher_repo.deactivate("DEACT")

    assert updated["is_active"] is False
    assert "deactivated_at" in updated


def test_reactivate_voucher(voucher_repo):
    """Test Voucher-Reaktivierung."""
    voucher_repo.create(code="REACT", discount_type="percentage", discount_value=10, applies_to="base_fee", max_uses=1)

    # Deaktiviere
    voucher_repo.deactivate("REACT")

    # Reaktiviere
    updated = voucher_repo.reactivate("REACT")

    assert updated["is_active"] is True
    assert "reactivated_at" in updated


def test_get_usage_stats(voucher_repo):
    """Test Nutzungsstatistiken."""
    voucher_repo.create(
        code="STATS",
        discount_type="percentage",
        discount_value=10,
        applies_to="base_fee",
        max_uses=10
    )

    # 3 User verwenden Voucher
    for i in range(3):
        voucher_repo.redeem("STATS", uuid4())

    stats = voucher_repo.get_usage_stats("STATS")

    assert stats["code"] == "STATS"
    assert stats["max_uses"] == 10
    assert stats["current_uses"] == 3
    assert stats["remaining_uses"] == 7
    assert stats["usage_percentage"] == 30.0
    assert stats["unique_users"] == 3
    assert stats["is_active"] is True
