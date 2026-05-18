"""Terraform Generator Package.

Generates Terraform HCL code from Architecture JSON.
"""

from app.core.terraform_generator.component_mapper import ComponentMapper
from app.core.terraform_generator.exceptions import (
    InvalidConfigurationError,
    TemplateNotFoundError,
    TemplateRenderError,
    TerraformGeneratorException,
    TerraformValidationError,
    UnsupportedComponentError,
)
from app.core.terraform_generator.file_builder import TerraformFileBuilder, TerraformProject
from app.core.terraform_generator.generator import TerraformGenerator
from app.core.terraform_generator.validators import TerraformValidator

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
