"""Script zum Erstellen eines SuperAdmin Users.

Usage:
    python scripts/create_superadmin.py --email admin@stackvertex.io --name "Admin User"

Wichtig:
    - Läuft nur wenn noch KEIN SuperAdmin existiert (Safety)
    - Generiert ein zufälliges Passwort (wird ausgegeben)
    - Speichert User in DynamoDB
    - Logt Action im Audit Trail
"""

import argparse
import logging
from uuid import uuid4

from app.db.dynamodb import get_dynamodb_table
from app.models.user import SystemRole, UserStatus, AuthProvider
from app.repositories.user import UserRepository
from app.services.audit_logger import log_audit
from app.utils.password import generate_secure_password

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_existing_superadmin(user_repo: UserRepository) -> bool:
    """Check if any SuperAdmin already exists.

    Args:
        user_repo: UserRepository

    Returns:
        True if SuperAdmin exists, False otherwise
    """
    # List all users and check for SuperAdmin
    users, _ = user_repo.list(skip=0, limit=1000)

    for user in users:
        if user.get("system_role") == SystemRole.SUPERADMIN.value:
            logger.warning(
                f"SuperAdmin already exists: {user['email']}",
                extra={"user_id": user["id"], "email": user["email"]}
            )
            return True

    return False


def create_superadmin(
    email: str,
    name: str,
    password: str = None,
    force: bool = False
) -> dict:
    """Create SuperAdmin user.

    Args:
        email: Admin email
        name: Admin name
        password: Admin password (if None, generates random)
        force: Force creation even if SuperAdmin exists

    Returns:
        Created user dict with password

    Raises:
        ValueError: If SuperAdmin already exists (and not force)
    """
    # Get DynamoDB table
    table = get_dynamodb_table()
    user_repo = UserRepository(table=table)

    # Check if SuperAdmin already exists
    if not force and check_existing_superadmin(user_repo):
        raise ValueError(
            "SuperAdmin already exists. Use --force to create another SuperAdmin "
            "(not recommended - use system_role update instead)."
        )

    # Generate password if not provided
    if not password:
        password = generate_secure_password()
        logger.info("Generated random password (will be displayed at the end)")

    # Create user
    logger.info(f"Creating SuperAdmin user: {email}")

    user = user_repo.create(
        email=email,
        name=name,
        password=password,
        auth_provider=AuthProvider.EMAIL,
    )

    # Update system role to SuperAdmin
    logger.info(f"Promoting user to SuperAdmin: {user['id']}")
    user = user_repo.update_system_role(
        user_id=uuid4().__class__(user["id"]),
        system_role=SystemRole.SUPERADMIN
    )

    # Log audit event
    log_audit(
        user="system",
        action="admin.create_superadmin",
        resource_type="user",
        resource_id=uuid4().__class__(user["id"]),
        details={
            "email": email,
            "name": name,
            "created_by": "script"
        }
    )

    logger.info(
        f"SuperAdmin created successfully: {user['id']}",
        extra={"user_id": user["id"], "email": email}
    )

    return {
        "user": user,
        "password": password
    }


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Create SuperAdmin user for StackVertex"
    )
    parser.add_argument(
        "--email",
        required=True,
        help="SuperAdmin email address"
    )
    parser.add_argument(
        "--name",
        required=True,
        help="SuperAdmin display name"
    )
    parser.add_argument(
        "--password",
        help="SuperAdmin password (if not provided, generates random)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force creation even if SuperAdmin exists (not recommended)"
    )

    args = parser.parse_args()

    try:
        result = create_superadmin(
            email=args.email,
            name=args.name,
            password=args.password,
            force=args.force
        )

        print("\n" + "=" * 80)
        print("SuperAdmin created successfully!")
        print("=" * 80)
        print(f"Email:    {result['user']['email']}")
        print(f"Name:     {result['user']['name']}")
        print(f"User ID:  {result['user']['id']}")
        print(f"Password: {result['password']}")
        print("=" * 80)
        print("\nIMPORTANT:")
        print("- Store this password securely (password manager)")
        print("- Enable 2FA after first login (coming soon)")
        print("- Change password after first login")
        print("- This password will NOT be shown again")
        print("=" * 80 + "\n")

    except ValueError as e:
        logger.error(f"Failed to create SuperAdmin: {e}")
        exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        exit(1)


if __name__ == "__main__":
    main()
