"""Tests für JSONDiff - JSON Diff Generator.

Testet Diff Generation zwischen Architecture JSONs.
"""

import pytest
from copy import deepcopy
from datetime import datetime

from app.core.json_engine.diff import JSONDiff, DiffResult
from app.core.json_engine.exceptions import DiffGenerationError


class TestJSONDiff:
    """Tests für JSONDiff."""

    def test_generate_diff_no_changes(self, sample_architecture_minimal):
        """Test: Diff zwischen identischen JSONs."""
        diff_gen = JSONDiff()

        # Ensure architecture structure
        if "architecture" not in sample_architecture_minimal:
            sample_architecture_minimal["architecture"] = {"components": []}

        result = diff_gen.generate_diff(
            sample_architecture_minimal,
            sample_architecture_minimal
        )

        assert len(result.added) == 0
        assert len(result.removed) == 0
        assert len(result.modified) == 0
        assert result.summary == "No changes"

    def test_generate_diff_added_keys(self):
        """Test: Diff mit hinzugefügten Keys."""
        diff_gen = JSONDiff()

        old_json = {"a": 1, "b": 2}
        new_json = {"a": 1, "b": 2, "c": 3}

        result = diff_gen.generate_diff(old_json, new_json)

        assert "$.c" in result.added
        assert result.added["$.c"] == 3
        assert len(result.removed) == 0
        assert len(result.modified) == 0

    def test_generate_diff_removed_keys(self):
        """Test: Diff mit entfernten Keys."""
        diff_gen = JSONDiff()

        old_json = {"a": 1, "b": 2, "c": 3}
        new_json = {"a": 1, "b": 2}

        result = diff_gen.generate_diff(old_json, new_json)

        assert "$.c" in result.removed
        assert result.removed["$.c"] == 3
        assert len(result.added) == 0

    def test_generate_diff_modified_values(self):
        """Test: Diff mit geänderten Werten."""
        diff_gen = JSONDiff()

        old_json = {"name": "Old Name", "value": 10}
        new_json = {"name": "New Name", "value": 10}

        result = diff_gen.generate_diff(old_json, new_json)

        assert "$.name" in result.modified
        assert result.modified["$.name"]["old"] == "Old Name"
        assert result.modified["$.name"]["new"] == "New Name"

    def test_generate_diff_nested_dicts(self):
        """Test: Diff mit nested dictionaries."""
        diff_gen = JSONDiff(deep=True)

        old_json = {"metadata": {"name": "Old", "version": "1.0.0"}}
        new_json = {"metadata": {"name": "New", "version": "1.0.0"}}

        result = diff_gen.generate_diff(old_json, new_json)

        assert "$.metadata.name" in result.modified

    def test_generate_diff_lists(self):
        """Test: Diff mit Listen."""
        diff_gen = JSONDiff(deep=True)

        old_json = {"items": [1, 2, 3]}
        new_json = {"items": [1, 2, 4]}

        result = diff_gen.generate_diff(old_json, new_json)

        # Liste hat sich geändert
        assert len(result.modified) > 0

    def test_generate_component_diff_added(self, sample_architecture_minimal):
        """Test: Component-Level Diff - Added Components."""
        diff_gen = JSONDiff()

        old_arch = deepcopy(sample_architecture_minimal)
        new_arch = deepcopy(sample_architecture_minimal)

        # Ensure architecture structure
        if "architecture" not in old_arch:
            old_arch["architecture"] = {"components": []}
        if "architecture" not in new_arch:
            new_arch["architecture"] = {"components": []}

        new_arch["architecture"]["components"].append({
            "id": "new-component",
            "type": "compute",
            "name": "New Server"
        })

        comp_diff = diff_gen.generate_component_diff(old_arch, new_arch)

        assert len(comp_diff["added_components"]) == 1
        assert comp_diff["added_components"][0]["id"] == "new-component"

    def test_generate_component_diff_removed(self, sample_architecture_simple_web):
        """Test: Component-Level Diff - Removed Components."""
        diff_gen = JSONDiff()

        old_arch = deepcopy(sample_architecture_simple_web)
        new_arch = deepcopy(sample_architecture_simple_web)

        # Ensure architecture has components
        if "architecture" not in old_arch or not old_arch["architecture"].get("components"):
            pytest.skip("sample_architecture_simple_web has no components")

        # Remove first component
        first_id = old_arch["architecture"]["components"][0]["id"]
        new_arch["architecture"]["components"] = old_arch["architecture"]["components"][1:]

        comp_diff = diff_gen.generate_component_diff(old_arch, new_arch)

        assert len(comp_diff["removed_components"]) >= 1

    def test_apply_diff(self):
        """Test: Diff auf Base JSON anwenden."""
        diff_gen = JSONDiff()

        base_json = {"a": 1, "b": 2}

        # Erstelle Diff
        diff = DiffResult()
        diff.added = {"$.c": 3}
        diff.modified = {"$.b": {"old": 2, "new": 20}}

        # Diff anwenden
        result = diff_gen.apply_diff(base_json, diff)

        assert result["c"] == 3
        assert result["b"] == 20
        assert result["a"] == 1

    def test_summary_generation(self):
        """Test: Summary Generation."""
        diff_gen = JSONDiff()

        old_json = {"a": 1}
        new_json = {"b": 2, "c": 3}

        result = diff_gen.generate_diff(old_json, new_json)

        assert "added" in result.summary
        assert "removed" in result.summary
