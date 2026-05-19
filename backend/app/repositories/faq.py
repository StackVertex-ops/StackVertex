"""FAQ Repository - DynamoDB Data Access.

Handles FAQ management:
- FAQ items with categories
- Category management
- Sorting and ordering
- View count tracking
- Published/Draft status
"""

import logging
from datetime import datetime
from typing import Any
from uuid import uuid4

from boto3.dynamodb.conditions import Key, Attr
from mypy_boto3_dynamodb.service_resource import Table

from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class FaqRepository(BaseRepository):
    """Repository für FAQ Management.

    DynamoDB Structure:
        FAQ Item:
            PK: FAQ#{faq_id}
            SK: METADATA
            Attributes: faq_id, category, question, answer, sort_order,
                       status, view_count, created_by, updated_by
            GSI1: faq_category#{category} + sort_order (für Category-Filter + Sortierung)
            GSI2: faq_status#{status} + created_at (für Status-Filter)

        Category Item:
            PK: FAQ_CATEGORY#{category_id}
            SK: METADATA
            Attributes: category_id, name, slug, icon, sort_order
            GSI3: category_list + sort_order (für alle Kategorien sortiert)
    """

    # ========================================================================
    # Create FAQ
    # ========================================================================

    def create_faq(
        self,
        category: str,
        question: str,
        answer: str,
        sort_order: int = 0,
        status: str = "draft",
        created_by: str | None = None,
    ) -> dict[str, Any]:
        """Create new FAQ item.

        Args:
            category: Category slug (general/pricing/technical/security/other)
            question: FAQ question
            answer: FAQ answer (Markdown supported)
            sort_order: Sort order within category (lower = higher priority)
            status: published/draft
            created_by: Admin user ID

        Returns:
            Created FAQ item
        """
        faq_id = str(uuid4())
        now = datetime.utcnow().isoformat()

        item = {
            "PK": f"FAQ#{faq_id}",
            "SK": "METADATA",
            "faq_id": faq_id,
            "category": category,
            "question": question,
            "answer": answer,
            "sort_order": sort_order,
            "status": status,
            "view_count": 0,
            "created_by": created_by,
            "updated_by": created_by,
            "entity_type": "faq",
            # GSI1: Query by category + sort
            "GSI1PK": f"faq_category#{category}",
            "GSI1SK": sort_order,
            # GSI2: Query by status
            "GSI2PK": f"faq_status#{status}",
            "GSI2SK": now,
            "created_at": now,
            "updated_at": now,
        }

        return self._put_item(item)

    # ========================================================================
    # Get FAQ
    # ========================================================================

    def get_faq(self, faq_id: str) -> dict[str, Any] | None:
        """Get FAQ by ID.

        Args:
            faq_id: FAQ UUID

        Returns:
            FAQ item or None
        """
        return self._get_item(f"FAQ#{faq_id}", "METADATA")

    # ========================================================================
    # List FAQs
    # ========================================================================

    def list_faqs(
        self,
        category: str | None = None,
        status: str | None = None,
        limit: int = 100,
        last_evaluated_key: dict[str, Any] | None = None,
    ) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
        """List FAQs with optional filters.

        Args:
            category: Filter by category
            status: Filter by status (published/draft)
            limit: Max items to return
            last_evaluated_key: Pagination key

        Returns:
            Tuple of (items list sorted by sort_order, last_evaluated_key)
        """
        # Filter by category (GSI1) - bereits sortiert nach sort_order
        if category:
            items, last_key = self._query(
                key_condition=Key("GSI1PK").eq(f"faq_category#{category}"),
                index_name="GSI1",
                limit=limit,
                scan_index_forward=True,  # ASC sort_order
                exclusive_start_key=last_evaluated_key,
            )
            # Optionaler Status-Filter
            if status:
                items = [item for item in items if item.get("status") == status]
            return items, last_key

        # Filter by status (GSI2)
        if status:
            items, last_key = self._query(
                key_condition=Key("GSI2PK").eq(f"faq_status#{status}"),
                index_name="GSI2",
                limit=limit,
                scan_index_forward=False,  # Newest first
                exclusive_start_key=last_evaluated_key,
            )
            # Sortiere nach sort_order (nicht nach created_at)
            items.sort(key=lambda x: (x.get("category", ""), x.get("sort_order", 0)))
            return items, last_key

        # Keine Filter: Scan all FAQs (nur für kleine Datenmengen)
        items, last_key = self._scan(
            filter_condition=Attr("entity_type").eq("faq"),
            limit=limit,
            exclusive_start_key=last_evaluated_key,
        )
        # Sortiere nach category, dann sort_order
        items.sort(key=lambda x: (x.get("category", ""), x.get("sort_order", 0)))
        return items, last_key

    # ========================================================================
    # Update FAQ
    # ========================================================================

    def update_faq(
        self,
        faq_id: str,
        updated_by: str,
        **updates: Any,
    ) -> dict[str, Any] | None:
        """Update FAQ attributes.

        Args:
            faq_id: FAQ UUID
            updated_by: Admin user ID
            **updates: Fields to update (question, answer, category, status, sort_order)

        Returns:
            Updated FAQ item or None
        """
        faq = self.get_faq(faq_id)
        if not faq:
            return None

        # Update allowed fields
        allowed_fields = {"question", "answer", "category", "status", "sort_order"}
        for key, value in updates.items():
            if key in allowed_fields:
                faq[key] = value

                # Update GSI keys wenn category oder status sich ändert
                if key == "category":
                    faq["GSI1PK"] = f"faq_category#{value}"
                    faq["GSI1SK"] = faq.get("sort_order", 0)
                elif key == "status":
                    faq["GSI2PK"] = f"faq_status#{value}"
                elif key == "sort_order":
                    faq["GSI1SK"] = value

        faq["updated_by"] = updated_by
        faq["updated_at"] = datetime.utcnow().isoformat()

        return self._put_item(faq)

    # ========================================================================
    # Delete FAQ
    # ========================================================================

    def delete_faq(self, faq_id: str) -> bool:
        """Delete FAQ.

        Args:
            faq_id: FAQ UUID

        Returns:
            True if deleted successfully
        """
        return self._delete_item(f"FAQ#{faq_id}", "METADATA")

    # ========================================================================
    # Reorder FAQs
    # ========================================================================

    def reorder_faqs(
        self,
        faq_ids_in_order: list[str],
        updated_by: str,
    ) -> bool:
        """Update sort_order for multiple FAQs.

        Args:
            faq_ids_in_order: List of FAQ IDs in desired order
            updated_by: Admin user ID

        Returns:
            True if all updates succeeded
        """
        for index, faq_id in enumerate(faq_ids_in_order):
            faq = self.get_faq(faq_id)
            if not faq:
                logger.warning(f"FAQ {faq_id} not found during reorder")
                continue

            faq["sort_order"] = index
            faq["GSI1SK"] = index
            faq["updated_by"] = updated_by
            faq["updated_at"] = datetime.utcnow().isoformat()

            self._put_item(faq)

        return True

    # ========================================================================
    # View Count
    # ========================================================================

    def increment_view_count(self, faq_id: str) -> dict[str, Any] | None:
        """Increment view count for FAQ.

        Args:
            faq_id: FAQ UUID

        Returns:
            Updated FAQ item or None
        """
        faq = self.get_faq(faq_id)
        if not faq:
            return None

        faq["view_count"] = faq.get("view_count", 0) + 1
        faq["updated_at"] = datetime.utcnow().isoformat()

        return self._put_item(faq)

    # ========================================================================
    # Categories
    # ========================================================================

    def create_category(
        self,
        name: str,
        slug: str,
        icon: str = "",
        sort_order: int = 0,
    ) -> dict[str, Any]:
        """Create new FAQ category.

        Args:
            name: Category name (display)
            slug: Category slug (URL-safe)
            icon: Icon class or emoji
            sort_order: Sort order in category list

        Returns:
            Created category item
        """
        category_id = str(uuid4())
        now = datetime.utcnow().isoformat()

        item = {
            "PK": f"FAQ_CATEGORY#{category_id}",
            "SK": "METADATA",
            "category_id": category_id,
            "name": name,
            "slug": slug,
            "icon": icon,
            "sort_order": sort_order,
            "entity_type": "faq_category",
            # GSI3: Query all categories sorted
            "GSI3PK": "category_list",
            "GSI3SK": sort_order,
            "created_at": now,
            "updated_at": now,
        }

        return self._put_item(item)

    def get_category(self, category_id: str) -> dict[str, Any] | None:
        """Get category by ID.

        Args:
            category_id: Category UUID

        Returns:
            Category item or None
        """
        return self._get_item(f"FAQ_CATEGORY#{category_id}", "METADATA")

    def list_categories(
        self,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """List all categories sorted by sort_order.

        Args:
            limit: Max items to return

        Returns:
            List of categories
        """
        items, _ = self._query(
            key_condition=Key("GSI3PK").eq("category_list"),
            index_name="GSI3",
            limit=limit,
            scan_index_forward=True,  # ASC sort_order
        )
        return items

    def update_category(
        self,
        category_id: str,
        **updates: Any,
    ) -> dict[str, Any] | None:
        """Update category attributes.

        Args:
            category_id: Category UUID
            **updates: Fields to update (name, slug, icon, sort_order)

        Returns:
            Updated category item or None
        """
        category = self.get_category(category_id)
        if not category:
            return None

        # Update allowed fields
        allowed_fields = {"name", "slug", "icon", "sort_order"}
        for key, value in updates.items():
            if key in allowed_fields:
                category[key] = value

                # Update GSI3SK wenn sort_order sich ändert
                if key == "sort_order":
                    category["GSI3SK"] = value

        category["updated_at"] = datetime.utcnow().isoformat()

        return self._put_item(category)

    def delete_category(self, category_id: str) -> bool:
        """Delete category.

        Args:
            category_id: Category UUID

        Returns:
            True if deleted successfully
        """
        return self._delete_item(f"FAQ_CATEGORY#{category_id}", "METADATA")

    # ========================================================================
    # Analytics
    # ========================================================================

    def get_top_viewed_faqs(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get most viewed FAQs.

        Args:
            limit: Max items to return

        Returns:
            List of FAQs sorted by view_count DESC
        """
        # Scan alle published FAQs
        items, _ = self._query(
            key_condition=Key("GSI2PK").eq("faq_status#published"),
            index_name="GSI2",
            limit=1000,  # Get more items for accurate sorting
        )

        # Sortiere nach view_count DESC
        items.sort(key=lambda x: x.get("view_count", 0), reverse=True)

        return items[:limit]

    def get_unviewed_faqs(self) -> list[dict[str, Any]]:
        """Get FAQs with zero views.

        Returns:
            List of FAQs with view_count = 0
        """
        items, _ = self._query(
            key_condition=Key("GSI2PK").eq("faq_status#published"),
            index_name="GSI2",
            limit=1000,
        )

        return [item for item in items if item.get("view_count", 0) == 0]
