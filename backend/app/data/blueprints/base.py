"""
Blueprint Base Models

Definiert die Basisklassen für alle OverCloud Blueprints.
Blueprints sind vorkonfigurierte Architektur-Templates mit realistischen Use Cases.
"""

from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
from enum import Enum


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
    description: Optional[str] = None
    price_factor: Optional[float] = None  # Preismultiplikator für diese Option


class FieldValidation(BaseModel):
    """Validierungsregeln für Formularfelder"""
    min: Optional[Union[int, float]] = None
    max: Optional[Union[int, float]] = None
    pattern: Optional[str] = None
    options: Optional[List[SelectOption]] = None
    required_if: Optional[Dict[str, Any]] = None  # Bedingungen für required


class BlueprintFormField(BaseModel):
    """Formularfeld für Blueprint-Konfiguration"""
    name: str = Field(..., description="Interner Feldname (snake_case)")
    type: FieldType = Field(..., description="Feldtyp")
    label: str = Field(..., description="Angezeigtes Label")
    description: str = Field(..., description="Hilfetext für den User")
    required: bool = Field(default=True, description="Pflichtfeld?")
    default: Optional[Any] = None
    validation: Optional[FieldValidation] = None
    constraints: Optional[str] = Field(
        None,
        description="AWS Constraint-Referenz (z.B. 'aws.rds.min_storage')"
    )
    depends_on: Optional[str] = Field(
        None,
        description="Feldname von dem dieses Feld abhängt"
    )


class CostEstimate(BaseModel):
    """Kostenabschätzung für Blueprint"""
    min_usd: float = Field(..., description="Minimale monatliche Kosten (USD)")
    typical_usd: float = Field(..., description="Typische monatliche Kosten (USD)")
    max_usd: float = Field(..., description="Maximale monatliche Kosten (USD)")
    breakdown: Optional[Dict[str, float]] = Field(
        None,
        description="Kostenaufschlüsselung nach Service"
    )
    assumptions: Optional[List[str]] = Field(
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
    use_cases: List[str] = Field(..., description="Konkrete Use Cases")
    features: List[str] = Field(default_factory=list, description="Feature-Liste")
    limitations: List[str] = Field(default_factory=list, description="Bekannte Limitierungen")
    icon: Optional[str] = Field(None, description="Icon-Name für UI")


class Blueprint(BaseModel):
    """Vollständiger Blueprint"""
    metadata: BlueprintMetadata
    form_schema: List[BlueprintFormField]
    aws_resources: List[str] = Field(
        ...,
        description="Liste der verwendeten AWS Services (z.B. ['S3', 'CloudFront'])"
    )
    terraform_templates: List[str] = Field(
        ...,
        description="Liste der Terraform Template-Pfade (relativ zu templates/terraform/)"
    )
    deployment_guide: Optional[str] = Field(
        None,
        description="Markdown-Guide für Deployment"
    )

    class Config:
        use_enum_values = True
