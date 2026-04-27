"""Unit tests für OrganisationRepository.

Fokus: Organisation CRUD, Member Management, Quota Tracking, AWS Credentials.
"""

import pytest
from uuid import uuid4

from app.models.organisation import OrganisationPlan, OrganisationType, OrganisationStatus
from app.models.user import UserRole


class TestOrganisationCreate:
    """Tests für create() method."""

    def test_create_organisation(self, organisation_repository):
        """Test creating organisation."""
        owner_id = uuid4()

        result = organisation_repository.create(
            name="Test Organisation",
            owner_user_id=owner_id,
            organisation_type=OrganisationType.TEAM,
            plan=OrganisationPlan.FREE
        )

        assert result["name"] == "Test Organisation"
        assert result["type"] == OrganisationType.TEAM.value
        assert result["owner_user_id"] == str(owner_id)
        assert result["plan"] == OrganisationPlan.FREE.value
        assert result["status"] == OrganisationStatus.ACTIVE.value
        assert "quota" in result
        assert result["quota"]["active_deployments"] == 0
        assert result["quota"]["members"] == 1  # Owner counts
        assert result["quota"]["architectures"] == 0

    def test_create_organisation_creates_owner_membership(self, organisation_repository):
        """Test that creating org also creates owner membership."""
        owner_id = uuid4()

        org = organisation_repository.create(
            name="Test Org",
            owner_user_id=owner_id,
        )

        # Verify owner membership exists
        from uuid import UUID
        member = organisation_repository.get_member(UUID(org["id"]), owner_id)

        assert member is not None
        assert member["user_id"] == str(owner_id)
        assert member["role"] == UserRole.OWNER.value


class TestOrganisationGet:
    """Tests für get() method."""

    def test_get_organisation(self, organisation_repository):
        """Test getting organisation by ID."""
        owner_id = uuid4()
        created = organisation_repository.create(
            name="Test Org",
            owner_user_id=owner_id
        )

        from uuid import UUID
        result = organisation_repository.get(UUID(created["id"]))

        assert result is not None
        assert result["id"] == created["id"]
        assert result["name"] == "Test Org"

    def test_get_nonexistent_organisation(self, organisation_repository):
        """Test getting non-existent organisation returns None."""
        result = organisation_repository.get(uuid4())

        assert result is None


class TestOrganisationMembers:
    """Tests für member management."""

    def test_get_members(self, organisation_repository):
        """Test getting all members of organisation."""
        owner_id = uuid4()
        org = organisation_repository.create(
            name="Test Org",
            owner_user_id=owner_id
        )

        from uuid import UUID
        members = organisation_repository.get_members(UUID(org["id"]))

        # Should have owner
        assert len(members) >= 1
        assert members[0]["role"] == UserRole.OWNER.value

    def test_add_member(self, organisation_repository):
        """Test adding member to organisation."""
        owner_id = uuid4()
        org = organisation_repository.create(
            name="Test Org",
            owner_user_id=owner_id
        )

        # Add new member
        new_member_id = uuid4()
        from uuid import UUID

        membership = organisation_repository.add_member(
            org_id=UUID(org["id"]),
            user_id=new_member_id,
            user_email="member@example.com",
            user_name="New Member",
            role=UserRole.MEMBER
        )

        assert membership["user_id"] == str(new_member_id)
        assert membership["role"] == UserRole.MEMBER.value

        # Verify member count incremented
        updated_org = organisation_repository.get(UUID(org["id"]))
        assert updated_org["quota"]["members"] == 2  # Owner + new member

    def test_remove_member(self, organisation_repository):
        """Test removing member from organisation."""
        owner_id = uuid4()
        org = organisation_repository.create(
            name="Test Org",
            owner_user_id=owner_id
        )

        # Add member
        member_id = uuid4()
        from uuid import UUID

        organisation_repository.add_member(
            org_id=UUID(org["id"]),
            user_id=member_id,
            user_email="member@example.com",
            user_name="Member",
            role=UserRole.MEMBER
        )

        # Remove member
        removed = organisation_repository.remove_member(UUID(org["id"]), member_id)

        assert removed is True

        # Verify member gone
        member = organisation_repository.get_member(UUID(org["id"]), member_id)
        assert member is None

        # Verify member count decremented
        updated_org = organisation_repository.get(UUID(org["id"]))
        assert updated_org["quota"]["members"] == 1  # Only owner

    def test_update_member_role(self, organisation_repository):
        """Test updating member role."""
        owner_id = uuid4()
        org = organisation_repository.create(
            name="Test Org",
            owner_user_id=owner_id
        )

        # Add member
        member_id = uuid4()
        from uuid import UUID

        organisation_repository.add_member(
            org_id=UUID(org["id"]),
            user_id=member_id,
            user_email="member@example.com",
            user_name="Member",
            role=UserRole.MEMBER
        )

        # Promote to admin
        updated = organisation_repository.update_member_role(
            UUID(org["id"]),
            member_id,
            UserRole.ADMIN
        )

        assert updated["role"] == UserRole.ADMIN.value


class TestOrganisationQuota:
    """Tests für quota management."""

    def test_get_quota(self, organisation_repository):
        """Test getting current quota."""
        owner_id = uuid4()
        org = organisation_repository.create(
            name="Test Org",
            owner_user_id=owner_id
        )

        from uuid import UUID
        quota = organisation_repository.get_quota(UUID(org["id"]))

        assert "active_deployments" in quota
        assert "members" in quota
        assert "architectures" in quota

    def test_increment_quota(self, organisation_repository):
        """Test incrementing quota counter."""
        owner_id = uuid4()
        org = organisation_repository.create(
            name="Test Org",
            owner_user_id=owner_id
        )

        from uuid import UUID
        org_id = UUID(org["id"])

        # Increment deployments
        organisation_repository.increment_quota(org_id, "active_deployments", 1)

        updated_org = organisation_repository.get(org_id)
        assert updated_org["quota"]["active_deployments"] == 1

        # Increment again
        organisation_repository.increment_quota(org_id, "active_deployments", 2)

        updated_org = organisation_repository.get(org_id)
        assert updated_org["quota"]["active_deployments"] == 3

    def test_increment_quota_negative(self, organisation_repository):
        """Test decrementing quota (negative increment)."""
        owner_id = uuid4()
        org = organisation_repository.create(
            name="Test Org",
            owner_user_id=owner_id
        )

        from uuid import UUID
        org_id = UUID(org["id"])

        # Set to 5
        organisation_repository.increment_quota(org_id, "active_deployments", 5)

        # Decrement by 2
        organisation_repository.increment_quota(org_id, "active_deployments", -2)

        updated_org = organisation_repository.get(org_id)
        assert updated_org["quota"]["active_deployments"] == 3

    def test_increment_quota_never_below_zero(self, organisation_repository):
        """Test quota never goes below 0."""
        owner_id = uuid4()
        org = organisation_repository.create(
            name="Test Org",
            owner_user_id=owner_id
        )

        from uuid import UUID
        org_id = UUID(org["id"])

        # Try to decrement below 0
        organisation_repository.increment_quota(org_id, "active_deployments", -10)

        updated_org = organisation_repository.get(org_id)
        assert updated_org["quota"]["active_deployments"] == 0  # Not negative

    def test_check_quota_within_limit(self, organisation_repository):
        """Test quota check when within limit."""
        owner_id = uuid4()
        org = organisation_repository.create(
            name="Test Org",
            owner_user_id=owner_id,
            plan=OrganisationPlan.FREE  # FREE has 1 max deployment
        )

        from uuid import UUID
        # NOTE: Pass the QUOTA key (active_deployments), not the MAX key
        can_proceed, current, max_allowed = organisation_repository.check_quota(
            UUID(org["id"]),
            "active_deployments"  # This maps to max_active_deployments in PLAN_QUOTAS
        )

        assert can_proceed is True  # 0 < 1
        assert current == 0
        assert max_allowed == 1

    def test_check_quota_exceeded(self, organisation_repository):
        """Test quota check when limit exceeded."""
        owner_id = uuid4()
        org = organisation_repository.create(
            name="Test Org",
            owner_user_id=owner_id,
            plan=OrganisationPlan.FREE  # 1 max deployment
        )

        from uuid import UUID
        org_id = UUID(org["id"])

        # Set to limit
        organisation_repository.increment_quota(org_id, "active_deployments", 1)

        can_proceed, current, max_allowed = organisation_repository.check_quota(
            org_id,
            "max_active_deployments"
        )

        assert can_proceed is False  # 1 >= 1
        assert current == 1
        assert max_allowed == 1

    def test_check_quota_unlimited(self, organisation_repository):
        """Test quota check for unlimited plan."""
        owner_id = uuid4()
        org = organisation_repository.create(
            name="Test Org",
            owner_user_id=owner_id,
            plan=OrganisationPlan.ENTERPRISE  # Unlimited
        )

        from uuid import UUID
        org_id = UUID(org["id"])

        # Even with high usage
        organisation_repository.increment_quota(org_id, "active_deployments", 999)

        can_proceed, current, max_allowed = organisation_repository.check_quota(
            org_id,
            "max_active_deployments"
        )

        assert can_proceed is True  # Unlimited
        assert max_allowed == -1  # -1 = unlimited


class TestOrganisationUpdate:
    """Tests für update() method."""

    def test_update_organisation_name(self, organisation_repository):
        """Test updating organisation name."""
        owner_id = uuid4()
        org = organisation_repository.create(
            name="Old Name",
            owner_user_id=owner_id
        )

        from uuid import UUID
        updated = organisation_repository.update(
            UUID(org["id"]),
            {"name": "New Name"}
        )

        assert updated["name"] == "New Name"

    def test_upgrade_plan(self, organisation_repository):
        """Test upgrading organisation plan."""
        owner_id = uuid4()
        org = organisation_repository.create(
            name="Test Org",
            owner_user_id=owner_id,
            plan=OrganisationPlan.FREE
        )

        from uuid import UUID
        updated = organisation_repository.upgrade_plan(
            UUID(org["id"]),
            OrganisationPlan.PRO
        )

        assert updated["plan"] == OrganisationPlan.PRO.value

    def test_update_aws_credentials(self, organisation_repository):
        """Test updating AWS credentials."""
        owner_id = uuid4()
        org = organisation_repository.create(
            name="Test Org",
            owner_user_id=owner_id
        )

        from uuid import UUID
        aws_role_arn = "arn:aws:iam::123456789012:role/OverCloudRole"

        updated = organisation_repository.update_aws_credentials(
            UUID(org["id"]),
            aws_role_arn=aws_role_arn,
            aws_account_id="123456789012"
        )

        assert updated["aws_role_arn"] == aws_role_arn
        assert updated["aws_account_id"] == "123456789012"
        assert "aws_verified_at" in updated


class TestOrganisationList:
    """Tests für list() method."""

    def test_list_all_organisations(self, organisation_repository):
        """Test listing all organisations."""
        # Create multiple orgs
        for i in range(3):
            organisation_repository.create(
                name=f"Org {i}",
                owner_user_id=uuid4()
            )

        items, total = organisation_repository.list(skip=0, limit=100)

        assert total >= 3
        assert len(items) >= 3

    def test_list_by_owner(self, organisation_repository):
        """Test listing organisations by owner."""
        owner_id = uuid4()

        # Create 2 orgs for this owner
        organisation_repository.create(
            name="Owner Org 1",
            owner_user_id=owner_id
        )
        organisation_repository.create(
            name="Owner Org 2",
            owner_user_id=owner_id
        )

        # Create org for different owner
        organisation_repository.create(
            name="Other Org",
            owner_user_id=uuid4()
        )

        # Query by owner
        items, total = organisation_repository.list(
            skip=0,
            limit=100,
            owner_user_id=owner_id
        )

        assert total == 2
        assert all(item["owner_user_id"] == str(owner_id) for item in items)

    def test_list_pagination(self, organisation_repository):
        """Test organisation list pagination."""
        owner_id = uuid4()

        # Create 10 orgs
        created_ids = []
        for i in range(10):
            result = organisation_repository.create(
                name=f"Page Org {i}",
                owner_user_id=owner_id
            )
            created_ids.append(result["id"])

        # First page
        items_page1, total = organisation_repository.list(
            skip=0,
            limit=3,
            owner_user_id=owner_id
        )

        assert len(items_page1) == 3
        assert total == 10

        # Second page
        items_page2, _ = organisation_repository.list(
            skip=3,
            limit=3,
            owner_user_id=owner_id
        )

        assert len(items_page2) == 3

        # Verify different orgs
        ids_page1 = {item["id"] for item in items_page1}
        ids_page2 = {item["id"] for item in items_page2}
        assert ids_page1.isdisjoint(ids_page2)


class TestOrganisationDelete:
    """Tests für delete() method."""

    def test_delete_organisation(self, organisation_repository):
        """Test deleting organisation."""
        owner_id = uuid4()
        org = organisation_repository.create(
            name="Test Org",
            owner_user_id=owner_id
        )

        from uuid import UUID
        deleted = organisation_repository.delete(UUID(org["id"]))

        assert deleted is True

        # Verify deleted
        result = organisation_repository.get(UUID(org["id"]))
        assert result is None

    def test_delete_organisation_cascades_members(self, organisation_repository):
        """Test deleting organisation also deletes all member relationships."""
        owner_id = uuid4()
        org = organisation_repository.create(
            name="Test Org",
            owner_user_id=owner_id
        )

        # Add members
        from uuid import UUID
        org_id = UUID(org["id"])

        for i in range(3):
            organisation_repository.add_member(
                org_id=org_id,
                user_id=uuid4(),
                user_email=f"member{i}@example.com",
                user_name=f"Member {i}",
                role=UserRole.MEMBER
            )

        # Delete org
        organisation_repository.delete(org_id)

        # Verify members gone
        members = organisation_repository.get_members(org_id)
        assert len(members) == 0
