"""Tests für TerraformValidator.

Testet Terraform HCL Validation (Syntax Checks).
"""

import pytest
from pathlib import Path

from app.core.terraform_generator.validators import TerraformValidator
from app.core.terraform_generator.exceptions import TerraformValidationError


class TestTerraformValidator:
    """Tests für TerraformValidator."""

    def test_create_validator(self):
        """Test: Validator erstellen."""
        validator = TerraformValidator()

        assert validator.terraform_binary == "terraform"

    def test_create_validator_custom_binary(self):
        """Test: Validator mit custom Binary Path."""
        validator = TerraformValidator(terraform_binary="/usr/local/bin/terraform")

        assert validator.terraform_binary == "/usr/local/bin/terraform"

    def test_validate_syntax_valid_hcl(self):
        """Test: Valide HCL Syntax."""
        validator = TerraformValidator()

        hcl_code = '''
        resource "aws_vpc" "main" {
          cidr_block = "10.0.0.0/16"
        }
        '''

        is_valid, errors = validator.validate_syntax(hcl_code)

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_syntax_unbalanced_braces(self):
        """Test: Unbalanced Braces werden erkannt."""
        validator = TerraformValidator()

        hcl_code = '''
        resource "aws_vpc" "main" {
          cidr_block = "10.0.0.0/16"
        '''  # Missing closing brace

        is_valid, errors = validator.validate_syntax(hcl_code)

        assert is_valid is False
        assert len(errors) > 0
        assert "braces" in errors[0].lower()

    def test_validate_syntax_unbalanced_quotes(self):
        """Test: Unbalanced Quotes werden erkannt."""
        validator = TerraformValidator()

        hcl_code = '''
        resource "aws_vpc" "main {
          cidr_block = "10.0.0.0/16"
        }
        '''  # Missing quote after "main

        is_valid, errors = validator.validate_syntax(hcl_code)

        assert is_valid is False
        assert "quotes" in errors[0].lower()

    def test_validate_syntax_empty_resource(self):
        """Test: Empty Resource Names werden erkannt."""
        validator = TerraformValidator()

        hcl_code = '''
        resource "" "" {
          cidr_block = "10.0.0.0/16"
        }
        '''

        is_valid, errors = validator.validate_syntax(hcl_code)

        assert is_valid is False
        assert "empty" in errors[0].lower()

    def test_validate_directory_not_exists(self):
        """Test: Nicht-existentes Verzeichnis wirft Exception."""
        validator = TerraformValidator()

        with pytest.raises(TerraformValidationError) as exc_info:
            validator.validate_directory(Path("/nonexistent/path"))

        assert "does not exist" in str(exc_info.value).lower()

    def test_validate_directory_no_tf_files(self, tmp_path):
        """Test: Verzeichnis ohne .tf Dateien wirft Exception."""
        validator = TerraformValidator()

        # Create empty directory
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        with pytest.raises(TerraformValidationError) as exc_info:
            validator.validate_directory(empty_dir)

        assert "no .tf files" in str(exc_info.value).lower()

    def test_check_terraform_installed(self):
        """Test: Check ob Terraform installiert ist."""
        validator = TerraformValidator()

        is_installed, version = validator.check_terraform_installed()

        # Test kann nicht garantieren dass Terraform installiert ist
        # Prüfe nur dass kein Error auftritt
        assert isinstance(is_installed, bool)

        if is_installed:
            assert version is not None
            assert "terraform" in version.lower()
        else:
            assert version is None

    def test_check_terraform_not_found(self):
        """Test: Terraform Binary nicht gefunden."""
        validator = TerraformValidator(terraform_binary="/nonexistent/terraform")

        is_installed, version = validator.check_terraform_installed()

        assert is_installed is False
        assert version is None
