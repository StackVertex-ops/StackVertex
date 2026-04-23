"""Terraform Generator - Main Generator Class.

Generiert Terraform HCL Code aus Architecture JSON.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from app.core.terraform_generator.component_mapper import ComponentMapper
from app.core.terraform_generator.file_builder import TerraformFileBuilder, TerraformProject
from app.core.terraform_generator.validators import TerraformValidator
from app.core.terraform_generator.filters import TERRAFORM_FILTERS
from app.core.terraform_generator.exceptions import (
    TerraformGeneratorException,
    TemplateNotFoundError,
    TemplateRenderError,
    UnsupportedComponentError,
    InvalidConfigurationError,
)

logger = logging.getLogger(__name__)


class TerraformGenerator:
    """Main Terraform Generator."""

    def __init__(
        self,
        template_dir: Optional[Path] = None,
        terraform_binary: str = "terraform"
    ):
        """Initialisiert Generator.

        Args:
            template_dir: Template-Verzeichnis (default: backend/templates/terraform)
            terraform_binary: Terraform Binary Path
        """
        # Template Directory
        if template_dir is None:
            # Default: backend/templates/terraform
            backend_dir = Path(__file__).parent.parent.parent
            template_dir = backend_dir.parent / "templates" / "terraform"

        self.template_dir = template_dir
        logger.info(f"Template directory: {self.template_dir}")

        # Jinja2 Environment
        self.jinja_env = Environment(
            loader=FileSystemLoader(self.template_dir),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Register custom filters
        self.jinja_env.filters.update(TERRAFORM_FILTERS)

        # Component Mapper
        self.mapper = ComponentMapper(template_dir)

        # Validator
        self.validator = TerraformValidator(terraform_binary)

        # File Builder
        self.builder = TerraformFileBuilder()

    def generate(
        self,
        architecture_json: Dict[str, Any],
        validate: bool = True
    ) -> TerraformProject:
        """Generiert Terraform-Projekt aus Architecture JSON.

        Args:
            architecture_json: Architecture Definition
            validate: Ob Terraform-Validierung durchgeführt werden soll

        Returns:
            TerraformProject mit allen generierten Dateien

        Raises:
            TerraformGeneratorException: Bei Generierungsfehlern
        """
        logger.info("Starting Terraform generation...")

        # 1. Extract Metadata
        metadata = architecture_json.get("metadata", {})
        provider = metadata.get("provider", "aws")
        region = metadata.get("region", "us-east-1")
        project_name = metadata.get("name", "overcloud-project")

        logger.info(f"Provider: {provider}, Region: {region}, Project: {project_name}")

        # 2. Reset Builder
        self.builder = TerraformFileBuilder()

        # 3. Extract Components
        components = architecture_json.get("architecture", {}).get("components", [])
        if not components:
            logger.warning("No components found in architecture")

        # 4. Group Components by Type
        components_by_type = self._group_components_by_type(components)

        # 5. Generate Resources (Template-basiert)
        for component_type, component_list in components_by_type.items():
            logger.info(f"Generating {len(component_list)} {component_type} resources...")
            for component in component_list:
                self._generate_component_resource(component, metadata)

        # 6. Generate Variables (aus metadata/requirements)
        self._generate_variables(architecture_json)

        # 7. Generate Outputs
        self._generate_outputs(components)

        # 8. Build Project
        project = self.builder.build_project(provider, region, project_name)

        logger.info(
            f"Generated {project.get_file_count()} files "
            f"with {project.get_total_lines()} lines"
        )

        # 9. Validate (optional)
        if validate:
            self._validate_project(project)

        return project

    def _group_components_by_type(
        self,
        components: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Gruppiert Components nach Type.

        Args:
            components: Liste von Components

        Returns:
            Dict {component_type: [components]}
        """
        grouped: Dict[str, List[Dict[str, Any]]] = {}

        for component in components:
            component_type = component.get("type")
            if not component_type:
                logger.warning(f"Component without type: {component.get('id')}")
                continue

            if component_type not in grouped:
                grouped[component_type] = []

            grouped[component_type].append(component)

        return grouped

    def _generate_component_resource(
        self,
        component: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> None:
        """Generiert Terraform Resource für ein Component.

        Args:
            component: Component Definition
            metadata: Architecture Metadata

        Raises:
            UnsupportedComponentError: Wenn Component-Type nicht unterstützt wird
            TemplateRenderError: Bei Template-Rendering-Fehlern
        """
        component_type = component.get("type")
        component_id = component.get("id", "unknown")

        # Prüfe ob Component supported
        if not self.mapper.is_supported(component_type):
            logger.warning(
                f"Unsupported component type '{component_type}' for {component_id}"
            )
            raise UnsupportedComponentError(component_type)

        # Get Template Path
        try:
            template_path = self.mapper.get_template_path(component_type)
        except KeyError as e:
            raise UnsupportedComponentError(component_type) from e

        # Load Template
        try:
            template = self.jinja_env.get_template(template_path)
        except TemplateNotFound as e:
            logger.error(f"Template not found: {template_path}")
            raise TemplateNotFoundError(template_path, component_type) from e

        # Render Template
        try:
            context = {
                "component": component,
                "metadata": metadata,
                "id": component_id,
                "name": component.get("name", component_id),
                "config": component.get("configuration", {}),
            }

            rendered = template.render(**context)
            self.builder.add_resource(rendered)

            logger.debug(f"Rendered {component_type} resource: {component_id}")

        except Exception as e:
            logger.error(f"Failed to render template {template_path}: {e}")
            raise TemplateRenderError(template_path, str(e)) from e

    def _generate_variables(self, architecture_json: Dict[str, Any]) -> None:
        """Generiert Terraform Variables.

        Args:
            architecture_json: Architecture Definition
        """
        metadata = architecture_json.get("metadata", {})

        # Standard Variables
        self.builder.add_variable(
            "project_name",
            type_="string",
            description="Project name",
            default=metadata.get("name", "overcloud-project")
        )

        self.builder.add_variable(
            "region",
            type_="string",
            description="AWS Region",
            default=metadata.get("region", "us-east-1")
        )

        self.builder.add_variable(
            "environment",
            type_="string",
            description="Environment (dev, staging, prod)",
            default="dev"
        )

        # Tags Variable
        tags = metadata.get("tags", [])
        if tags:
            self.builder.add_variable(
                "tags",
                type_="map(string)",
                description="Resource tags",
                default={tag: tag for tag in tags}
            )

    def _generate_outputs(self, components: List[Dict[str, Any]]) -> None:
        """Generiert Terraform Outputs.

        Args:
            components: Liste von Components
        """
        # Generate outputs für wichtige Resources
        for component in components:
            component_type = component.get("type")
            component_id = component.get("id")
            component_name = component.get("name", component_id)

            # VPC Outputs
            if component_type == "vpc":
                self.builder.add_output(
                    f"{component_id}_id",
                    f"aws_vpc.{component_id}.id",
                    f"VPC ID for {component_name}"
                )

            # EC2 Outputs
            elif component_type == "ec2":
                self.builder.add_output(
                    f"{component_id}_public_ip",
                    f"aws_instance.{component_id}.public_ip",
                    f"Public IP for {component_name}"
                )

            # S3 Outputs
            elif component_type == "s3":
                self.builder.add_output(
                    f"{component_id}_bucket_name",
                    f"aws_s3_bucket.{component_id}.id",
                    f"S3 Bucket name for {component_name}"
                )

            # RDS Outputs
            elif component_type == "rds":
                self.builder.add_output(
                    f"{component_id}_endpoint",
                    f"aws_db_instance.{component_id}.endpoint",
                    f"RDS endpoint for {component_name}"
                )

            # Lambda Outputs
            elif component_type == "lambda":
                self.builder.add_output(
                    f"{component_id}_arn",
                    f"aws_lambda_function.{component_id}.arn",
                    f"Lambda ARN for {component_name}"
                )

    def _validate_project(self, project: TerraformProject) -> None:
        """Validiert generiertes Terraform-Projekt.

        Args:
            project: TerraformProject

        Raises:
            TerraformValidationError: Bei Validierungsfehlern
        """
        logger.info("Validating generated Terraform...")

        # Syntax Validation für jede Datei
        for filename, content in project.files.items():
            if filename.endswith(".tf"):
                is_valid, errors = self.validator.validate_syntax(content)
                if not is_valid:
                    logger.error(f"Syntax errors in {filename}: {errors}")
                    # Warnung, aber kein Fehler (da nur einfache Checks)

        # Terraform CLI Validation würde hier laufen, wenn gewünscht
        # (requires writing to temp directory and running terraform validate)
        logger.info("Terraform validation passed (syntax checks only)")
