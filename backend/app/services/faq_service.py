"""FAQ Service - Business Logic for FAQ Management.

Handles:
- Public FAQ retrieval (published only)
- FAQ search
- Admin FAQ management (CRUD + reordering)
- Category management
- Analytics
"""

import logging
from typing import Any

from app.repositories.faq import FaqRepository

logger = logging.getLogger(__name__)


class FaqService:
    """Service for FAQ management."""

    def __init__(self, faq_repo: FaqRepository):
        """Initialize service.

        Args:
            faq_repo: FAQ repository instance
        """
        self.faq_repo = faq_repo

    # ========================================================================
    # Public FAQ Access (Published Only)
    # ========================================================================

    def get_public_faqs(self, category: str | None = None) -> dict[str, Any]:
        """Get published FAQs grouped by category.

        Args:
            category: Optional category filter

        Returns:
            Dict with categories and their FAQs
        """
        # Lade alle published FAQs (oder nur für eine Kategorie)
        faqs, _ = self.faq_repo.list_faqs(
            category=category,
            status="published",
            limit=1000,
        )

        # Gruppiere nach Kategorie
        if category:
            # Nur eine Kategorie - direkte Rückgabe
            return {
                "category": category,
                "faqs": faqs,
                "total": len(faqs),
            }

        # Gruppiere nach Kategorien
        categories = self.faq_repo.list_categories()
        result = {
            "categories": [],
            "total": len(faqs),
        }

        # Map FAQs zu Kategorien
        faq_by_category = {}
        for faq in faqs:
            cat = faq.get("category", "other")
            if cat not in faq_by_category:
                faq_by_category[cat] = []
            faq_by_category[cat].append(faq)

        # Erstelle sortierte Category-Liste mit FAQs
        for cat in categories:
            slug = cat.get("slug")
            result["categories"].append({
                "category_id": cat.get("category_id"),
                "name": cat.get("name"),
                "slug": slug,
                "icon": cat.get("icon", ""),
                "faqs": faq_by_category.get(slug, []),
            })

        return result

    def search_faqs(self, query: str) -> list[dict[str, Any]]:
        """Search FAQs by question or answer text.

        Args:
            query: Search query

        Returns:
            List of matching published FAQs
        """
        # Lade alle published FAQs
        faqs, _ = self.faq_repo.list_faqs(status="published", limit=1000)

        # Einfache Text-Suche (case-insensitive)
        query_lower = query.lower()
        results = []

        for faq in faqs:
            question = faq.get("question", "").lower()
            answer = faq.get("answer", "").lower()

            if query_lower in question or query_lower in answer:
                results.append(faq)

        return results

    def get_faq_detail(
        self,
        faq_id: str,
        track_view: bool = True,
    ) -> dict[str, Any] | None:
        """Get single FAQ with optional view tracking.

        Args:
            faq_id: FAQ UUID
            track_view: Increment view count if True

        Returns:
            FAQ item or None
        """
        faq = self.faq_repo.get_faq(faq_id)

        if not faq:
            return None

        # Nur published FAQs öffentlich zugänglich
        if faq.get("status") != "published":
            return None

        # Track view
        if track_view:
            self.faq_repo.increment_view_count(faq_id)
            # Update local view_count für Response
            faq["view_count"] = faq.get("view_count", 0) + 1

        return faq

    # ========================================================================
    # Admin FAQ Management
    # ========================================================================

    def list_all_faqs(
        self,
        category: str | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        """List all FAQs (including drafts) for admin.

        Args:
            category: Optional category filter
            status: Optional status filter

        Returns:
            List of FAQs
        """
        faqs, _ = self.faq_repo.list_faqs(
            category=category,
            status=status,
            limit=1000,
        )
        return faqs

    def create_faq(
        self,
        admin_id: str,
        category: str,
        question: str,
        answer: str,
        status: str = "draft",
        sort_order: int = 0,
    ) -> dict[str, Any]:
        """Create new FAQ.

        Args:
            admin_id: Admin user ID
            category: Category slug
            question: FAQ question
            answer: FAQ answer (Markdown)
            status: published/draft
            sort_order: Sort order within category

        Returns:
            Created FAQ
        """
        return self.faq_repo.create_faq(
            category=category,
            question=question,
            answer=answer,
            sort_order=sort_order,
            status=status,
            created_by=admin_id,
        )

    def update_faq(
        self,
        faq_id: str,
        admin_id: str,
        **updates: Any,
    ) -> dict[str, Any] | None:
        """Update FAQ.

        Args:
            faq_id: FAQ UUID
            admin_id: Admin user ID
            **updates: Fields to update

        Returns:
            Updated FAQ or None
        """
        return self.faq_repo.update_faq(
            faq_id=faq_id,
            updated_by=admin_id,
            **updates,
        )

    def delete_faq(self, faq_id: str) -> bool:
        """Delete FAQ.

        Args:
            faq_id: FAQ UUID

        Returns:
            True if deleted
        """
        return self.faq_repo.delete_faq(faq_id)

    def reorder_faqs(
        self,
        faq_ids: list[str],
        admin_id: str,
    ) -> bool:
        """Reorder FAQs within category.

        Args:
            faq_ids: List of FAQ IDs in desired order
            admin_id: Admin user ID

        Returns:
            True if reordering succeeded
        """
        return self.faq_repo.reorder_faqs(
            faq_ids_in_order=faq_ids,
            updated_by=admin_id,
        )

    # ========================================================================
    # Category Management
    # ========================================================================

    def get_categories(self) -> list[dict[str, Any]]:
        """Get all FAQ categories.

        Returns:
            List of categories sorted by sort_order
        """
        return self.faq_repo.list_categories()

    def create_category(
        self,
        name: str,
        slug: str,
        icon: str = "",
        sort_order: int = 0,
    ) -> dict[str, Any]:
        """Create new category.

        Args:
            name: Category name
            slug: URL-safe slug
            icon: Icon class or emoji
            sort_order: Sort order

        Returns:
            Created category
        """
        return self.faq_repo.create_category(
            name=name,
            slug=slug,
            icon=icon,
            sort_order=sort_order,
        )

    def update_category(
        self,
        category_id: str,
        **updates: Any,
    ) -> dict[str, Any] | None:
        """Update category.

        Args:
            category_id: Category UUID
            **updates: Fields to update

        Returns:
            Updated category or None
        """
        return self.faq_repo.update_category(
            category_id=category_id,
            **updates,
        )

    def delete_category(self, category_id: str) -> bool:
        """Delete category.

        Args:
            category_id: Category UUID

        Returns:
            True if deleted
        """
        return self.faq_repo.delete_category(category_id)

    # ========================================================================
    # Analytics
    # ========================================================================

    def get_faq_analytics(self) -> dict[str, Any]:
        """Get FAQ analytics.

        Returns:
            Dict with analytics data
        """
        # Top viewed FAQs
        top_viewed = self.faq_repo.get_top_viewed_faqs(limit=10)

        # FAQs ohne Views
        unviewed = self.faq_repo.get_unviewed_faqs()

        # Alle FAQs für Statistik
        all_faqs, _ = self.faq_repo.list_faqs(limit=1000)
        published = [f for f in all_faqs if f.get("status") == "published"]
        drafts = [f for f in all_faqs if f.get("status") == "draft"]

        # Total views
        total_views = sum(f.get("view_count", 0) for f in all_faqs)

        return {
            "total_faqs": len(all_faqs),
            "published": len(published),
            "drafts": len(drafts),
            "total_views": total_views,
            "top_viewed": [
                {
                    "faq_id": f.get("faq_id"),
                    "question": f.get("question"),
                    "category": f.get("category"),
                    "view_count": f.get("view_count", 0),
                }
                for f in top_viewed
            ],
            "unviewed_count": len(unviewed),
        }
