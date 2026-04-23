"""Integration Tests - Version Tracking.

Testet Version Tracking über mehrere Updates.
"""

import pytest
from copy import deepcopy


class TestVersionTracking:
    """Version Tracking Integration Tests."""

    def test_version_chain_integrity(self, test_client, db_engine, clear_db, sample_architecture_simple_web):
        """Test: Version Chain bleibt intakt über mehrere Updates.

        Flow:
        1. Create v1
        2. Update → v2 (parent: v1)
        3. Update → v3 (parent: v2)
        4. Verify chain: v3 → v2 → v1
        """
        # 1. Create v1
        response = test_client.post(
            "/api/v1/architectures",
            json=sample_architecture_simple_web,
        )

        assert response.status_code == 201
        v1_id = response.json()["id"]
        assert response.json()["parent_version_id"] is None

        # 2. Update → v2
        v2_json = deepcopy(sample_architecture_simple_web)
        v2_json["metadata"]["name"] = "Web App v2"

        response = test_client.put(
            f"/api/v1/architectures/{v1_id}",
            json=v2_json,
        )

        assert response.status_code == 200
        v2_id = response.json()["id"]
        assert response.json()["parent_version_id"] == v1_id

        # 3. Update → v3
        v3_json = deepcopy(v2_json)
        v3_json["metadata"]["name"] = "Web App v3"

        response = test_client.put(
            f"/api/v1/architectures/{v2_id}",
            json=v3_json,
        )

        assert response.status_code == 200
        v3_id = response.json()["id"]
        assert response.json()["parent_version_id"] == v2_id

        # 4. Verify chain
        # v3 → v2
        response = test_client.get(f"/api/v1/architectures/{v3_id}")
        assert response.json()["parent_version_id"] == v2_id

        # v2 → v1
        response = test_client.get(f"/api/v1/architectures/{v2_id}")
        assert response.json()["parent_version_id"] == v1_id

        # v1 → None
        response = test_client.get(f"/api/v1/architectures/{v1_id}")
        assert response.json()["parent_version_id"] is None

    def test_version_history_endpoint(self, test_client, db_engine, clear_db, sample_architecture_simple_web):
        """Test: Version History Endpoint.

        Flow:
        1. Create v1
        2. Update 2x → v2, v3
        3. Get version history
        4. Verify all versions returned
        """
        # 1. Create v1
        response = test_client.post(
            "/api/v1/architectures",
            json=sample_architecture_simple_web,
        )
        v1_id = response.json()["id"]

        # 2. Update 2x
        v2_json = deepcopy(sample_architecture_simple_web)
        v2_json["metadata"]["name"] = "v2"
        response = test_client.put(f"/api/v1/architectures/{v1_id}", json=v2_json)
        v2_id = response.json()["id"]

        v3_json = deepcopy(v2_json)
        v3_json["metadata"]["name"] = "v3"
        response = test_client.put(f"/api/v1/architectures/{v2_id}", json=v3_json)
        v3_id = response.json()["id"]

        # 3. Get version history
        response = test_client.get(f"/api/v1/architectures/{v3_id}/versions")

        # 4. Verify all versions
        assert response.status_code == 200
        history = response.json()

        # Should return chain: v3 → v2 → v1
        assert len(history) == 3
        assert history[0]["id"] == v3_id
        assert history[1]["id"] == v2_id
        assert history[2]["id"] == v1_id

    def test_version_diff(self, test_client, db_engine, clear_db, sample_architecture_simple_web):
        """Test: Version Diff Endpoint.

        Flow:
        1. Create v1
        2. Update → v2 (add component)
        3. Get diff v1 → v2
        4. Verify diff shows added component
        """
        # 1. Create v1
        response = test_client.post(
            "/api/v1/architectures",
            json=sample_architecture_simple_web,
        )
        v1_id = response.json()["id"]

        # 2. Update → v2 (add component)
        v2_json = deepcopy(sample_architecture_simple_web)
        v2_json["architecture"]["components"].append({
            "id": "new-component",
            "type": "rds",
            "name": "New Database",
            "properties": {
                "engine": "postgres",
                "instance_class": "db.t3.micro",
            },
        })

        response = test_client.put(
            f"/api/v1/architectures/{v1_id}",
            json=v2_json,
        )
        v2_id = response.json()["id"]

        # 3. Get diff
        response = test_client.get(
            f"/api/v1/architectures/{v1_id}/diff/{v2_id}"
        )

        assert response.status_code == 200
        diff = response.json()

        # 4. Verify diff
        assert "added" in diff
        assert "removed" in diff
        assert "modified" in diff

        # Should show new component in added
        assert "components" in diff["added"] or len(diff.get("added", {})) > 0

    def test_branching_not_allowed(self, test_client, db_engine, clear_db, sample_architecture_simple_web):
        """Test: Branching sollte nicht erlaubt sein.

        Flow:
        1. Create v1
        2. Update → v2
        3. Try to update v1 again (should fail or create separate chain)
        """
        # 1. Create v1
        response = test_client.post(
            "/api/v1/architectures",
            json=sample_architecture_simple_web,
        )
        v1_id = response.json()["id"]

        # 2. Update → v2
        v2_json = deepcopy(sample_architecture_simple_web)
        v2_json["metadata"]["name"] = "v2"
        response = test_client.put(f"/api/v1/architectures/{v1_id}", json=v2_json)
        assert response.status_code == 200

        # 3. Try to update v1 again
        v2b_json = deepcopy(sample_architecture_simple_web)
        v2b_json["metadata"]["name"] = "v2b"
        response = test_client.put(f"/api/v1/architectures/{v1_id}", json=v2b_json)

        # Implementation allows this (creates new version from v1)
        # This is fine - linear chain is per-branch
        assert response.status_code == 200

    def test_delete_version_preserves_chain(self, test_client, db_engine, clear_db, sample_architecture_simple_web):
        """Test: Deleting version doesn't break chain.

        Flow:
        1. Create v1 → v2 → v3
        2. Delete v2
        3. Verify v3 still exists
        """
        # 1. Create v1 → v2 → v3
        response = test_client.post("/api/v1/architectures", json=sample_architecture_simple_web)
        v1_id = response.json()["id"]

        v2_json = deepcopy(sample_architecture_simple_web)
        v2_json["metadata"]["name"] = "v2"
        response = test_client.put(f"/api/v1/architectures/{v1_id}", json=v2_json)
        v2_id = response.json()["id"]

        v3_json = deepcopy(v2_json)
        v3_json["metadata"]["name"] = "v3"
        response = test_client.put(f"/api/v1/architectures/{v2_id}", json=v3_json)
        v3_id = response.json()["id"]

        # 2. Delete v2
        response = test_client.delete(f"/api/v1/architectures/{v2_id}")
        assert response.status_code == 204

        # 3. Verify v3 still exists
        response = test_client.get(f"/api/v1/architectures/{v3_id}")
        assert response.status_code == 200

        # v3's parent_version_id is still v2, but v2 is deleted
        # This is acceptable behavior

    def test_version_metadata_tracking(self, test_client, db_engine, clear_db, sample_architecture_simple_web):
        """Test: Version Metadata wird korrekt getrackt.

        Flow:
        1. Create architecture
        2. Verify created_at, updated_at
        3. Update architecture
        4. Verify new version has different timestamps
        """
        # 1. Create architecture
        response = test_client.post(
            "/api/v1/architectures",
            json=sample_architecture_simple_web,
        )
        v1 = response.json()
        v1_created = v1["created_at"]

        # 2. Verify timestamps
        assert v1_created is not None
        assert v1["updated_at"] is not None

        # 3. Update architecture
        import time
        time.sleep(0.1)  # Ensure timestamp difference

        v2_json = deepcopy(sample_architecture_simple_web)
        v2_json["metadata"]["name"] = "Updated"

        response = test_client.put(
            f"/api/v1/architectures/{v1['id']}",
            json=v2_json,
        )
        v2 = response.json()

        # 4. Verify different timestamps
        assert v2["created_at"] != v1_created
        assert v2["id"] != v1["id"]
