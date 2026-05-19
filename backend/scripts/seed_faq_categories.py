#!/usr/bin/env python3
"""Seed Default FAQ Categories.

Erstellt die Standard-Kategorien für FAQs in DynamoDB:
- Allgemein
- Preise
- Technik
- Sicherheit
- Support
"""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.db.dynamodb import get_dynamodb_table
from app.repositories.faq import FaqRepository

DEFAULT_CATEGORIES = [
    {
        "name": "Allgemein",
        "slug": "general",
        "icon": "📌",
        "sort_order": 0,
    },
    {
        "name": "Preise",
        "slug": "pricing",
        "icon": "💰",
        "sort_order": 1,
    },
    {
        "name": "Technik",
        "slug": "technical",
        "icon": "⚙️",
        "sort_order": 2,
    },
    {
        "name": "Sicherheit",
        "slug": "security",
        "icon": "🔐",
        "sort_order": 3,
    },
    {
        "name": "Support",
        "slug": "support",
        "icon": "💬",
        "sort_order": 4,
    },
]


def seed_categories():
    """Seed default FAQ categories."""
    print("🌱 Seeding default FAQ categories...")

    table = get_dynamodb_table()
    faq_repo = FaqRepository(table=table)

    # Check if categories already exist
    existing = faq_repo.list_categories()
    if existing:
        print(f"⚠️  {len(existing)} categories already exist. Skipping seed.")
        return

    # Create categories
    for cat_data in DEFAULT_CATEGORIES:
        try:
            category = faq_repo.create_category(**cat_data)
            print(f"✅ Created category: {category['name']} ({category['slug']})")
        except Exception as e:
            print(f"❌ Failed to create category {cat_data['name']}: {e}")

    print("\n✨ Seeding complete!")


if __name__ == "__main__":
    seed_categories()
