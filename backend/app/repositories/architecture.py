"""Architecture Repository - DynamoDB Data Access.

Handles CRUD operations for Architecture entities with automatic
S3 offload for large architecture_json (> 300KB).
"""

import json
from typing import Any
from uuid import UUID, uuid4

from boto3.dynamodb.conditions import Key

from app.repositories.base import BaseRepository
from app.schemas.architecture import ArchitectureCreate, ArchitectureUpdate


class ArchitectureRepository(BaseRepository):
    """Repository for Architecture entities.

    DynamoDB Structure:
        PK: ARCH#{architecture_id}
        SK: METADATA
        Attributes: id, name, description, version, architecture_json (or S3 URI), owner, timestamps
        GSI1: entity_type + created_at (for list all)
        GSI2: owner#{owner} + created_at (for list by owner)
    """

    def create(self, architecture: ArchitectureCreate) -> dict[str, Any]:
        """Create new architecture.

        Args:
            architecture: Architecture data

        Returns:
            Created architecture item

        Raises:
            Exception: If creation fails
        """
        arch_id = str(uuid4())

        # Serialize architecture_json to check size
        json_str = json.dumps(architecture.architecture_json, ensure_ascii=False)
        json_size = len(json_str.encode("utf-8"))

        # Prepare base item
        item: dict[str, Any] = {
            "PK": f"ARCH#{arch_id}",
            "SK": "METADATA",
            "id": arch_id,
            "name": architecture.name,
            "description": architecture.description or "",
            "version": architecture.version,
            "owner": architecture.owner,
            "entity_type": "architecture",
        }

        # Add GSI attributes for querying
        from datetime import datetime
        created_at_iso = datetime.utcnow().isoformat()
        item["GSI1PK"] = "architecture"
        item["GSI1SK"] = created_at_iso
        item["GSI2PK"] = f"owner#{architecture.owner}"
        item["GSI2SK"] = created_at_iso

        # Check if architecture_json exceeds threshold
        if json_size > self.large_item_threshold:
            # Store in S3
            s3_uri = self._store_large_item(
                json_str,
                f"architectures/{arch_id}/architecture.json"
            )
            item["architecture_json_s3_uri"] = s3_uri
        else:
            # Store inline in DynamoDB
            item["architecture_json"] = architecture.architecture_json

        # Store in DynamoDB
        return self._put_item(item)

    def get(self, architecture_id: UUID) -> dict[str, Any] | None:
        """Get architecture by ID.

        Args:
            architecture_id: Architecture UUID

        Returns:
            Architecture item or None if not found
        """
        item = self._get_item(f"ARCH#{str(architecture_id)}", "METADATA")

        if not item:
            return None

        # Load from S3 if needed
        if "architecture_json_s3_uri" in item:
            json_str = self._load_large_item(item["architecture_json_s3_uri"])
            item["architecture_json"] = json.loads(json_str)
            # Remove S3 URI from response (transparent to caller)
            del item["architecture_json_s3_uri"]

        return item

    def list(
        self,
        skip: int = 0,
        limit: int = 100,
        owner: str | None = None
    ) -> tuple[list[dict[str, Any]], int]:
        """List architectures with pagination and optional owner filter.

        Args:
            skip: Number of items to skip
            limit: Maximum items to return
            owner: Optional owner filter

        Returns:
            Tuple of (items list, total count)

        Note:
            For accurate total count, this queries all items and applies
            skip/limit in memory. For large datasets, consider using
            LastEvaluatedKey for cursor-based pagination.
        """
        if owner:
            # Query GSI2 (by owner)
            items, _ = self._query(
                key_condition=Key("GSI2PK").eq(f"owner#{owner}"),
                index_name="GSI2",
                scan_index_forward=False  # DESC order (newest first)
            )
        else:
            # Query GSI1 (all architectures)
            items, _ = self._query(
                key_condition=Key("GSI1PK").eq("architecture"),
                index_name="GSI1",
                scan_index_forward=False  # DESC order (newest first)
            )

        # Get total count before pagination
        total = len(items)

        # Apply skip/limit
        paginated_items = items[skip : skip + limit]

        # Load large items from S3 if needed
        for item in paginated_items:
            if "architecture_json_s3_uri" in item:
                json_str = self._load_large_item(item["architecture_json_s3_uri"])
                item["architecture_json"] = json.loads(json_str)
                del item["architecture_json_s3_uri"]

        return paginated_items, total

    def update(
        self,
        architecture_id: UUID,
        architecture_update: ArchitectureUpdate
    ) -> dict[str, Any] | None:
        """Update architecture (partial update).

        Args:
            architecture_id: Architecture UUID
            architecture_update: Fields to update

        Returns:
            Updated architecture or None if not found

        Raises:
            Exception: If update fails
        """
        # Check if architecture exists
        existing = self.get(architecture_id)
        if not existing:
            return None

        # Prepare update data
        update_data = architecture_update.model_dump(exclude_unset=True)

        # Handle architecture_json update (check size for S3 offload)
        if "architecture_json" in update_data:
            json_str = json.dumps(update_data["architecture_json"], ensure_ascii=False)
            json_size = len(json_str.encode("utf-8"))

            if json_size > self.large_item_threshold:
                # Store in S3
                s3_uri = self._store_large_item(
                    json_str,
                    f"architectures/{str(architecture_id)}/architecture.json"
                )
                update_data["architecture_json_s3_uri"] = s3_uri
                # Remove architecture_json from DynamoDB update
                del update_data["architecture_json"]

                # Delete old S3 object if it was inline before
                # (No need to delete, will be overwritten)
            else:
                # Store inline - if was in S3 before, delete S3 object
                if "architecture_json_s3_uri" in existing:
                    self._delete_large_item(existing["architecture_json_s3_uri"])
                    # Remove S3 URI attribute in DynamoDB
                    # Note: DynamoDB doesn't have a "remove attribute" in update_item easily
                    # We'll handle this by setting it to None and filtering later

        # Perform update
        updated = self._update_item(
            f"ARCH#{str(architecture_id)}",
            "METADATA",
            update_data
        )

        # Load from S3 if needed
        if "architecture_json_s3_uri" in updated:
            json_str = self._load_large_item(updated["architecture_json_s3_uri"])
            updated["architecture_json"] = json.loads(json_str)
            del updated["architecture_json_s3_uri"]

        return updated

    def delete(self, architecture_id: UUID) -> bool:
        """Delete architecture and related items.

        Args:
            architecture_id: Architecture UUID

        Returns:
            True if deleted successfully

        Note:
            Also deletes:
            - Architecture-Deployment relationship items
            - Version link items
            - S3 objects (if architecture_json was in S3)
        """
        arch_id_str = str(architecture_id)

        # Get architecture to check for S3 objects
        arch = self.get(architecture_id)
        if arch and "architecture_json_s3_uri" in arch:
            # Delete S3 object
            self._delete_large_item(arch["architecture_json_s3_uri"])

        # Delete main architecture item
        success = self._delete_item(f"ARCH#{arch_id_str}", "METADATA")

        if not success:
            return False

        # Delete all deployment relationships (ARCH#{id}/DEPLOY#{deployment_id})
        deployment_rels, _ = self._query(
            key_condition=Key("PK").eq(f"ARCH#{arch_id_str}") & Key("SK").begins_with("DEPLOY#")
        )
        for rel in deployment_rels:
            self._delete_item(rel["PK"], rel["SK"])

        # Delete all version links (ARCH#{id}/VERSION#{parent_id})
        version_links, _ = self._query(
            key_condition=Key("PK").eq(f"ARCH#{arch_id_str}") & Key("SK").begins_with("VERSION#")
        )
        for link in version_links:
            self._delete_item(link["PK"], link["SK"])

        return True
