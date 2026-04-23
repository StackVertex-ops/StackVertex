"""Tests für Validation API Endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestValidationEndpoint:
    """Tests für POST /api/v1/validate/architecture."""

    def test_validate_valid_architecture(self):
        """Test: Valide Architektur wird akzeptiert."""
        data = {
            "data": {
                "version": "1.0.0",
                "metadata": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "name": "Test Architecture",
                    "provider": "aws",
                    "created_at": "2024-03-24T10:00:00Z",
                    "updated_at": "2024-03-24T10:00:00Z",
                },
                "requirements": {},
                "architecture": {
                    "components": [],
                    "relationships": [],
                },
            }
        }

        response = client.post("/api/v1/validate/architecture", json=data)

        assert response.status_code == 200
        result = response.json()
        assert result["valid"] is True
        assert result["message"] == "Validierung erfolgreich"
        assert result["error_count"] == 0
        assert len(result["errors"]) == 0

    def test_validate_invalid_architecture_missing_field(self):
        """Test: Fehlende Pflichtfelder führen zu Validierungsfehler."""
        data = {
            "data": {
                "version": "1.0.0",
                # 'metadata' fehlt
                "requirements": {},
                "architecture": {
                    "components": [],
                    "relationships": [],
                },
            }
        }

        response = client.post("/api/v1/validate/architecture", json=data)

        assert response.status_code == 200
        result = response.json()
        assert result["valid"] is False
        assert result["message"] == "Validierung fehlgeschlagen"
        assert result["error_count"] > 0
        assert len(result["errors"]) > 0

        # Prüfe Fehlerdetails
        error = result["errors"][0]
        assert "message" in error
        assert "path" in error
        assert "validator" in error

    def test_validate_invalid_version_format(self):
        """Test: Ungültiges Versionsformat wird erkannt."""
        data = {
            "data": {
                "version": "not-a-semver",
                "metadata": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "name": "Test",
                    "provider": "aws",
                    "created_at": "2024-03-24T10:00:00Z",
                    "updated_at": "2024-03-24T10:00:00Z",
                },
                "requirements": {},
                "architecture": {
                    "components": [],
                    "relationships": [],
                },
            }
        }

        response = client.post("/api/v1/validate/architecture", json=data)

        assert response.status_code == 200
        result = response.json()
        assert result["valid"] is False
        assert result["error_count"] > 0

    def test_validate_invalid_provider_enum(self):
        """Test: Ungültiger Provider-Wert wird abgelehnt."""
        data = {
            "data": {
                "version": "1.0.0",
                "metadata": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "name": "Test",
                    "provider": "invalid-provider",
                    "created_at": "2024-03-24T10:00:00Z",
                    "updated_at": "2024-03-24T10:00:00Z",
                },
                "requirements": {},
                "architecture": {
                    "components": [],
                    "relationships": [],
                },
            }
        }

        response = client.post("/api/v1/validate/architecture", json=data)

        assert response.status_code == 200
        result = response.json()
        assert result["valid"] is False

    def test_validate_complex_valid_architecture(self):
        """Test: Komplexe valide Architektur mit Components."""
        data = {
            "data": {
                "version": "1.0.0",
                "metadata": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "name": "Web Application",
                    "description": "Simple web app",
                    "provider": "aws",
                    "region": "us-east-1",
                    "created_at": "2024-03-24T10:00:00Z",
                    "updated_at": "2024-03-24T10:00:00Z",
                    "tags": ["production", "web"],
                },
                "requirements": {
                    "functional": {
                        "workload_type": "web_application",
                    },
                    "non_functional": {
                        "security": {
                            "public_access": True,
                        }
                    },
                },
                "architecture": {
                    "components": [
                        {
                            "id": "web-server",
                            "type": "compute",
                            "name": "Web Server",
                            "provider_service": "ec2",
                            "configuration": {
                                "instance_type": "t3.micro",
                            },
                            "tags": {
                                "Environment": "production",
                            },
                        }
                    ],
                    "relationships": [],
                },
            }
        }

        response = client.post("/api/v1/validate/architecture", json=data)

        assert response.status_code == 200
        result = response.json()
        assert result["valid"] is True
        assert result["error_count"] == 0

    def test_validate_empty_request_body(self):
        """Test: Leerer Request-Body führt zu FastAPI-Validierungsfehler."""
        response = client.post("/api/v1/validate/architecture", json={})

        # FastAPI sollte 422 für fehlende Pflichtfelder zurückgeben
        assert response.status_code == 422

    def test_validate_malformed_json(self):
        """Test: Ungültiges JSON im Request."""
        response = client.post(
            "/api/v1/validate/architecture",
            data="not-valid-json",
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 422


class TestValidationHealthEndpoint:
    """Tests für GET /api/v1/validate/health."""

    def test_health_check_success(self):
        """Test: Health-Check ist erfolgreich."""
        response = client.get("/api/v1/validate/health")

        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "healthy"
        assert result["schema_loaded"] is True
        assert "schema_version" in result
        assert "schema_title" in result

    def test_health_check_returns_schema_info(self):
        """Test: Health-Check gibt Schema-Informationen zurück."""
        response = client.get("/api/v1/validate/health")

        assert response.status_code == 200
        result = response.json()
        assert "OverCloud" in result["schema_title"]
        assert "overcloud.io" in result["schema_version"]


class TestValidationErrorDetails:
    """Tests für Fehlerdetails in der Response."""

    def test_error_contains_all_required_fields(self):
        """Test: Fehler enthalten alle erforderlichen Felder."""
        data = {
            "data": {
                "version": "invalid",
                "metadata": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "name": "Test",
                    "provider": "aws",
                    "created_at": "2024-03-24T10:00:00Z",
                    "updated_at": "2024-03-24T10:00:00Z",
                },
                "requirements": {},
                "architecture": {
                    "components": [],
                    "relationships": [],
                },
            }
        }

        response = client.post("/api/v1/validate/architecture", json=data)

        assert response.status_code == 200
        result = response.json()
        assert result["valid"] is False
        assert len(result["errors"]) > 0

        error = result["errors"][0]
        # Prüfe alle erforderlichen Fehlerfelder
        assert "message" in error
        assert "path" in error
        assert "schema_path" in error
        assert "validator" in error
        assert "validator_value" in error

    def test_error_path_format(self):
        """Test: Fehler-Pfade sind korrekt formatiert."""
        data = {
            "data": {
                "version": "1.0.0",
                "metadata": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "name": "",  # Leerer Name - verletzt minLength: 1
                    "provider": "aws",
                    "created_at": "2024-03-24T10:00:00Z",
                    "updated_at": "2024-03-24T10:00:00Z",
                },
                "requirements": {},
                "architecture": {
                    "components": [],
                    "relationships": [],
                },
            }
        }

        response = client.post("/api/v1/validate/architecture", json=data)

        assert response.status_code == 200
        result = response.json()
        assert result["valid"] is False

        # Sollte Fehler mit korrektem Pfad haben
        assert any(
            "$.metadata.name" in error["path"] for error in result["errors"]
        )
