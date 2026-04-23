"""Tests für TerraformFileBuilder.

Testet Terraform File Structure Generation.
"""

import pytest
from pathlib import Path

from app.core.terraform_generator.file_builder import (
    TerraformFileBuilder,
    TerraformProject,
)


class TestTerraformProject:
    """Tests für TerraformProject."""

    def test_create_empty_project(self):
        """Test: Leeres Projekt erstellen."""
        project = TerraformProject()

        assert project.files == {}
        assert project.provider == "aws"
        assert project.region == "us-east-1"

    def test_add_file(self):
        """Test: Datei hinzufügen."""
        project = TerraformProject()
        project.add_file("main.tf", "# Main file")

        assert "main.tf" in project.files
        assert project.files["main.tf"] == "# Main file"

    def test_get_file_count(self):
        """Test: Anzahl Dateien."""
        project = TerraformProject()
        assert project.get_file_count() == 0

        project.add_file("main.tf", "content")
        assert project.get_file_count() == 1

        project.add_file("vars.tf", "content")
        assert project.get_file_count() == 2

    def test_get_total_lines(self):
        """Test: Gesamtzahl Zeilen."""
        project = TerraformProject()
        project.add_file("main.tf", "line1\nline2\nline3")

        assert project.get_total_lines() == 3

    def test_write_to_directory(self, tmp_path):
        """Test: Dateien in Verzeichnis schreiben."""
        project = TerraformProject()
        project.add_file("main.tf", "# Main")
        project.add_file("vars.tf", "# Variables")

        # Write to temp directory
        project.write_to_directory(tmp_path)

        # Prüfe ob Dateien existieren
        assert (tmp_path / "main.tf").exists()
        assert (tmp_path / "vars.tf").exists()

        # Prüfe Inhalt
        assert (tmp_path / "main.tf").read_text() == "# Main"


class TestTerraformFileBuilder:
    """Tests für TerraformFileBuilder."""

    def test_create_builder(self):
        """Test: Builder erstellen."""
        builder = TerraformFileBuilder()

        assert builder.resources == []
        assert builder.variables == []
        assert builder.outputs == []

    def test_add_resource(self):
        """Test: Resource hinzufügen."""
        builder = TerraformFileBuilder()
        builder.add_resource('resource "aws_vpc" "main" {}')

        assert len(builder.resources) == 1
        assert 'aws_vpc' in builder.resources[0]

    def test_add_variable(self):
        """Test: Variable hinzufügen."""
        builder = TerraformFileBuilder()
        builder.add_variable("region", type_="string", description="AWS Region")

        assert len(builder.variables) == 1
        assert builder.variables[0]["name"] == "region"
        assert builder.variables[0]["type"] == "string"

    def test_add_variable_with_default(self):
        """Test: Variable mit Default-Wert."""
        builder = TerraformFileBuilder()
        builder.add_variable("region", default="us-east-1")

        assert builder.variables[0]["default"] == "us-east-1"

    def test_add_output(self):
        """Test: Output hinzufügen."""
        builder = TerraformFileBuilder()
        builder.add_output(
            "vpc_id",
            "aws_vpc.main.id",
            description="VPC ID"
        )

        assert len(builder.outputs) == 1
        assert builder.outputs[0]["name"] == "vpc_id"
        assert builder.outputs[0]["value"] == "aws_vpc.main.id"

    def test_add_output_sensitive(self):
        """Test: Sensitive Output."""
        builder = TerraformFileBuilder()
        builder.add_output("db_password", "var.password", sensitive=True)

        assert builder.outputs[0]["sensitive"] is True

    def test_add_local(self):
        """Test: Local Variable hinzufügen."""
        builder = TerraformFileBuilder()
        builder.add_local("project_name", "my-project")

        assert "project_name" in builder.locals
        assert builder.locals["project_name"] == "my-project"

    def test_build_provider_tf(self):
        """Test: provider.tf generieren."""
        builder = TerraformFileBuilder()
        content = builder.build_provider_tf("aws", "us-east-1")

        assert "terraform {" in content
        assert "provider \"aws\"" in content
        assert 'region = "us-east-1"' in content

    def test_build_variables_tf_empty(self):
        """Test: variables.tf mit 0 Variables."""
        builder = TerraformFileBuilder()
        content = builder.build_variables_tf()

        assert "No variables" in content

    def test_build_variables_tf(self):
        """Test: variables.tf generieren."""
        builder = TerraformFileBuilder()
        builder.add_variable("region", type_="string", default="us-east-1")

        content = builder.build_variables_tf()

        assert 'variable "region"' in content
        assert 'type        = string' in content
        assert 'default     = "us-east-1"' in content

    def test_build_outputs_tf_empty(self):
        """Test: outputs.tf mit 0 Outputs."""
        builder = TerraformFileBuilder()
        content = builder.build_outputs_tf()

        assert "No outputs" in content

    def test_build_outputs_tf(self):
        """Test: outputs.tf generieren."""
        builder = TerraformFileBuilder()
        builder.add_output("vpc_id", "aws_vpc.main.id", description="VPC ID")

        content = builder.build_outputs_tf()

        assert 'output "vpc_id"' in content
        assert 'value       = aws_vpc.main.id' in content
        assert 'description = "VPC ID"' in content

    def test_build_main_tf_empty(self):
        """Test: main.tf ohne Resources."""
        builder = TerraformFileBuilder()
        content = builder.build_main_tf()

        assert "Main Resources" in content

    def test_build_main_tf_with_resources(self):
        """Test: main.tf mit Resources."""
        builder = TerraformFileBuilder()
        builder.add_resource('resource "aws_vpc" "main" {}')

        content = builder.build_main_tf()

        assert 'resource "aws_vpc" "main"' in content

    def test_build_main_tf_with_locals(self):
        """Test: main.tf mit Locals."""
        builder = TerraformFileBuilder()
        builder.add_local("project", "my-project")

        content = builder.build_main_tf()

        assert "locals {" in content
        assert 'project = "my-project"' in content

    def test_build_project(self):
        """Test: Komplettes Projekt bauen."""
        builder = TerraformFileBuilder()
        builder.add_variable("region", default="us-east-1")
        builder.add_resource('resource "aws_vpc" "main" {}')
        builder.add_output("vpc_id", "aws_vpc.main.id")

        project = builder.build_project("aws", "us-east-1", "test-project")

        assert "provider.tf" in project.files
        assert "variables.tf" in project.files
        assert "main.tf" in project.files
        assert "outputs.tf" in project.files
        assert project.provider == "aws"
        assert project.region == "us-east-1"
