"""OrganisationRepository - DynamoDB Organisation Management.

Handles Organisation CRUD, Member Management, Quota Tracking.
"""

import logging
from datetime import datetime
from uuid import UUID, uuid4

from boto3.dynamodb.conditions import Key
from mypy_boto3_dynamodb.service_resource import Table

from app.models.organisation import (
    OrganisationPlan,
    OrganisationStatus,
    OrganisationType,
    get_quota,
)
from app.models.user import UserRole
from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class OrganisationRepository(BaseRepository):
    """Repository für Organisation Management."""

    def __init__(self, table: Table, s3_storage=None, secrets_manager=None):
        """Initialize OrganisationRepository.

        Args:
            table: DynamoDB Table Resource
            s3_storage: S3 Storage for large items (optional)
            secrets_manager: SecretsManager for encrypting AWS credentials (optional)
        """
        super().__init__(table, s3_storage)
        self.secrets_manager = secrets_manager

    # ========================================================================
    # Create
    # ========================================================================

    def create(
        self,
        name: str,
        owner_user_id: UUID,
        organisation_type: OrganisationType = OrganisationType.TEAM,
        plan: OrganisationPlan = OrganisationPlan.FREE,
    ) -> dict:
        """Create new organisation.

        Args:
            name: Organisation name
            owner_user_id: User ID of owner/creator
            organisation_type: Personal or Team
            plan: Subscription plan

        Returns:
            Organisation item
        """
        org_id = uuid4()
        now = datetime.utcnow().isoformat()

        # Organisation Item
        org_item = {
            "PK": f"ORG#{str(org_id)}",
            "SK": "METADATA",
            "id": str(org_id),
            "name": name,
            "type": organisation_type.value,
            "owner_user_id": str(owner_user_id),
            "plan": plan.value,
            "status": OrganisationStatus.ACTIVE.value,
            "aws_role_arn": None,
            "aws_account_id": None,
            "created_at": now,
            "updated_at": now,
            # Quota tracking
            "quota": {
                "active_deployments": 0,
                "members": 1,  # Owner zählt
                "architectures": 0,
            },
            # GSI1: Query all organisations
            "GSI1PK": "organisation",
            "GSI1SK": str(org_id),
            # GSI2: Query by owner
            "GSI2PK": f"owner#{str(owner_user_id)}",
            "GSI2SK": str(org_id),
        }

        # Owner Membership Item
        membership_item = {
            "PK": f"ORG#{str(org_id)}",
            "SK": f"USER#{str(owner_user_id)}",
            "user_id": str(owner_user_id),
            "role": UserRole.OWNER.value,
            "created_at": now,
        }

        # Reverse Membership (USER → ORG)
        reverse_membership_item = {
            "PK": f"USER#{str(owner_user_id)}",
            "SK": f"ORG#{str(org_id)}",
            "org_id": str(org_id),
            "org_name": name,
            "role": UserRole.OWNER.value,
            "joined_at": now,
        }

        # Batch write
        self._batch_write_items(
            items=[org_item, membership_item, reverse_membership_item]
        )

        logger.info(
            f"Created organisation {org_id}",
            extra={"org_id": str(org_id), "owner": str(owner_user_id)}
        )

        return org_item

    # ========================================================================
    # Read
    # ========================================================================

    def get(self, org_id: UUID) -> dict | None:
        """Get organisation by ID.

        Args:
            org_id: Organisation UUID

        Returns:
            Organisation item or None
        """
        return self._get_item(f"ORG#{str(org_id)}", "METADATA")

    def get_members(self, org_id: UUID) -> list[dict]:
        """Get all members of organisation.

        Args:
            org_id: Organisation UUID

        Returns:
            List of membership items
        """
        items, _ = self._query(
            key_condition=Key("PK").eq(f"ORG#{str(org_id)}") & Key("SK").begins_with("USER#")
        )

        return items

    def get_member(self, org_id: UUID, user_id: UUID) -> dict | None:
        """Get specific member.

        Args:
            org_id: Organisation UUID
            user_id: User UUID

        Returns:
            Membership item or None
        """
        return self._get_item(
            f"ORG#{str(org_id)}",
            f"USER#{str(user_id)}"
        )

    def list_all(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[dict], int]:
        """List ALL organisations (Admin only).

        Args:
            skip: Offset for pagination
            limit: Max items

        Returns:
            (items, total_count)
        """
        # Query all (GSI1) - get ALL items first
        items, _ = self._query(
            key_condition=Key("GSI1PK").eq("organisation"),
            index_name="GSI1"
        )

        # Calculate total before pagination
        total = len(items)

        # Manual pagination
        paginated_items = items[skip:skip + limit] if items else []

        return paginated_items, total

    def list(
        self,
        skip: int = 0,
        limit: int = 100,
        owner_user_id: UUID | None = None,
    ) -> tuple[list[dict], int]:
        """List organisations.

        Args:
            skip: Offset for pagination
            limit: Max items
            owner_user_id: Filter by owner (optional)

        Returns:
            (items, total_count)
        """
        if owner_user_id:
            # Query by owner (GSI2) - get ALL items first
            items, _ = self._query(
                key_condition=Key("GSI2PK").eq(f"owner#{str(owner_user_id)}"),
                index_name="GSI2"
            )
        else:
            # Query all (GSI1) - get ALL items first
            items, _ = self._query(
                key_condition=Key("GSI1PK").eq("organisation"),
                index_name="GSI1"
            )

        # Calculate total before pagination
        total = len(items)

        # Manual pagination
        paginated_items = items[skip:skip + limit] if items else []

        return paginated_items, total

    # ========================================================================
    # Update
    # ========================================================================

    def update(self, org_id: UUID, updates: dict) -> dict | None:
        """Update organisation.

        Args:
            org_id: Organisation UUID
            updates: Fields to update

        Returns:
            Updated item or None
        """
        # Remove protected fields
        updates.pop("id", None)
        updates.pop("owner_user_id", None)
        updates.pop("created_at", None)
        updates.pop("plan", None)  # Use upgrade_plan() instead

        if not updates:
            return self.get(org_id)

        return self._update_item(
            f"ORG#{str(org_id)}",
            "METADATA",
            updates
        )

    def upgrade_plan(
        self,
        org_id: UUID,
        new_plan: OrganisationPlan
    ) -> dict | None:
        """Upgrade/downgrade organisation plan.

        Args:
            org_id: Organisation UUID
            new_plan: New plan

        Returns:
            Updated organisation
        """
        return self._update_item(
            f"ORG#{str(org_id)}",
            "METADATA",
            {"plan": new_plan.value}
        )

    def update_aws_credentials(
        self,
        org_id: UUID,
        aws_role_arn: str,
        aws_account_id: str
    ) -> dict | None:
        """Update AWS IAM Role credentials (ENCRYPTED).

        Args:
            org_id: Organisation UUID
            aws_role_arn: IAM Role ARN
            aws_account_id: AWS Account ID (extracted from ARN)

        Returns:
            Updated organisation

        Security:
            ✅ AWS Role ARN is encrypted in AWS Secrets Manager (KMS)
            ✅ Only secret reference stored in DynamoDB
            ✅ Encryption at rest + in transit
        """
        updates = {
            "aws_account_id": aws_account_id,
            "aws_verified_at": datetime.utcnow().isoformat(),
        }

        # Encrypt AWS Role ARN in Secrets Manager
        if self.secrets_manager:
            try:
                secret_name = self.secrets_manager.store_aws_role_arn(
                    str(org_id),
                    aws_role_arn
                )
                updates["aws_role_arn_secret"] = secret_name
                logger.info(
                    f"Encrypted AWS credentials for org {org_id}",
                    extra={"org_id": str(org_id), "secret_name": secret_name}
                )
            except Exception as e:
                logger.error(f"Failed to encrypt AWS credentials: {e}")
                raise HTTPException(
                    status_code=500,
                    detail="Failed to securely store AWS credentials"
                )
        else:
            # Fallback for tests/dev without SecretsManager
            logger.warning(
                "Storing AWS credentials in PLAINTEXT (SecretsManager not configured)",
                extra={"org_id": str(org_id)}
            )
            updates["aws_role_arn"] = aws_role_arn  # ⚠️ PLAINTEXT fallback

        return self._update_item(
            f"ORG#{str(org_id)}",
            "METADATA",
            updates
        )

    def get_aws_role_arn(self, org_id: UUID) -> str | None:
        """Retrieve decrypted AWS Role ARN.

        Args:
            org_id: Organisation UUID

        Returns:
            Decrypted AWS Role ARN or None

        Security:
            ✅ Transparently decrypts from AWS Secrets Manager
            ✅ Falls back to plaintext for tests/dev
        """
        org = self.get(org_id)
        if not org:
            return None

        # Decrypt from Secrets Manager if available
        if self.secrets_manager and "aws_role_arn_secret" in org:
            try:
                return self.secrets_manager.retrieve_aws_role_arn(
                    org["aws_role_arn_secret"]
                )
            except Exception as e:
                logger.error(
                    f"Failed to decrypt AWS credentials for org {org_id}: {e}",
                    extra={"org_id": str(org_id)}
                )
                return None
        else:
            # Fallback to plaintext (tests/dev)
            return org.get("aws_role_arn")

    # ========================================================================
    # Member Management
    # ========================================================================

    def add_member(
        self,
        org_id: UUID,
        user_id: UUID,
        user_email: str,
        user_name: str,
        role: UserRole = UserRole.MEMBER
    ) -> dict:
        """Add member to organisation.

        Args:
            org_id: Organisation UUID
            user_id: User UUID
            user_email: User email
            user_name: User name
            role: Member role

        Returns:
            Membership item
        """
        now = datetime.utcnow().isoformat()

        # Membership Item
        membership_item = {
            "PK": f"ORG#{str(org_id)}",
            "SK": f"USER#{str(user_id)}",
            "user_id": str(user_id),
            "email": user_email,
            "name": user_name,
            "role": role.value,
            "created_at": now,
        }

        # Reverse Membership
        org = self.get(org_id)
        reverse_membership_item = {
            "PK": f"USER#{str(user_id)}",
            "SK": f"ORG#{str(org_id)}",
            "org_id": str(org_id),
            "org_name": org["name"] if org else "Unknown",
            "role": role.value,
            "joined_at": now,
        }

        # Batch write
        self._batch_write_items(items=[membership_item, reverse_membership_item])

        # Increment member count
        self.increment_quota(org_id, "members", 1)

        logger.info(
            f"Added member {user_id} to org {org_id}",
            extra={"org_id": str(org_id), "user_id": str(user_id), "role": role.value}
        )

        return membership_item

    def remove_member(self, org_id: UUID, user_id: UUID) -> bool:
        """Remove member from organisation.

        Args:
            org_id: Organisation UUID
            user_id: User UUID

        Returns:
            True if removed
        """
        # Delete membership
        deleted1 = self._delete_item(
            f"ORG#{str(org_id)}",
            f"USER#{str(user_id)}"
        )

        # Delete reverse membership
        deleted2 = self._delete_item(
            f"USER#{str(user_id)}",
            f"ORG#{str(org_id)}"
        )

        if deleted1:
            # Decrement member count
            self.increment_quota(org_id, "members", -1)

        logger.info(
            f"Removed member {user_id} from org {org_id}",
            extra={"org_id": str(org_id), "user_id": str(user_id)}
        )

        return deleted1 and deleted2

    def update_member_role(
        self,
        org_id: UUID,
        user_id: UUID,
        new_role: UserRole
    ) -> dict | None:
        """Update member role.

        Args:
            org_id: Organisation UUID
            user_id: User UUID
            new_role: New role

        Returns:
            Updated membership item
        """
        # Update membership
        updated1 = self._update_item(
            f"ORG#{str(org_id)}",
            f"USER#{str(user_id)}",
            {"role": new_role.value}
        )

        # Update reverse membership
        updated2 = self._update_item(
            f"USER#{str(user_id)}",
            f"ORG#{str(org_id)}",
            {"role": new_role.value}
        )

        return updated1

    # ========================================================================
    # Quota Management
    # ========================================================================

    def get_quota(self, org_id: UUID) -> dict[str, int]:
        """Get current quota usage.

        Args:
            org_id: Organisation UUID

        Returns:
            Quota dict (active_deployments, members, architectures)
        """
        org = self.get(org_id)
        if not org:
            return {}

        return org.get("quota", {})

    def increment_quota(
        self,
        org_id: UUID,
        quota_key: str,
        increment: int = 1
    ) -> dict | None:
        """Increment quota counter.

        Args:
            org_id: Organisation UUID
            quota_key: Quota key (e.g., "active_deployments")
            increment: Amount to increment (can be negative)

        Returns:
            Updated organisation
        """
        # Read current quota
        org = self.get(org_id)
        if not org:
            return None

        quota = org.get("quota", {})
        current_value = quota.get(quota_key, 0)
        new_value = max(0, current_value + increment)  # Never go below 0

        quota[quota_key] = new_value

        return self._update_item(
            f"ORG#{str(org_id)}",
            "METADATA",
            {"quota": quota}
        )

    def check_quota(
        self,
        org_id: UUID,
        quota_key: str
    ) -> tuple[bool, int, int]:
        """Check if quota limit is exceeded.

        Args:
            org_id: Organisation UUID
            quota_key: Quota key to check (can be "max_*" or just the key)

        Returns:
            (can_proceed, current_value, max_allowed)
        """
        org = self.get(org_id)
        if not org:
            return False, 0, 0

        plan = OrganisationPlan(org.get("plan", OrganisationPlan.FREE.value))

        # Ensure "max_" prefix for PLAN_QUOTAS lookup
        max_key = quota_key if quota_key.startswith("max_") else f"max_{quota_key}"
        max_allowed = get_quota(plan, max_key)

        # -1 = unlimited
        if isinstance(max_allowed, int) and max_allowed == -1:
            return True, 0, -1

        # Strip "max_" prefix to get actual quota key in org["quota"]
        current_key = quota_key.replace("max_", "") if quota_key.startswith("max_") else quota_key
        current_value = org.get("quota", {}).get(current_key, 0)

        can_proceed = current_value < max_allowed

        return can_proceed, current_value, max_allowed

    # ========================================================================
    # Delete
    # ========================================================================

    def delete(self, org_id: UUID) -> bool:
        """Delete organisation (CASCADE delete members).

        Args:
            org_id: Organisation UUID

        Returns:
            True if deleted
        """
        # Get all members first
        members = self.get_members(org_id)

        # Delete all member relationships
        delete_keys = []
        for member in members:
            user_id = member["user_id"]
            # Membership
            delete_keys.append({"PK": f"ORG#{str(org_id)}", "SK": f"USER#{user_id}"})
            # Reverse membership
            delete_keys.append({"PK": f"USER#{user_id}", "SK": f"ORG#{str(org_id)}"})

        if delete_keys:
            self._batch_write_items(items=[], delete_keys=delete_keys)

        # Delete organisation metadata
        deleted = self._delete_item(f"ORG#{str(org_id)}", "METADATA")

        logger.info(
            f"Deleted organisation {org_id} with {len(members)} members",
            extra={"org_id": str(org_id)}
        )

        return deleted
