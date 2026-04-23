"""Tests für Terraform Jinja2 Filters.

Testet Custom Filters für Template-Rendering.
"""

import pytest

from app.core.terraform_generator.filters import (
    terraform_bool,
    terraform_string,
    terraform_list,
    terraform_map,
    terraform_identifier,
    terraform_tags,
)


class TestTerraformBool:
    """Tests für terraform_bool Filter."""

    def test_true_value(self):
        """Test: True → 'true'."""
        assert terraform_bool(True) == "true"

    def test_false_value(self):
        """Test: False → 'false'."""
        assert terraform_bool(False) == "false"

    def test_truthy_values(self):
        """Test: Truthy values → 'true'."""
        assert terraform_bool(1) == "true"
        assert terraform_bool("yes") == "true"
        assert terraform_bool([1, 2]) == "true"

    def test_falsy_values(self):
        """Test: Falsy values → 'false'."""
        assert terraform_bool(0) == "false"
        assert terraform_bool("") == "false"
        assert terraform_bool([]) == "false"
        assert terraform_bool(None) == "false"


class TestTerraformString:
    """Tests für terraform_string Filter."""

    def test_simple_string(self):
        """Test: Einfacher String wird quoted."""
        assert terraform_string("hello") == '"hello"'

    def test_string_with_quotes(self):
        """Test: Quotes werden escaped."""
        assert terraform_string('hello "world"') == '"hello \\"world\\""'

    def test_string_with_backslash(self):
        """Test: Backslashes werden escaped."""
        assert terraform_string("path\\to\\file") == '"path\\\\to\\\\file"'

    def test_none_value(self):
        """Test: None → empty string."""
        assert terraform_string(None) == '""'

    def test_number_as_string(self):
        """Test: Number wird als String formatiert."""
        assert terraform_string(123) == '"123"'


class TestTerraformList:
    """Tests für terraform_list Filter."""

    def test_empty_list(self):
        """Test: Leere Liste."""
        assert terraform_list([]) == "[]"

    def test_string_list(self):
        """Test: Liste mit Strings."""
        assert terraform_list(["a", "b", "c"]) == '["a", "b", "c"]'

    def test_number_list(self):
        """Test: Liste mit Zahlen."""
        assert terraform_list([1, 2, 3]) == "[1, 2, 3]"

    def test_bool_list(self):
        """Test: Liste mit Booleans."""
        assert terraform_list([True, False]) == "[true, false]"

    def test_mixed_list(self):
        """Test: Gemischte Liste."""
        result = terraform_list(["text", 42, True])
        assert '"text"' in result
        assert '42' in result
        assert 'true' in result


class TestTerraformMap:
    """Tests für terraform_map Filter."""

    def test_empty_map(self):
        """Test: Leeres Dict."""
        assert terraform_map({}) == "{}"

    def test_simple_map(self):
        """Test: Einfaches Dict."""
        result = terraform_map({"key": "value"})
        assert "key = " in result
        assert '"value"' in result

    def test_nested_map(self):
        """Test: Nested Dict."""
        result = terraform_map({"outer": {"inner": "value"}})
        assert "outer = " in result
        assert "inner = " in result

    def test_map_with_list(self):
        """Test: Dict mit Liste als Value."""
        result = terraform_map({"tags": ["tag1", "tag2"]})
        assert "tags = " in result
        assert '["tag1", "tag2"]' in result


class TestTerraformIdentifier:
    """Tests für terraform_identifier Filter."""

    def test_simple_identifier(self):
        """Test: Einfacher Identifier bleibt unverändert."""
        assert terraform_identifier("myserver") == "myserver"

    def test_uppercase_to_lowercase(self):
        """Test: Uppercase → Lowercase."""
        assert terraform_identifier("MyServer") == "myserver"

    def test_spaces_to_underscores(self):
        """Test: Spaces → Underscores."""
        assert terraform_identifier("My Server") == "my_server"

    def test_dashes_to_underscores(self):
        """Test: Dashes → Underscores."""
        assert terraform_identifier("my-server") == "my_server"

    def test_special_chars_removed(self):
        """Test: Special Characters werden entfernt."""
        assert terraform_identifier("my@server#123") == "myserver123"

    def test_starts_with_number(self):
        """Test: Identifier starting with number gets 'r_' prefix."""
        assert terraform_identifier("123server") == "r_123server"

    def test_empty_string(self):
        """Test: Empty string → 'resource'."""
        assert terraform_identifier("") == "resource"


class TestTerraformTags:
    """Tests für terraform_tags Filter."""

    def test_empty_tags(self):
        """Test: Leere Tag-Liste."""
        assert terraform_tags([]) == "{}"

    def test_environment_tags(self):
        """Test: Environment Tags werden erkannt."""
        result = terraform_tags(["prod"])
        assert "environment = " in result.lower()

    def test_key_value_tags(self):
        """Test: key=value Format."""
        result = terraform_tags(["env=prod", "team:backend"])
        assert "env = " in result
        assert "team = " in result
