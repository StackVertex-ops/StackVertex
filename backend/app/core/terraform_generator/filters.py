"""Jinja2 Custom Filters für Terraform Templates.

Terraform-spezifische Filter für Template-Rendering.
"""

import re
from typing import Any, List, Dict


def terraform_bool(value: Any) -> str:
    """Konvertiert Python Bool zu Terraform Bool.

    Args:
        value: Python boolean oder truthy/falsy value

    Returns:
        Terraform bool string ("true" oder "false")

    Examples:
        >>> terraform_bool(True)
        'true'
        >>> terraform_bool(False)
        'false'
        >>> terraform_bool(None)
        'false'
    """
    return "true" if value else "false"


def terraform_string(value: Any) -> str:
    """Escaped String für Terraform HCL.

    Args:
        value: Wert zum escapen

    Returns:
        Quoted und escaped string

    Examples:
        >>> terraform_string("hello")
        '"hello"'
        >>> terraform_string('hello "world"')
        '"hello \\"world\\""'
    """
    if value is None:
        return '""'

    # Escape Quotes und Backslashes
    escaped = str(value).replace('\\', '\\\\').replace('"', '\\"')
    return f'"{escaped}"'


def terraform_list(value: List[Any]) -> str:
    """Konvertiert Python List zu Terraform List.

    Args:
        value: Python list

    Returns:
        Terraform list string

    Examples:
        >>> terraform_list(["a", "b", "c"])
        '["a", "b", "c"]'
        >>> terraform_list([1, 2, 3])
        '[1, 2, 3]'
    """
    if not value:
        return "[]"

    # String items werden quoted, andere nicht
    items = []
    for item in value:
        if isinstance(item, str):
            items.append(terraform_string(item))
        elif isinstance(item, bool):
            items.append(terraform_bool(item))
        else:
            items.append(str(item))

    return f"[{', '.join(items)}]"


def terraform_map(value: Dict[str, Any]) -> str:
    """Konvertiert Python Dict zu Terraform Map.

    Args:
        value: Python dict

    Returns:
        Terraform map string

    Examples:
        >>> terraform_map({"key": "value"})
        '{\\n  key = "value"\\n}'
    """
    if not value:
        return "{}"

    lines = []
    for key, val in value.items():
        # Key sanitieren
        safe_key = terraform_identifier(key)

        # Value formatieren
        if isinstance(val, str):
            formatted_val = terraform_string(val)
        elif isinstance(val, bool):
            formatted_val = terraform_bool(val)
        elif isinstance(val, list):
            formatted_val = terraform_list(val)
        elif isinstance(val, dict):
            formatted_val = terraform_map(val)
        else:
            formatted_val = str(val)

        lines.append(f"  {safe_key} = {formatted_val}")

    return "{\n" + "\n".join(lines) + "\n}"


def terraform_identifier(value: str) -> str:
    """Sanitized Identifier für Terraform (Resource-Namen, etc.).

    Entfernt ungültige Zeichen und ersetzt sie durch Underscores.

    Args:
        value: Original identifier

    Returns:
        Terraform-safe identifier

    Examples:
        >>> terraform_identifier("My Server")
        'my_server'
        >>> terraform_identifier("app-db-01")
        'app_db_01'
    """
    # Lowercase
    sanitized = value.lower()

    # Ersetze Leerzeichen und Bindestriche mit Underscores
    sanitized = sanitized.replace(" ", "_").replace("-", "_")

    # Entferne alle nicht-alphanumerischen Zeichen (außer _)
    sanitized = re.sub(r'[^a-z0-9_]', '', sanitized)

    # Stelle sicher, dass es mit Buchstabe beginnt
    if sanitized and not sanitized[0].isalpha():
        sanitized = f"r_{sanitized}"

    # Fallback wenn leer
    return sanitized or "resource"


def terraform_tags(tags: List[str]) -> str:
    """Konvertiert Tag-Array zu Terraform Tags Map.

    Args:
        tags: Liste von Tag-Strings

    Returns:
        Terraform tags map

    Examples:
        >>> terraform_tags(["prod", "web"])
        '{\\n  Name = "..."\\n  Environment = "prod"\\n  Type = "web"\\n}'
    """
    if not tags:
        return "{}"

    # Baue tags map
    tag_map = {}
    for tag in tags:
        # Versuche key=value Format zu parsen
        if "=" in tag or ":" in tag:
            sep = "=" if "=" in tag else ":"
            parts = tag.split(sep, 1)
            if len(parts) == 2:
                tag_map[parts[0].strip()] = parts[1].strip()
        else:
            # Einfacher tag wird als Environment oder Type kategorisiert
            if tag.lower() in ["dev", "test", "staging", "prod", "production"]:
                tag_map["Environment"] = tag
            else:
                tag_map.setdefault("Tags", []).append(tag) if isinstance(tag_map.get("Tags"), list) else None

    return terraform_map(tag_map)


# Filter Registry für Jinja2
TERRAFORM_FILTERS = {
    "tf_bool": terraform_bool,
    "tf_string": terraform_string,
    "tf_list": terraform_list,
    "tf_map": terraform_map,
    "tf_identifier": terraform_identifier,
    "tf_tags": terraform_tags,
}
