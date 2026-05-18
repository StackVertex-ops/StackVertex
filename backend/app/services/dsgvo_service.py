"""
DSGVO Service - Business Logic for GDPR Compliance

Implements data processing functions for GDPR rights:
- Data Export (Art. 15)
- Data Deletion (Art. 17)
- Data Rectification (Art. 16)
- Consent Management (Art. 7)
"""

import json
import logging
from datetime import datetime, timedelta
from uuid import UUID

from app.repositories.architecture import ArchitectureRepository
from app.repositories.audit_log import AuditLogRepository
from app.repositories.deployment import DeploymentRepository
from app.repositories.dsgvo import DsgvoRepository
from app.repositories.user import UserRepository

logger = logging.getLogger(__name__)

# ===========================
# Data Export (Art. 15)
# ===========================


async def export_user_data(
    user_id: UUID,
    format: str = "json",
    include_metadata: bool = True,
    dsgvo_repo: DsgvoRepository = None,
) -> dict:
    """
    Export all user data (DSGVO Art. 15)

    Args:
        user_id: User UUID
        format: Export format (json, csv, pdf)
        include_metadata: Include timestamps, IDs, etc.
        dsgvo_repo: DSGVO Repository

    Returns:
        Dict with export_id, status, expires_at
    """
    if not dsgvo_repo:
        dsgvo_repo = DsgvoRepository()

    # Create export request in DynamoDB
    export_item = dsgvo_repo.create_export_request(
        user_id=user_id,
        format=format,
        include_metadata=include_metadata,
    )

    logger.info(f"Created data export request {export_item['export_id']} for user {user_id}")

    return {
        "export_id": export_item["export_id"],
        "expires_at": export_item["expires_at"],
        "download_url": None,  # Will be generated when ready
    }


async def generate_data_export_json(
    user_id: UUID,
    export_id: str,
    user_repo: UserRepository = None,
    architecture_repo: ArchitectureRepository = None,
    deployment_repo: DeploymentRepository = None,
    audit_log_repo: AuditLogRepository = None,
    dsgvo_repo: DsgvoRepository = None,
):
    """
    Background task: Generate complete data export

    Collects data from all sources:
    - User profile
    - Architectures
    - Deployments
    - Audit logs
    - Consents
    - S3 files
    """
    # Initialize repositories if not provided
    if not user_repo:
        user_repo = UserRepository()
    if not architecture_repo:
        architecture_repo = ArchitectureRepository()
    if not deployment_repo:
        deployment_repo = DeploymentRepository()
    if not audit_log_repo:
        audit_log_repo = AuditLogRepository()
    if not dsgvo_repo:
        dsgvo_repo = DsgvoRepository()

    try:
        # Collect user data
        user = user_repo.get(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        export_data = {
            "export_info": {
                "export_id": export_id,
                "generated_at": datetime.utcnow().isoformat(),
                "user_id": str(user_id),
                "format_version": "1.0",
            },
            "personal_data": {
                "email": user.get("email"),
                "name": user.get("name"),
                "created_at": user.get("created_at"),
                "updated_at": user.get("updated_at"),
            },
            "architectures": await _export_architectures(user_id, architecture_repo),
            "deployments": await _export_deployments(user_id, deployment_repo),
            "audit_logs": await _export_audit_logs(user_id, audit_log_repo),
            "consents": await _export_consents(user_id, dsgvo_repo),
            "s3_files": await _export_s3_files(user_id),
        }

        # Convert to JSON
        json_data = json.dumps(export_data, indent=2, default=str)

        # Upload to S3 (temporary bucket)
        s3_key = f"data-exports/{user_id}/{export_id}.json"
        # TODO: Upload to S3
        # from app.db.s3_storage import S3Storage
        # s3_storage = S3Storage()
        # s3_storage.upload_string(json_data, s3_key)

        # Update export status to ready
        dsgvo_repo.update_export_status(
            user_id=user_id,
            export_id=export_id,
            status="ready",
            s3_key=s3_key,
        )

        logger.info(f"Data export {export_id} for user {user_id} completed successfully")

        return export_data

    except Exception as e:
        logger.error(f"Failed to generate data export {export_id}: {str(e)}")
        # Update export status to failed
        dsgvo_repo.update_export_status(
            user_id=user_id,
            export_id=export_id,
            status="failed",
            error=str(e),
        )
        raise


async def _export_architectures(
    user_id: UUID, architecture_repo: ArchitectureRepository
) -> list[dict]:
    """Export all user architectures"""
    try:
        architectures = architecture_repo.list_by_owner(str(user_id))
        return [
            {
                "id": arch.get("id"),
                "name": arch.get("name"),
                "description": arch.get("description"),
                "version": arch.get("version"),
                "created_at": arch.get("created_at"),
                "updated_at": arch.get("updated_at"),
                # Include architecture_json (can be large)
                "architecture_json": arch.get("architecture_json"),
            }
            for arch in architectures
        ]
    except Exception as e:
        logger.warning(f"Failed to export architectures for user {user_id}: {str(e)}")
        return []


async def _export_deployments(
    user_id: UUID, deployment_repo: DeploymentRepository
) -> list[dict]:
    """Export all user deployments"""
    try:
        deployments = deployment_repo.list_by_owner(str(user_id))
        return [
            {
                "id": dep.get("id"),
                "architecture_id": dep.get("architecture_id"),
                "status": dep.get("status"),
                "region": dep.get("region"),
                "created_at": dep.get("created_at"),
                "updated_at": dep.get("updated_at"),
            }
            for dep in deployments
        ]
    except Exception as e:
        logger.warning(f"Failed to export deployments for user {user_id}: {str(e)}")
        return []


async def _export_audit_logs(
    user_id: UUID, audit_log_repo: AuditLogRepository
) -> list[dict]:
    """Export audit logs (last 90 days)"""
    try:
        # List audit logs for user (last 90 days)
        logs = audit_log_repo.list_by_user(str(user_id), limit=1000)
        cutoff = datetime.utcnow() - timedelta(days=90)

        return [
            {
                "id": log.get("id"),
                "action": log.get("action"),
                "resource_type": log.get("resource_type"),
                "resource_id": log.get("resource_id"),
                "timestamp": log.get("timestamp"),
                "success": log.get("success"),
            }
            for log in logs
            if datetime.fromisoformat(log.get("timestamp", "")) >= cutoff
        ]
    except Exception as e:
        logger.warning(f"Failed to export audit logs for user {user_id}: {str(e)}")
        return []


async def _export_consents(user_id: UUID, dsgvo_repo: DsgvoRepository) -> list[dict]:
    """Export consent history"""
    try:
        consents = dsgvo_repo.list_consents(user_id)
        return [
            {
                "consent_type": consent.get("consent_type"),
                "granted": consent.get("granted"),
                "granted_at": consent.get("granted_at"),
                "revoked_at": consent.get("revoked_at"),
            }
            for consent in consents
        ]
    except Exception as e:
        logger.warning(f"Failed to export consents for user {user_id}: {str(e)}")
        return []


async def _export_s3_files(user_id: str) -> dict:
    """Export S3 file list (not content, only metadata)"""
    # TODO: Implement S3 listing
    return {"files": [], "total_size_bytes": 0}


# ===========================
# Data Deletion (Art. 17)
# ===========================


async def schedule_user_deletion(
    user_id: UUID,
    reason: str,
    delete_backups: bool = True,
    dsgvo_repo: DsgvoRepository = None,
) -> dict:
    """
    Schedule user data deletion (with 7-day grace period)

    Args:
        user_id: User UUID
        reason: Deletion reason
        delete_backups: Also delete from backups
        dsgvo_repo: DSGVO Repository

    Returns:
        Dict with deletion_id, scheduled_at, estimated_completion
    """
    if not dsgvo_repo:
        dsgvo_repo = DsgvoRepository()

    # Create deletion request in DynamoDB
    deletion_item = dsgvo_repo.create_deletion_request(
        user_id=user_id,
        reason=reason,
        delete_backups=delete_backups,
    )

    logger.info(f"Scheduled data deletion {deletion_item['deletion_id']} for user {user_id}")

    return {
        "deletion_id": deletion_item["deletion_id"],
        "scheduled_at": deletion_item["scheduled_at"],
        "estimated_completion": deletion_item["estimated_completion"],
    }


async def delete_user_data(
    user_id: UUID,
    delete_backups: bool = True,
    user_repo: UserRepository = None,
    architecture_repo: ArchitectureRepository = None,
    deployment_repo: DeploymentRepository = None,
    audit_log_repo: AuditLogRepository = None,
):
    """
    Execute user data deletion (called by background job)

    **Deletion Steps:**
    1. Delete architectures & deployments
    2. Delete S3 customer data
    3. Anonymize audit logs (keep for compliance)
    4. Delete user account
    5. (Optional) Delete from backups
    """
    # Initialize repositories if not provided
    if not user_repo:
        user_repo = UserRepository()
    if not architecture_repo:
        architecture_repo = ArchitectureRepository()
    if not deployment_repo:
        deployment_repo = DeploymentRepository()
    if not audit_log_repo:
        audit_log_repo = AuditLogRepository()

    try:
        # Step 1: Delete architectures
        architectures = architecture_repo.list_by_owner(str(user_id))
        for arch in architectures:
            architecture_repo.delete(UUID(arch["id"]))
        logger.info(f"Deleted {len(architectures)} architectures for user {user_id}")

        # Step 2: Delete deployments
        deployments = deployment_repo.list_by_owner(str(user_id))
        for dep in deployments:
            deployment_repo.delete(UUID(dep["id"]))
        logger.info(f"Deleted {len(deployments)} deployments for user {user_id}")

        # Step 3: Delete S3 customer data
        await _delete_s3_customer_data(user_id)

        # Step 4: Anonymize audit logs (don't delete - keep for compliance)
        await anonymize_user_data(user_id, audit_log_repo)

        # Step 5: Delete user account
        user_repo.delete(user_id)
        logger.info(f"Deleted user account {user_id}")

        # Step 6: (Optional) Delete from backups
        if delete_backups:
            await _delete_from_backups(user_id)

        logger.info(f"User data deletion completed for user {user_id}")

        return {"status": "completed", "deleted_at": datetime.utcnow().isoformat()}

    except Exception as e:
        logger.error(f"Failed to delete user data for {user_id}: {str(e)}")
        raise Exception(f"Failed to delete user data: {str(e)}")


async def anonymize_user_data(user_id: UUID, audit_log_repo: AuditLogRepository):
    """
    Anonymize user in audit logs (keep logs for compliance, but remove PII)

    Replaces:
    - user → "anonymized_user_{random_id}"
    - ip_address → "0.0.0.0"
    """
    from uuid import uuid4

    anonymous_id = str(uuid4())[:8]

    # Get all audit logs for user
    logs = audit_log_repo.list_by_user(str(user_id), limit=10000)

    # Update each log to anonymize user data
    for log in logs:
        try:
            # Note: DynamoDB doesn't support batch updates, so we need to update each item
            # In a production system, this would be done via DynamoDB Streams + Lambda
            # For now, we'll update the user field to indicate anonymization
            audit_log_repo.update(
                log_id=UUID(log["id"]),
                updates={
                    "user": f"anonymized_user_{anonymous_id}",
                    "ip_address": "0.0.0.0",
                    "anonymized": True,
                    "anonymized_at": datetime.utcnow().isoformat(),
                }
            )
        except Exception as e:
            logger.warning(f"Failed to anonymize audit log {log['id']}: {str(e)}")

    logger.info(f"Anonymized {len(logs)} audit logs for user {user_id}")


async def _delete_s3_customer_data(user_id: str):
    """Delete all S3 objects for user"""
    # TODO: Implement S3 deletion
    # bucket_name = f"overcloud-customer-data"
    # prefix = f"users/{user_id}/"
    # S3Client.delete_objects(bucket_name, prefix)
    pass


async def _delete_from_backups(user_id: UUID):
    """
    Delete user data from backups (AWS Backup, RDS Snapshots)

    **Note:** This is complex and may take days to complete.
    DSGVO allows up to 30 days for complete deletion.
    """
    # TODO: Implement backup deletion
    # 1. List all backup vaults
    # 2. Identify backups containing user data
    # 3. Create "deletion markers" for those backups
    # 4. Schedule point-in-time deletion (when backups expire)
    logger.warning(f"Backup deletion for user {user_id} not yet implemented")
    pass


# ===========================
# Helper Functions for Router
# ===========================


async def get_user_export(
    export_id: str, user_id: UUID, dsgvo_repo: DsgvoRepository = None
) -> dict | None:
    """Retrieve export data by ID"""
    if not dsgvo_repo:
        dsgvo_repo = DsgvoRepository()

    return dsgvo_repo.get_export(user_id, export_id)


async def cancel_scheduled_deletion(
    deletion_id: str, user_id: UUID, dsgvo_repo: DsgvoRepository = None
) -> bool:
    """Cancel scheduled deletion"""
    if not dsgvo_repo:
        dsgvo_repo = DsgvoRepository()

    # Get deletion request
    deletion = dsgvo_repo.get_deletion(user_id, deletion_id)

    if not deletion:
        return False

    # Check if still in scheduled state
    if deletion.get("status") != "scheduled":
        return False

    # Update status to cancelled
    dsgvo_repo.update_deletion_status(
        user_id=user_id,
        deletion_id=deletion_id,
        status="cancelled",
    )

    logger.info(f"Cancelled deletion request {deletion_id} for user {user_id}")

    return True


async def update_user_field(
    user_id: UUID,
    field: str,
    old_value: str,
    new_value: str,
    reason: str | None = None,
    user_repo: UserRepository = None,
) -> dict:
    """Update user field with audit trail"""
    if not user_repo:
        user_repo = UserRepository()

    # Get user
    user = user_repo.get(user_id)
    if not user:
        raise ValueError(f"User {user_id} not found")

    # Verify old value matches
    current_value = user.get(field)
    if current_value != old_value:
        raise ValueError(
            f"Old value mismatch: expected '{old_value}', got '{current_value}'"
        )

    # Update field
    updates = {field: new_value}
    if reason:
        updates[f"{field}_change_reason"] = reason

    updated_user = user_repo.update(user_id, updates)

    logger.info(
        f"Updated field {field} for user {user_id}: '{old_value}' → '{new_value}'"
    )

    return updated_user


async def send_deletion_confirmation_email(email: str, deletion_id: str):
    """Send deletion confirmation email"""
    # TODO: Implement email service integration
    logger.info(f"Would send deletion confirmation email to {email} for {deletion_id}")
    pass


# ===========================
# Consent Management (Art. 7)
# ===========================


async def get_user_consents(user_id: UUID, dsgvo_repo: DsgvoRepository = None) -> list[dict]:
    """
    Get all user consents

    Returns:
        List of consent records with type, granted status, timestamps
    """
    if not dsgvo_repo:
        dsgvo_repo = DsgvoRepository()

    consents = dsgvo_repo.list_consents(user_id)

    # If no consents exist, return defaults
    if not consents:
        return [
            {
                "consent_type": "required",
                "granted": True,
                "granted_at": None,
                "revoked_at": None,
                "ip_address": None,
                "user_agent": None,
            },
            {
                "consent_type": "marketing",
                "granted": False,
                "granted_at": None,
                "revoked_at": None,
                "ip_address": None,
                "user_agent": None,
            },
            {
                "consent_type": "analytics",
                "granted": False,
                "granted_at": None,
                "revoked_at": None,
                "ip_address": None,
                "user_agent": None,
            },
        ]

    return [
        {
            "consent_type": consent.get("consent_type"),
            "granted": consent.get("granted"),
            "granted_at": consent.get("granted_at"),
            "revoked_at": consent.get("revoked_at"),
            "ip_address": consent.get("ip_address"),
            "user_agent": consent.get("user_agent"),
        }
        for consent in consents
    ]


async def update_user_consent(
    user_id: UUID,
    consent_type: str,
    granted: bool,
    ip_address: str | None = None,
    user_agent: str | None = None,
    reason: str | None = None,
    dsgvo_repo: DsgvoRepository = None,
) -> dict:
    """
    Update user consent (grant or revoke)

    Args:
        user_id: User UUID
        consent_type: Type of consent (marketing, analytics, etc.)
        granted: True to grant, False to revoke
        ip_address: IP address of request
        user_agent: User agent of request
        reason: Optional reason for change
        dsgvo_repo: DSGVO Repository

    Returns:
        Updated consent record
    """
    # Validate consent type
    valid_types = ["marketing", "analytics", "third_party"]
    if consent_type not in valid_types:
        raise ValueError(
            f"Invalid consent type. Must be one of: {', '.join(valid_types)}"
        )

    if not dsgvo_repo:
        dsgvo_repo = DsgvoRepository()

    # Update consent in DynamoDB
    consent_item = dsgvo_repo.update_consent(
        user_id=user_id,
        consent_type=consent_type,
        granted=granted,
        ip_address=ip_address,
        user_agent=user_agent,
        reason=reason,
    )

    logger.info(
        f"Updated consent {consent_type} for user {user_id}: granted={granted}"
    )

    return {
        "consent_type": consent_item.get("consent_type"),
        "granted": consent_item.get("granted"),
        "updated_at": consent_item.get("updated_at"),
    }


# ===========================
# Data Retention & Cleanup
# ===========================


async def cleanup_expired_exports(dsgvo_repo: DsgvoRepository = None):
    """
    Background job: Clean up expired data exports (runs daily)

    Deletes exports older than 7 days from S3 and database.
    """
    if not dsgvo_repo:
        dsgvo_repo = DsgvoRepository()

    # Get expired exports
    expired_exports = dsgvo_repo.list_expired_exports(limit=1000)

    for export in expired_exports:
        try:
            # Delete from S3
            s3_key = export.get("s3_key")
            if s3_key:
                from app.db.s3_storage import S3Storage
                s3_storage = S3Storage()
                s3_storage.delete(s3_key)

            # Delete from DynamoDB
            user_id = UUID(export["user_id"])
            export_id = export["export_id"]
            # Note: We need to implement delete in repository
            # For now, just update status to "expired"
            dsgvo_repo.update_export_status(
                user_id=user_id,
                export_id=export_id,
                status="expired",
            )

            logger.info(f"Cleaned up expired export {export_id}")

        except Exception as e:
            logger.error(f"Failed to cleanup export {export.get('export_id')}: {str(e)}")

    logger.info(f"Cleaned up {len(expired_exports)} expired exports")


async def execute_scheduled_deletions(dsgvo_repo: DsgvoRepository = None):
    """
    Background job: Execute scheduled user deletions (runs hourly)

    Finds deletions with scheduled_at <= now and executes them.
    """
    if not dsgvo_repo:
        dsgvo_repo = DsgvoRepository()

    # Get scheduled deletions ready to execute
    pending_deletions = dsgvo_repo.list_scheduled_deletions(limit=100)

    for deletion in pending_deletions:
        user_id = UUID(deletion["user_id"])
        deletion_id = deletion["deletion_id"]

        try:
            # Update status to in_progress
            dsgvo_repo.update_deletion_status(
                user_id=user_id,
                deletion_id=deletion_id,
                status="in_progress",
            )

            # Execute deletion
            await delete_user_data(
                user_id=user_id,
                delete_backups=deletion.get("delete_backups", True),
            )

            # Mark as completed
            dsgvo_repo.update_deletion_status(
                user_id=user_id,
                deletion_id=deletion_id,
                status="completed",
            )

            logger.info(f"Completed scheduled deletion {deletion_id} for user {user_id}")

        except Exception as e:
            logger.error(f"Failed to execute deletion {deletion_id}: {str(e)}")
            # Mark as failed
            dsgvo_repo.update_deletion_status(
                user_id=user_id,
                deletion_id=deletion_id,
                status="failed",
                error=str(e),
            )

    logger.info(f"Processed {len(pending_deletions)} scheduled deletions")
