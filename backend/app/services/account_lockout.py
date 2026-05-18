"""Account Lockout Service.

Tracks failed login attempts and locks accounts after threshold exceeded.
"""

import logging
from datetime import datetime, timedelta

from mypy_boto3_dynamodb.service_resource import Table

logger = logging.getLogger(__name__)


class AccountLockoutService:
    """Manages account lockout after failed login attempts."""

    # Configuration
    MAX_FAILED_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 15
    FAILED_ATTEMPTS_WINDOW_MINUTES = 30  # Reset counter after 30min of no attempts

    def __init__(self, table: Table):
        """Initialize service.

        Args:
            table: DynamoDB Table for storing lockout data
        """
        self.table = table

    def record_failed_login(self, email: str, ip_address: str) -> tuple[bool, int, datetime | None]:
        """Record failed login attempt.

        Args:
            email: User email (lowercased)
            ip_address: IP address of attempt

        Returns:
            (is_locked, failed_count, locked_until)
        """
        now = datetime.utcnow()
        email_lower = email.lower()

        # Get current lockout record
        lockout_data = self._get_lockout_data(email_lower)

        # Check if already locked
        if lockout_data and lockout_data.get("locked_until"):
            locked_until = datetime.fromisoformat(lockout_data["locked_until"])
            if now < locked_until:
                logger.warning(
                    f"Login attempt for locked account: {email_lower}",
                    extra={"email": email_lower, "ip": ip_address}
                )
                return True, lockout_data.get("failed_count", 0), locked_until

        # Check if we should reset counter (30min window expired)
        if lockout_data and lockout_data.get("last_failed_at"):
            last_failed = datetime.fromisoformat(lockout_data["last_failed_at"])
            if now - last_failed > timedelta(minutes=self.FAILED_ATTEMPTS_WINDOW_MINUTES):
                # Reset counter
                lockout_data["failed_count"] = 0

        # Increment failed attempts
        failed_count = lockout_data.get("failed_count", 0) + 1 if lockout_data else 1

        # Lock account if threshold exceeded
        locked_until = None
        if failed_count >= self.MAX_FAILED_ATTEMPTS:
            locked_until = now + timedelta(minutes=self.LOCKOUT_DURATION_MINUTES)
            logger.warning(
                f"Account locked: {email_lower} (too many failed attempts)",
                extra={"email": email_lower, "failed_count": failed_count}
            )

        # Save lockout data
        self._save_lockout_data(
            email_lower,
            failed_count=failed_count,
            last_failed_at=now,
            locked_until=locked_until,
            last_failed_ip=ip_address
        )

        return locked_until is not None, failed_count, locked_until

    def record_successful_login(self, email: str):
        """Clear failed attempts after successful login.

        Args:
            email: User email
        """
        email_lower = email.lower()

        # Delete lockout record
        try:
            self.table.delete_item(
                Key={
                    "PK": f"LOCKOUT#{email_lower}",
                    "SK": "METADATA"
                }
            )
            logger.info(f"Cleared lockout data for {email_lower}")
        except Exception as e:
            logger.error(f"Failed to clear lockout data: {e}")

    def is_account_locked(self, email: str) -> tuple[bool, datetime | None]:
        """Check if account is currently locked.

        Args:
            email: User email

        Returns:
            (is_locked, locked_until)
        """
        email_lower = email.lower()
        lockout_data = self._get_lockout_data(email_lower)

        if not lockout_data or not lockout_data.get("locked_until"):
            return False, None

        locked_until = datetime.fromisoformat(lockout_data["locked_until"])
        now = datetime.utcnow()

        if now >= locked_until:
            # Lockout expired, clear it
            self._save_lockout_data(
                email_lower,
                failed_count=0,
                last_failed_at=None,
                locked_until=None
            )
            return False, None

        return True, locked_until

    def unlock_account(self, email: str) -> bool:
        """Manually unlock account (admin action).

        Args:
            email: User email

        Returns:
            True if unlocked
        """
        email_lower = email.lower()

        try:
            self.table.delete_item(
                Key={
                    "PK": f"LOCKOUT#{email_lower}",
                    "SK": "METADATA"
                }
            )
            logger.info(f"Manually unlocked account: {email_lower}")
            return True
        except Exception as e:
            logger.error(f"Failed to unlock account: {e}")
            return False

    def _get_lockout_data(self, email_lower: str) -> dict | None:
        """Get lockout data for email."""
        try:
            response = self.table.get_item(
                Key={
                    "PK": f"LOCKOUT#{email_lower}",
                    "SK": "METADATA"
                }
            )
            return response.get("Item")
        except Exception:
            return None

    def _save_lockout_data(
        self,
        email_lower: str,
        failed_count: int,
        last_failed_at: datetime | None,
        locked_until: datetime | None,
        last_failed_ip: str = None
    ):
        """Save lockout data to DynamoDB."""
        now = datetime.utcnow().isoformat()

        item = {
            "PK": f"LOCKOUT#{email_lower}",
            "SK": "METADATA",
            "email": email_lower,
            "failed_count": failed_count,
            "created_at": now,
            "updated_at": now,
        }

        if last_failed_at:
            item["last_failed_at"] = last_failed_at.isoformat()

        if locked_until:
            item["locked_until"] = locked_until.isoformat()

        if last_failed_ip:
            item["last_failed_ip"] = last_failed_ip

        self.table.put_item(Item=item)


def get_account_lockout_service(table=None) -> AccountLockoutService:
    """Get AccountLockoutService instance (FastAPI dependency).

    Args:
        table: DynamoDB table (injected via Depends)
    """
    from app.db.dynamodb import get_dynamodb_table
    if table is None:
        table = get_dynamodb_table()
    return AccountLockoutService(table=table)
