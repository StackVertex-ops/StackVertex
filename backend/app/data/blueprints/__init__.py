"""
StackVertex Blueprint Library

Zentrale Registry für alle verfügbaren Blueprints.
Blueprints sind vorkonfigurierte Architektur-Templates mit realistischen Use Cases und fairen Preisen.
"""

from .base import Blueprint, BlueprintCategory, BlueprintDifficulty
from .simple_api import SIMPLE_API
from .spa import SPA

# Import aller Blueprints
from .static_website import STATIC_WEBSITE
from .three_tier_web import THREE_TIER_WEB
from .wordpress import WORDPRESS

# Blueprint Registry
BLUEPRINT_REGISTRY: dict[str, Blueprint] = {
    "static-website": STATIC_WEBSITE,
    "spa": SPA,
    "simple-api": SIMPLE_API,
    "three-tier-web": THREE_TIER_WEB,
    "wordpress": WORDPRESS,
}


def get_blueprint(blueprint_id: str) -> Blueprint | None:
    """
    Holt einen Blueprint anhand seiner ID.

    Args:
        blueprint_id: Blueprint ID (z.B. 'static-website')

    Returns:
        Blueprint oder None falls nicht gefunden
    """
    return BLUEPRINT_REGISTRY.get(blueprint_id)


def list_blueprints(
    category: BlueprintCategory | None = None,
    difficulty: BlueprintDifficulty | None = None,
    max_cost_usd: float | None = None,
) -> list[Blueprint]:
    """
    Listet alle Blueprints mit optionalen Filtern.

    Args:
        category: Filtere nach Kategorie (z.B. BlueprintCategory.STATIC)
        difficulty: Filtere nach Schwierigkeit (z.B. BlueprintDifficulty.BEGINNER)
        max_cost_usd: Filtere nach maximalen Kosten (typical_usd)

    Returns:
        Liste von Blueprints
    """
    blueprints = list(BLUEPRINT_REGISTRY.values())

    if category:
        blueprints = [bp for bp in blueprints if bp.metadata.category == category]

    if difficulty:
        blueprints = [bp for bp in blueprints if bp.metadata.difficulty == difficulty]

    if max_cost_usd is not None:
        blueprints = [
            bp for bp in blueprints
            if bp.metadata.estimated_cost.typical_usd <= max_cost_usd
        ]

    return blueprints


def get_blueprints_by_category() -> dict[str, list[Blueprint]]:
    """
    Gruppiert alle Blueprints nach Kategorie.

    Returns:
        Dict mit Kategorie -> Liste von Blueprints
    """
    result: dict[str, list[Blueprint]] = {}

    for blueprint in BLUEPRINT_REGISTRY.values():
        category = blueprint.metadata.category.value
        if category not in result:
            result[category] = []
        result[category].append(blueprint)

    return result


def search_blueprints(query: str) -> list[Blueprint]:
    """
    Sucht Blueprints nach Name, Description oder Use Cases.

    Args:
        query: Suchbegriff (case-insensitive)

    Returns:
        Liste von passenden Blueprints
    """
    query_lower = query.lower()
    results = []

    for blueprint in BLUEPRINT_REGISTRY.values():
        # Suche in Name
        if query_lower in blueprint.metadata.name.lower():
            results.append(blueprint)
            continue

        # Suche in Description
        if query_lower in blueprint.metadata.description.lower():
            results.append(blueprint)
            continue

        # Suche in Use Cases
        if any(query_lower in use_case.lower() for use_case in blueprint.metadata.use_cases):
            results.append(blueprint)
            continue

    return results


__all__ = [
    # Base Models
    "Blueprint",
    "BlueprintCategory",
    "BlueprintDifficulty",
    # Blueprints
    "STATIC_WEBSITE",
    "SPA",
    "SIMPLE_API",
    "THREE_TIER_WEB",
    "WORDPRESS",
    # Registry
    "BLUEPRINT_REGISTRY",
    # Helper Functions
    "get_blueprint",
    "list_blueprints",
    "get_blueprints_by_category",
    "search_blueprints",
]
