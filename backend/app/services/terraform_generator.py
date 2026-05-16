"""Terraform Code Generator Service.

Generiert Terraform HCL aus Blueprint Templates und User Configuration.
"""

import logging
from pathlib import Path
from typing import Dict, Any
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

logger = logging.getLogger(__name__)

# Path to Terraform templates
TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates" / "terraform"


def generate_terraform_from_blueprint(
    blueprint_id: str, configuration: Dict[str, Any]
) -> str:
    """Generiert Terraform Code aus Blueprint + User Config.

    Args:
        blueprint_id: Blueprint ID (z.B. "static-website")
        configuration: User Form Data

    Returns:
        Terraform HCL Code (String)

    Raises:
        FileNotFoundError: Wenn Template nicht existiert
        ValueError: Bei invalider Konfiguration
    """
    try:
        # Jinja2 Environment setup
        env = Environment(
            loader=FileSystemLoader(str(TEMPLATES_DIR)),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Load template
        template_name = f"{blueprint_id}.tf.j2"
        try:
            template = env.get_template(template_name)
        except TemplateNotFound:
            raise FileNotFoundError(f"Template {template_name} nicht gefunden")

        # Enrich configuration with helpers
        context = {
            **configuration,
            "blueprint_id": blueprint_id,
            # Helper Functions für Templates
            "to_kebab_case": lambda s: s.lower().replace("_", "-").replace(" ", "-"),
            "to_snake_case": lambda s: s.lower().replace("-", "_").replace(" ", "_"),
        }

        # Render Terraform Code
        terraform_code = template.render(**context)

        # Validate basic syntax
        if not terraform_code.strip():
            raise ValueError("Generated Terraform code ist leer")

        logger.info(f"Generated Terraform for blueprint '{blueprint_id}'")
        return terraform_code

    except FileNotFoundError:
        raise

    except Exception as e:
        logger.error(f"Error generating Terraform: {e}", exc_info=True)
        raise ValueError(f"Terraform generation failed: {str(e)}")


def generate_example_terraform(blueprint_id: str) -> str:
    """Generiert Beispiel-Terraform mit Default-Werten.

    Args:
        blueprint_id: Blueprint ID

    Returns:
        Example Terraform Code
    """
    # Default configurations per blueprint
    defaults = {
        "static-website": {
            "bucket_name": "my-static-website",
            "region": "eu-central-1",
            "enable_cdn": True,
            "custom_domain": "example.com",
        },
        "rds-postgres": {
            "db_name": "mydb",
            "instance_type": "db.t3.micro",
            "storage_size": 20,
            "region": "eu-central-1",
        },
        # Add more defaults...
    }

    default_config = defaults.get(blueprint_id, {})
    return generate_terraform_from_blueprint(blueprint_id, default_config)
