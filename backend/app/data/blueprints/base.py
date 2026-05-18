"""
Blueprint Base Models

Definiert die Basisklassen für alle OverCloud Blueprints.
Blueprints sind vorkonfigurierte Architektur-Templates mit realistischen Use Cases.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class BlueprintCategory(str, Enum):
    """Blueprint-Kategorien"""
    STATIC = "static"
    WEBAPP = "webapp"
    API = "api"
    DATABASE = "database"
    SERVERLESS = "serverless"
    COMPUTE = "compute"


class BlueprintDifficulty(str, Enum):
    """Schwierigkeitsgrade für Blueprints"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class FieldType(str, Enum):
    """Unterstützte Formular-Feldtypen"""
    TEXT = "text"
    SELECT = "select"
    NUMBER = "number"
    CIDR = "cidr"
    TOGGLE = "toggle"
    MULTISELECT = "multiselect"


class SelectOption(BaseModel):
    """Option für Select-Felder"""
    value: str
    label: str
    description: str | None = None
    price_factor: float | None = None  # Preismultiplikator für diese Option


class FieldValidation(BaseModel):
    """Validierungsregeln für Formularfelder"""
    min: int | float | None = None
    max: int | float | None = None
    pattern: str | None = None
    options: list[SelectOption] | None = None
    required_if: dict[str, Any] | None = None  # Bedingungen für required


class BlueprintFormField(BaseModel):
    """Formularfeld für Blueprint-Konfiguration"""
    name: str = Field(..., description="Interner Feldname (snake_case)")
    type: FieldType = Field(..., description="Feldtyp")
    label: str = Field(..., description="Angezeigtes Label")
    description: str = Field(..., description="Hilfetext für den User")
    required: bool = Field(default=True, description="Pflichtfeld?")
    default: Any | None = None
    validation: FieldValidation | None = None
    constraints: str | None = Field(
        None,
        description="AWS Constraint-Referenz (z.B. 'aws.rds.min_storage')"
    )
    depends_on: str | None = Field(
        None,
        description="Feldname von dem dieses Feld abhängt"
    )


class CostEstimate(BaseModel):
    """Kostenabschätzung für Blueprint"""
    min_usd: float = Field(..., description="Minimale monatliche Kosten (USD)")
    typical_usd: float = Field(..., description="Typische monatliche Kosten (USD)")
    max_usd: float = Field(..., description="Maximale monatliche Kosten (USD)")
    breakdown: dict[str, float] | None = Field(
        None,
        description="Kostenaufschlüsselung nach Service"
    )
    assumptions: list[str] | None = Field(
        None,
        description="Annahmen für die Kostenberechnung"
    )


class BlueprintMetadata(BaseModel):
    """Metadaten für einen Blueprint"""
    id: str = Field(..., description="Eindeutige Blueprint-ID (kebab-case)")
    name: str = Field(..., description="Anzeigename")
    description: str = Field(..., description="Kurzbeschreibung (1-2 Sätze)")
    category: BlueprintCategory
    difficulty: BlueprintDifficulty
    estimated_cost: CostEstimate
    setup_time_minutes: int = Field(..., description="Geschätzte Setup-Zeit in Minuten")
    use_cases: list[str] = Field(..., description="Konkrete Use Cases")
    features: list[str] = Field(default_factory=list, description="Feature-Liste")
    limitations: list[str] = Field(default_factory=list, description="Bekannte Limitierungen")
    icon: str | None = Field(None, description="Icon-Name für UI")


class Blueprint(BaseModel):
    """Vollständiger Blueprint"""
    metadata: BlueprintMetadata
    form_schema: list[BlueprintFormField]
    aws_resources: list[str] = Field(
        ...,
        description="Liste der verwendeten AWS Services (z.B. ['S3', 'CloudFront'])"
    )
    terraform_templates: list[str] = Field(
        ...,
        description="Liste der Terraform Template-Pfade (relativ zu templates/terraform/)"
    )
    deployment_guide: str | None = Field(
        None,
        description="Markdown-Guide für Deployment"
    )

    class Config:
        use_enum_values = True
