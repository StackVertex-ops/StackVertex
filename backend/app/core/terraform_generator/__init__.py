"""Terraform Generator Package.

Generates Terraform HCL code from Architecture JSON.
"""

from app.core.terraform_generator.generator import TerraformGenerator
from app.core.terraform_generator.file_builder import TerraformProject, TerraformFileBuilder
from app.core.terraform_generator.component_mapper import ComponentMapper
from app.core.terraform_generator.validators import TerraformValidator
from app.core.terraform_generator.exceptions import (
    TerraformGeneratorException,
    TemplateNotFoundError,
    TemplateRenderError,
    TerraformValidationError,
    UnsupportedComponentError,
    InvalidConfigurationError,
)

__all__ = [
    # Main Generator
    "TerraformGenerator",
    # File Building
    "TerraformProject",
    "TerraformFileBuilder",
    # Mapping & Validation
    "ComponentMapper",
    "TerraformValidator",
    # Exceptions
    "TerraformGeneratorException",
    "TemplateNotFoundError",
    "TemplateRenderError",
    "TerraformValidationError",
    "UnsupportedComponentError",
    "InvalidConfigurationError",
]
