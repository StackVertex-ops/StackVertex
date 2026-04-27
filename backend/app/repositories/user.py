"""UserRepository - DynamoDB User Management.

Handles User CRUD operations with DynamoDB Single Table Design.
"""

import logging
from datetime import datetime
from typing import Optional, List, Tuple
from uuid import UUID, uuid4

from boto3.dynamodb.conditions import Key, Attr
from mypy_boto3_dynamodb.service_resource import Table
from passlib.context import CryptContext

from app.repositories.base import BaseRepository
from app.models.user import AuthProvider, UserRole, UserStatus
from app.models.organisation import OrganisationPlan, OrganisationType

logger = logging.getLogger(__name__)

# Password Hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserRepository(BaseRepository):
    """Repository für User Management."""

    def __init__(self, table: Table):
        """Initialize UserRepository.

        Args:
            table: DynamoDB Table Resource
        """
        super().__init__(table)

    # ========================================================================
    # Create
    # ========================================================================

    def create(
        self,
        email: str,
        name: str,
        password: str,
        auth_provider: AuthProvider = AuthProvider.EMAIL,
        auth_provider_id: Optional[str] = None,
    ) -> dict:
        """Create new user mit auto-created personal organisation.

        Args:
            email: User email (unique)
            name: Display name
            password: Plain password (wird gehasht)
            auth_provider: OAuth provider oder email
            auth_provider_id: OAuth provider user ID

        Returns:
            User item (DynamoDB format)
        """
        user_id = uuid4()
        personal_org_id = uuid4()
        now = datetime.utcnow().isoformat()

        # Hash password (bcrypt has 72-byte limit)
        password_truncated = password[:72] if len(password) > 72 else password
        password_hash = pwd_context.hash(password_truncated)

        # User Item
        user_item = {
            "PK": f"USER#{str(user_id)}",
            "SK": "METADATA",
            "id": str(user_id),
            "email": email.lower(),  # lowercase for case-insensitive lookup
            "name": name,
            "password_hash": password_hash,
            "auth_provider": auth_provider.value,
            "auth_provider_id": auth_provider_id,
            "status": UserStatus.ACTIVE.value,
            "personal_org_id": str(personal_org_id),
            "created_at": now,
            "updated_at": now,
            # GSI1: Query by email
            "GSI1PK": "user_by_email",
            "GSI1SK": email.lower(),
        }

        # Personal Organisation Item (auto-created)
        personal_org_item = {
            "PK": f"ORG#{str(personal_org_id)}",
            "SK": "METADATA",
            "id": str(personal_org_id),
            "name": f"{name}'s Organisation",
            "type": OrganisationType.PERSONAL.value,
            "owner_user_id": str(user_id),
            "plan": OrganisationPlan.FREE.value,
            "status": "active",
            "created_at": now,
            "updated_at": now,
            "quota": {
                "active_deployments": 0,
                "members": 1,
                "architectures": 0,
            },
            # GSI1: Query all organisations
            "GSI1PK": "organisation",
            "GSI1SK": str(personal_org_id),
            # GSI2: Query by owner
            "GSI2PK": f"owner#{str(user_id)}",
            "GSI2SK": str(personal_org_id),
        }

        # User-Organisation Membership Item
        membership_item = {
            "PK": f"ORG#{str(personal_org_id)}",
            "SK": f"USER#{str(user_id)}",
            "user_id": str(user_id),
            "email": email.lower(),
            "name": name,
            "role": UserRole.OWNER.value,
        }

        # Reverse Membership (USER → ORG)
        reverse_membership_item = {
            "PK": f"USER#{str(user_id)}",
            "SK": f"ORG#{str(personal_org_id)}",
            "org_id": str(personal_org_id),
            "org_name": personal_org_item["name"],
            "role": UserRole.OWNER.value,
        }

        # Batch write all items
        self._batch_write_items(
            items=[user_item, personal_org_item, membership_item, reverse_membership_item]
        )

        logger.info(
            f"Created user {user_id} with personal org {personal_org_id}",
            extra={"user_id": str(user_id), "email": email}
        )

        return user_item

    # ========================================================================
    # Read
    # ========================================================================

    def get(self, user_id: UUID) -> Optional[dict]:
        """Get user by ID.

        Args:
            user_id: User UUID

        Returns:
            User item or None
        """
        return self._get_item(f"USER#{str(user_id)}", "METADATA")

    def get_by_email(self, email: str) -> Optional[dict]:
        """Get user by email (case-insensitive).

        Args:
            email: User email

        Returns:
            User item or None
        """
        # Query GSI1: user_by_email
        items, _ = self._query(
            key_condition=Key("GSI1PK").eq("user_by_email") & Key("GSI1SK").eq(email.lower()),
            index_name="GSI1",
            limit=1
        )

        return items[0] if items else None

    def get_organisations(self, user_id: UUID) -> List[dict]:
        """Get all organisations this user is member of.

        Args:
            user_id: User UUID

        Returns:
            List of organisation membership items
        """
        # Query all ORG# items for this user
        items, _ = self._query(
            key_condition=Key("PK").eq(f"USER#{str(user_id)}") & Key("SK").begins_with("ORG#")
        )

        return items

    # ========================================================================
    # Update
    # ========================================================================

    def update(self, user_id: UUID, updates: dict) -> Optional[dict]:
        """Update user profile.

        Args:
            user_id: User UUID
            updates: Fields to update (name, etc.)

        Returns:
            Updated user item or None if not found
        """
        # Remove fields that shouldn't be updated via this method
        updates.pop("password_hash", None)
        updates.pop("email", None)  # Email change requires verification
        updates.pop("id", None)
        updates.pop("created_at", None)

        if not updates:
            return self.get(user_id)

        return self._update_item(
            f"USER#{str(user_id)}",
            "METADATA",
            updates
        )

    def update_password(self, user_id: UUID, new_password: str) -> bool:
        """Update user password.

        Args:
            user_id: User UUID
            new_password: New plain password

        Returns:
            True if updated
        """
        # Truncate password (bcrypt 72-byte limit)
        password_truncated = new_password[:72] if len(new_password) > 72 else new_password
        password_hash = pwd_context.hash(password_truncated)

        updated = self._update_item(
            f"USER#{str(user_id)}",
            "METADATA",
            {"password_hash": password_hash}
        )

        return updated is not None

    def update_status(self, user_id: UUID, status: UserStatus) -> Optional[dict]:
        """Update user status.

        Args:
            user_id: User UUID
            status: New status

        Returns:
            Updated user item
        """
        return self._update_item(
            f"USER#{str(user_id)}",
            "METADATA",
            {"status": status.value}
        )

    # ========================================================================
    # Delete
    # ========================================================================

    def delete(self, user_id: UUID) -> bool:
        """Delete user (soft delete via status change).

        Args:
            user_id: User UUID

        Returns:
            True if deleted
        """
        # Soft delete: Set status to INACTIVE
        updated = self.update_status(user_id, UserStatus.INACTIVE)
        return updated is not None

    # ========================================================================
    # Authentication
    # ========================================================================

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password hash.

        Args:
            plain_password: Plain text password
            hashed_password: Hashed password from DB

        Returns:
            True if password matches
        """
        return pwd_context.verify(plain_password, hashed_password)

    def authenticate(self, email: str, password: str) -> Optional[dict]:
        """Authenticate user by email + password.

        Args:
            email: User email
            password: Plain password

        Returns:
            User item if authenticated, None otherwise
        """
        user = self.get_by_email(email)

        if not user:
            return None

        if not self.verify_password(password, user.get("password_hash", "")):
            return None

        if user.get("status") != UserStatus.ACTIVE.value:
            logger.warning(
                f"Login attempt for inactive user {user['id']}",
                extra={"user_id": user["id"], "status": user.get("status")}
            )
            return None

        return user

    # ========================================================================
    # List
    # ========================================================================

    def list(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[dict], int]:
        """List all users (admin only).

        Args:
            skip: Offset for pagination
            limit: Max items to return

        Returns:
            (items, total_count)
        """
        # Query GSI1: All users
        items, _ = self._query(
            key_condition=Key("GSI1PK").eq("user_by_email"),
            index_name="GSI1",
            limit=limit + skip
        )

        # Manual pagination (DynamoDB doesn't support offset)
        paginated_items = items[skip:skip + limit] if items else []
        total = len(items)

        return paginated_items, total
