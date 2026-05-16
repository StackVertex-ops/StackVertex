"""Base Repository for DynamoDB Operations.

Provides common DynamoDB operations with S3 offload for large items.
"""

from typing import Any, Dict, List, Optional, TypeVar, Generic
from datetime import datetime
from decimal import Decimal
from mypy_boto3_dynamodb.service_resource import Table
from boto3.dynamodb.conditions import Key, Attr, ConditionBase

from app.db.dynamodb import get_dynamodb_table
from app.db.s3_storage import S3Storage
from app.config import settings


def convert_floats_to_decimal(obj: Any) -> Any:
    """Convert all float values to Decimal for DynamoDB compatibility.

    DynamoDB doesn't support Python float types, only Decimal.
    This recursively converts all floats in nested structures.

    Args:
        obj: Object to convert (dict, list, or primitive)

    Returns:
        Object with all floats converted to Decimal
    """
    if isinstance(obj, float):
        return Decimal(str(obj))
    elif isinstance(obj, dict):
        return {k: convert_floats_to_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_floats_to_decimal(item) for item in obj]
    else:
        return obj


T = TypeVar("T")


class BaseRepository(Generic[T]):
    """Base repository with common DynamoDB operations.

    Provides CRUD operations, querying, and automatic S3 offload
    for items exceeding the size threshold.
    """

    def __init__(
        self,
        table: Optional[Table] = None,
        s3_storage: Optional[S3Storage] = None
    ):
        """Initialize repository.

        Args:
            table: DynamoDB table (creates default if None)
            s3_storage: S3 storage helper (creates default if None)
        """
        self.table = table or get_dynamodb_table()
        self.s3_storage = s3_storage or S3Storage()
        self.large_item_threshold = settings.LARGE_ITEM_THRESHOLD

    def _put_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Put item in DynamoDB with automatic timestamps.

        Args:
            item: Item to store

        Returns:
            Stored item with timestamps

        Raises:
            Exception: If put operation fails
        """
        # Add timestamps
        now = datetime.utcnow().isoformat()
        if "created_at" not in item:
            item["created_at"] = now
        item["updated_at"] = now

        # Convert floats to Decimal (DynamoDB requirement)
        item = convert_floats_to_decimal(item)

        # Put item
        self.table.put_item(Item=item)

        return item

    def _get_item(self, pk: str, sk: str) -> Optional[Dict[str, Any]]:
        """Get single item by primary key.

        Args:
            pk: Partition key value
            sk: Sort key value

        Returns:
            Item dict or None if not found
        """
        response = self.table.get_item(
            Key={"PK": pk, "SK": sk}
        )
        return response.get("Item")

    def _query(
        self,
        key_condition: ConditionBase,
        filter_condition: Optional[ConditionBase] = None,
        index_name: Optional[str] = None,
        limit: Optional[int] = None,
        scan_index_forward: bool = True,
        exclusive_start_key: Optional[Dict[str, Any]] = None,
        projection_expression: Optional[str] = None
    ) -> tuple[List[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """Query items with optional filtering and pagination.

        Args:
            key_condition: Key condition expression
            filter_condition: Optional filter condition
            index_name: GSI name (if querying index)
            limit: Maximum items to return
            scan_index_forward: True for ASC, False for DESC
            exclusive_start_key: Pagination key from previous query
            projection_expression: Attributes to return

        Returns:
            Tuple of (items list, last_evaluated_key for pagination)
        """
        kwargs: Dict[str, Any] = {
            "KeyConditionExpression": key_condition,
            "ScanIndexForward": scan_index_forward,
        }

        if filter_condition is not None:
            kwargs["FilterExpression"] = filter_condition
        if index_name:
            kwargs["IndexName"] = index_name
        if limit:
            kwargs["Limit"] = limit
        if exclusive_start_key:
            kwargs["ExclusiveStartKey"] = exclusive_start_key
        if projection_expression:
            kwargs["ProjectionExpression"] = projection_expression

        response = self.table.query(**kwargs)
        return response.get("Items", []), response.get("LastEvaluatedKey")

    def _scan(
        self,
        filter_condition: Optional[ConditionBase] = None,
        limit: Optional[int] = None,
        exclusive_start_key: Optional[Dict[str, Any]] = None
    ) -> tuple[List[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """Scan table (use sparingly - prefer query).

        Args:
            filter_condition: Optional filter condition
            limit: Maximum items to return
            exclusive_start_key: Pagination key from previous scan

        Returns:
            Tuple of (items list, last_evaluated_key for pagination)
        """
        kwargs: Dict[str, Any] = {}

        if filter_condition is not None:
            kwargs["FilterExpression"] = filter_condition
        if limit:
            kwargs["Limit"] = limit
        if exclusive_start_key:
            kwargs["ExclusiveStartKey"] = exclusive_start_key

        response = self.table.scan(**kwargs)
        return response.get("Items", []), response.get("LastEvaluatedKey")

    def _update_item(
        self,
        pk: str,
        sk: str,
        updates: Dict[str, Any],
        condition_expression: Optional[ConditionBase] = None
    ) -> Dict[str, Any]:
        """Update item attributes.

        Args:
            pk: Partition key value
            sk: Sort key value
            updates: Dict of attributes to update
            condition_expression: Optional condition for update

        Returns:
            Updated item

        Raises:
            Exception: If update fails
        """
        # Build update expression
        update_parts = []
        expr_attr_names = {}
        expr_attr_values = {}

        for i, (key, value) in enumerate(updates.items()):
            attr_name = f"#attr{i}"
            attr_value = f":val{i}"
            update_parts.append(f"{attr_name} = {attr_value}")
            expr_attr_names[attr_name] = key
            expr_attr_values[attr_value] = value

        # Add updated_at timestamp
        update_parts.append("#updated_at = :updated_at")
        expr_attr_names["#updated_at"] = "updated_at"
        expr_attr_values[":updated_at"] = datetime.utcnow().isoformat()

        update_expr = "SET " + ", ".join(update_parts)

        kwargs: Dict[str, Any] = {
            "Key": {"PK": pk, "SK": sk},
            "UpdateExpression": update_expr,
            "ExpressionAttributeNames": expr_attr_names,
            "ExpressionAttributeValues": expr_attr_values,
            "ReturnValues": "ALL_NEW",
        }

        if condition_expression is not None:
            kwargs["ConditionExpression"] = condition_expression

        response = self.table.update_item(**kwargs)
        return response["Attributes"]

    def _delete_item(
        self,
        pk: str,
        sk: str,
        condition_expression: Optional[ConditionBase] = None
    ) -> bool:
        """Delete item.

        Args:
            pk: Partition key value
            sk: Sort key value
            condition_expression: Optional condition for delete

        Returns:
            True if deleted successfully
        """
        try:
            kwargs: Dict[str, Any] = {
                "Key": {"PK": pk, "SK": sk}
            }

            if condition_expression is not None:
                kwargs["ConditionExpression"] = condition_expression

            self.table.delete_item(**kwargs)
            return True
        except Exception:
            return False

    def _batch_get_items(
        self,
        keys: List[Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        """Get multiple items in a single batch request.

        Args:
            keys: List of primary keys [{PK: ..., SK: ...}, ...]

        Returns:
            List of items (order not guaranteed)
        """
        if not keys:
            return []

        response = self.table.meta.client.batch_get_item(
            RequestItems={
                self.table.name: {
                    "Keys": keys
                }
            }
        )

        return response.get("Responses", {}).get(self.table.name, [])

    def _batch_write_items(
        self,
        items: List[Dict[str, Any]],
        delete_keys: Optional[List[Dict[str, str]]] = None
    ) -> bool:
        """Batch write (put/delete) items.

        Args:
            items: Items to put
            delete_keys: Keys to delete

        Returns:
            True if all writes succeeded
        """
        if not items and not delete_keys:
            return True

        requests = []

        # Add put requests
        for item in items:
            requests.append({"PutRequest": {"Item": item}})

        # Add delete requests
        if delete_keys:
            for key in delete_keys:
                requests.append({"DeleteRequest": {"Key": key}})

        # Batch write (handles pagination internally)
        try:
            self.table.meta.client.batch_write_item(
                RequestItems={
                    self.table.name: requests
                }
            )
            return True
        except Exception:
            return False

    def _store_large_item(self, data: str, s3_key: str) -> str:
        """Store large item in S3.

        Args:
            data: String data to store
            s3_key: S3 object key

        Returns:
            S3 URI (s3://bucket/key)
        """
        return self.s3_storage.upload(s3_key, data)

    def _load_large_item(self, s3_uri: str) -> str:
        """Load large item from S3.

        Args:
            s3_uri: S3 URI (s3://bucket/key)

        Returns:
            Downloaded data as string
        """
        return self.s3_storage.download(s3_uri)

    def _delete_large_item(self, s3_uri: str) -> bool:
        """Delete large item from S3.

        Args:
            s3_uri: S3 URI (s3://bucket/key)

        Returns:
            True if deleted successfully
        """
        return self.s3_storage.delete(s3_uri)
