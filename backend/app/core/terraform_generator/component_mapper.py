"""Component-to-Template Mapping.

Maps Architecture Component Types zu Terraform Templates.
"""

from typing import Dict, Optional
from pathlib import Path

# Component Type → Template Path Mapping
COMPONENT_TEMPLATES: Dict[str, str] = {
    # Networking
    "vpc": "networking/vpc.tf.j2",
    "subnet": "networking/subnet.tf.j2",
    "internet_gateway": "networking/internet_gateway.tf.j2",
    "nat_gateway": "networking/nat_gateway.tf.j2",
    "route_table": "networking/route_table.tf.j2",
    "security_group": "networking/security_group.tf.j2",
    "network_acl": "networking/network_acl.tf.j2",

    # Compute
    "ec2": "compute/ec2.tf.j2",
    "lambda": "compute/lambda.tf.j2",
    "ecs": "compute/ecs.tf.j2",
    "eks": "compute/eks.tf.j2",
    "auto_scaling_group": "compute/auto_scaling_group.tf.j2",

    # Storage
    "s3": "storage/s3.tf.j2",
    "ebs": "storage/ebs.tf.j2",
    "efs": "storage/efs.tf.j2",

    # Database
    "rds": "database/rds.tf.j2",
    "dynamodb": "database/dynamodb.tf.j2",
    "elasticache": "database/elasticache.tf.j2",

    # Load Balancing
    "alb": "load_balancing/alb.tf.j2",
    "nlb": "load_balancing/nlb.tf.j2",
    "target_group": "load_balancing/target_group.tf.j2",
}

# Alternative/Alias Namen
COMPONENT_ALIASES: Dict[str, str] = {
    "network": "vpc",
    "virtual_private_cloud": "vpc",
    "instance": "ec2",
    "compute": "ec2",
    "function": "lambda",
    "bucket": "s3",
    "storage": "s3",
    "database": "rds",
    "db": "rds",
    "load_balancer": "alb",
    "application_load_balancer": "alb",
    "network_load_balancer": "nlb",
}


class ComponentMapper:
    """Maps Architecture Components zu Terraform Templates."""

    def __init__(self, template_dir: Optional[Path] = None):
        """Initialisiert Mapper.

        Args:
            template_dir: Custom Template Directory (default: backend/templates/terraform)
        """
        self.template_dir = template_dir
        self.templates = COMPONENT_TEMPLATES.copy()
        self.aliases = COMPONENT_ALIASES.copy()

    def get_template_path(self, component_type: str) -> str:
        """Gibt Template-Path für Component-Type zurück.

        Args:
            component_type: Type des Components (z.B. "vpc", "ec2")

        Returns:
            Relativer Template-Path (z.B. "networking/vpc.tf.j2")

        Raises:
            KeyError: Wenn Component-Type nicht unterstützt wird
        """
        # Normalisiere type (lowercase, strip)
        normalized_type = component_type.lower().strip()

        # Prüfe Alias
        if normalized_type in self.aliases:
            normalized_type = self.aliases[normalized_type]

        # Prüfe Template Mapping
        if normalized_type not in self.templates:
            raise KeyError(f"No template found for component type: {component_type}")

        return self.templates[normalized_type]

    def is_supported(self, component_type: str) -> bool:
        """Prüft ob Component-Type unterstützt wird.

        Args:
            component_type: Type des Components

        Returns:
            True wenn Template existiert, sonst False
        """
        try:
            self.get_template_path(component_type)
            return True
        except KeyError:
            return False

    def get_supported_types(self) -> list[str]:
        """Gibt Liste aller unterstützten Component-Types zurück.

        Returns:
            Liste von unterstützten Types
        """
        return list(self.templates.keys())

    def register_template(self, component_type: str, template_path: str) -> None:
        """Registriert ein neues Template (für Custom Components).

        Args:
            component_type: Type des Components
            template_path: Relativer Template-Path
        """
        self.templates[component_type] = template_path

    def register_alias(self, alias: str, component_type: str) -> None:
        """Registriert einen Alias für einen Component-Type.

        Args:
            alias: Alias-Name
            component_type: Ziel Component-Type
        """
        self.aliases[alias] = component_type
