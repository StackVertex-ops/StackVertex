"""Terraform Generator Exceptions.

Custom exceptions für Terraform-Generierung.
"""



class TerraformGeneratorException(Exception):
    """Base Exception für Terraform Generator."""
    pass


class TemplateNotFoundError(TerraformGeneratorException):
    """Exception wenn ein Template nicht gefunden wurde."""

    def __init__(self, template_name: str, component_type: str):
        super().__init__(
            f"Template '{template_name}' not found for component type '{component_type}'"
        )
        self.template_name = template_name
        self.component_type = component_type


class TemplateRenderError(TerraformGeneratorException):
    """Exception bei Fehlern während Template-Rendering."""

    def __init__(self, template_name: str, error: str):
        super().__init__(f"Failed to render template '{template_name}': {error}")
        self.template_name = template_name
        self.error = error


class TerraformValidationError(TerraformGeneratorException):
    """Exception bei Terraform-Validierungsfehlern."""

    def __init__(self, message: str, errors: list[str] | None = None):
        super().__init__(message)
        self.errors = errors or []

    def __str__(self) -> str:
        """String representation mit Fehler-Details."""
        base = super().__str__()
        if self.errors:
            error_details = "\n".join(f"  - {err}" for err in self.errors)
            return f"{base}\nValidation Errors:\n{error_details}"
        return base


class UnsupportedComponentError(TerraformGeneratorException):
    """Exception für nicht-unterstützte Component-Types."""

    def __init__(self, component_type: str):
        super().__init__(f"Unsupported component type: '{component_type}'")
        self.component_type = component_type


class InvalidConfigurationError(TerraformGeneratorException):
    """Exception für ungültige Konfigurationen."""

    def __init__(self, message: str, field: str | None = None):
        super().__init__(message)
        self.field = field
