"""Terraform Generator V2 - Component-based Architecture.

Generiert Terraform HCL Code aus Architecture JSON (Infrastructure Designer).
Im Gegensatz zu V1 (Blueprint-basiert) ist dieser Generator komponentenbasiert.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

logger = logging.getLogger(__name__)


class TerraformGeneratorV2:
    """Generate Terraform from Architecture JSON (component-based)."""

    def __init__(self, template_dir: Optional[Path] = None):
        """Initialisiert Generator.

        Args:
            template_dir: Template-Verzeichnis (default: backend/templates/terraform/components)
        """
        if template_dir is None:
            backend_dir = Path(__file__).parent.parent.parent
            template_dir = backend_dir / "templates" / "terraform"

        self.template_dir = template_dir
        self.components_template_dir = template_dir / "components"

        logger.info(f"Template directory: {self.template_dir}")
        logger.info(f"Components template directory: {self.components_template_dir}")

        # Jinja2 Environment
        self.env = Environment(
            loader=FileSystemLoader([
                str(self.template_dir),
                str(self.components_template_dir)
            ]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Supported component types
        self.supported_types = {
            'vpc', 'subnet', 'ec2', 'rds', 's3', 'lambda',
            'security_group', 'internet_gateway', 'nat_gateway',
            'route_table', 'alb', 'target_group', 'dynamodb', 'iam'
        }

    def generate(self, architecture_json: Dict[str, Any]) -> Dict[str, str]:
        """Generiert Terraform files aus Architecture JSON.

        Args:
            architecture_json: Complete architecture JSON from designer

        Returns:
            Dict of filename -> content:
            {
                'main.tf': '...',
                'variables.tf': '...',
                'outputs.tf': '...',
                'vpc.tf': '...',
                'ec2.tf': '...'
            }

        Raises:
            ValueError: Bei invalider Architektur
        """
        logger.info("Starting Terraform generation (V2)...")

        files = {}

        # Extract metadata
        metadata = architecture_json.get('metadata', {})
        project_name = metadata.get('name', 'infrastructure')
        provider = metadata.get('provider', 'aws')

        # Extract components
        components = architecture_json.get('components', {})
        if not components:
            raise ValueError("No components found in architecture JSON")

        # Extract connections
        connections = architecture_json.get('connections', [])

        logger.info(
            f"Generating for {len(components)} components, "
            f"{len(connections)} connections"
        )

        # 1. Generate main.tf (provider configuration)
        files['main.tf'] = self._generate_main_tf(architecture_json)

        # 2. Generate variables.tf
        files['variables.tf'] = self._generate_variables_tf(architecture_json)

        # 3. Group components by type
        components_by_type = self._group_components_by_type(components)

        # 4. Generate component-specific .tf files
        for comp_type, comps in components_by_type.items():
            filename = f'{comp_type}.tf'
            try:
                files[filename] = self._generate_component_file(
                    comp_type,
                    comps,
                    components,
                    connections,
                    architecture_json
                )
                logger.info(f"Generated {filename} with {len(comps)} resources")
            except Exception as e:
                logger.error(f"Failed to generate {filename}: {e}")
                # Continue mit nächstem type

        # 5. Generate outputs.tf
        files['outputs.tf'] = self._generate_outputs_tf(components)

        logger.info(f"Generated {len(files)} Terraform files")

        return files

    def _generate_main_tf(self, architecture: Dict[str, Any]) -> str:
        """Generiert main.tf mit provider und terraform block."""
        metadata = architecture.get('metadata', {})

        try:
            template = self.env.get_template('components/main.tf.j2')
        except TemplateNotFound:
            # Fallback: Simple hardcoded version
            logger.warning("Template components/main.tf.j2 not found, using fallback")
            return self._generate_main_tf_fallback(architecture)

        return template.render(
            project_name=metadata.get('name', 'infrastructure'),
            region=self._get_primary_region(architecture),
            provider=metadata.get('provider', 'aws')
        )

    def _generate_main_tf_fallback(self, architecture: Dict[str, Any]) -> str:
        """Fallback für main.tf wenn Template fehlt."""
        metadata = architecture.get('metadata', {})
        project_name = metadata.get('name', 'infrastructure')
        region = self._get_primary_region(architecture)

        return f"""# ============================================================================
# {project_name} - Infrastructure as Code
# ============================================================================
# Generated by OverCloud Infrastructure Designer

terraform {{
  required_version = ">= 1.0"

  required_providers {{
    aws = {{
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }}
  }}
}}

provider "aws" {{
  region = var.aws_region

  default_tags {{
    tags = {{
      Project     = "{project_name}"
      Environment = var.environment
      ManagedBy   = "OverCloud"
    }}
  }}
}}
"""

    def _generate_variables_tf(self, architecture: Dict[str, Any]) -> str:
        """Generiert variables.tf."""
        variables = self._extract_variables(architecture)

        try:
            template = self.env.get_template('components/variables.tf.j2')
            return template.render(variables=variables)
        except TemplateNotFound:
            logger.warning("Template components/variables.tf.j2 not found, using fallback")
            return self._generate_variables_tf_fallback(variables)

    def _generate_variables_tf_fallback(self, variables: List[Dict]) -> str:
        """Fallback für variables.tf."""
        lines = [
            "# ============================================================================",
            "# Variables",
            "# ============================================================================",
            ""
        ]

        for var in variables:
            lines.append(f'variable "{var["name"]}" {{')
            lines.append(f'  type        = {var["type"]}')
            lines.append(f'  description = "{var["description"]}"')

            if 'default' in var:
                default_value = var['default']
                if isinstance(default_value, str):
                    lines.append(f'  default     = "{default_value}"')
                elif isinstance(default_value, bool):
                    lines.append(f'  default     = {str(default_value).lower()}')
                elif isinstance(default_value, (int, float)):
                    lines.append(f'  default     = {default_value}')
                else:
                    # Dict or List - use multi-line
                    lines.append(f'  default     = {default_value}')

            lines.append("}")
            lines.append("")

        return "\n".join(lines)

    def _generate_component_file(
        self,
        comp_type: str,
        components: List[Tuple[str, Dict]],
        all_components: Dict,
        connections: List[Dict],
        architecture: Dict
    ) -> str:
        """Generiert .tf file für specific component type."""
        template_name = f'{comp_type}.tf.j2'

        try:
            template = self.env.get_template(template_name)
        except TemplateNotFound:
            # Try in components subdirectory
            try:
                template = self.env.get_template(f'components/{template_name}')
            except TemplateNotFound:
                logger.warning(
                    f"Template {template_name} not found, using generic template"
                )
                return self._generate_generic_component_file(
                    comp_type, components, all_components
                )

        # Prepare component data for template
        components_data = []
        for comp_id, comp_data in components:
            dependencies = self._get_dependencies(
                comp_id, all_components, connections, architecture
            )

            # Build depends_on statements mit korrekten resource types
            depends_on_statements = []
            for dep in dependencies:
                resource_type = self._get_resource_type(dep)
                depends_on_statements.append(f'aws_{resource_type}.{dep}')

            components_data.append({
                'id': comp_id,
                'name': comp_data.get('name', comp_id),
                'config': comp_data.get('config', {}),
                'dependencies': dependencies,
                'depends_on': depends_on_statements,
            })

        return template.render(
            components=components_data,
            type=comp_type
        )

    def _generate_generic_component_file(
        self,
        comp_type: str,
        components: List[Tuple[str, Dict]],
        all_components: Dict
    ) -> str:
        """Generiert generischen Terraform Code ohne Template."""
        lines = [
            f"# ============================================================================",
            f"# {comp_type.upper()} Resources",
            f"# ============================================================================",
            f"# WARNING: Generic template used - please create {comp_type}.tf.j2 template",
            ""
        ]

        for comp_id, comp_data in components:
            config = comp_data.get('config', {})
            name = comp_data.get('name', comp_id)

            lines.append(f'# {name}')
            lines.append(f'resource "aws_{comp_type}" "{comp_id}" {{')
            lines.append(f'  # TODO: Configure {comp_type} resource')

            # Add basic config entries
            for key, value in config.items():
                if isinstance(value, str):
                    lines.append(f'  {key} = "{value}"')
                elif isinstance(value, bool):
                    lines.append(f'  {key} = {str(value).lower()}')
                elif isinstance(value, (int, float)):
                    lines.append(f'  {key} = {value}')

            lines.append("")
            lines.append("  tags = {")
            lines.append(f'    Name = "{name}"')
            lines.append("  }")
            lines.append("}")
            lines.append("")

        return "\n".join(lines)

    def _generate_outputs_tf(self, components: Dict[str, Any]) -> str:
        """Generiert outputs.tf."""
        outputs = self._extract_outputs(components)

        try:
            template = self.env.get_template('components/outputs.tf.j2')
            return template.render(outputs=outputs)
        except TemplateNotFound:
            logger.warning("Template components/outputs.tf.j2 not found, using fallback")
            return self._generate_outputs_tf_fallback(outputs)

    def _generate_outputs_tf_fallback(self, outputs: List[Dict]) -> str:
        """Fallback für outputs.tf."""
        lines = [
            "# ============================================================================",
            "# Outputs",
            "# ============================================================================",
            ""
        ]

        for output in outputs:
            lines.append(f'output "{output["name"]}" {{')
            lines.append(f'  description = "{output["description"]}"')
            lines.append(f'  value       = {output["value"]}')
            lines.append("}")
            lines.append("")

        return "\n".join(lines)

    def _group_components_by_type(
        self,
        components: Dict[str, Any]
    ) -> Dict[str, List[Tuple[str, Dict]]]:
        """Gruppiert Components nach Type.

        Returns:
            Dict {component_type: [(comp_id, comp_data), ...]}
        """
        grouped: Dict[str, List[Tuple[str, Dict]]] = {}

        for comp_id, comp_data in components.items():
            comp_type = comp_data.get('type')

            if not comp_type:
                logger.warning(f"Component {comp_id} hat keinen type")
                continue

            if comp_type not in grouped:
                grouped[comp_type] = []

            grouped[comp_type].append((comp_id, comp_data))

        return grouped

    def _get_dependencies(
        self,
        comp_id: str,
        components: Dict,
        connections: List[Dict],
        architecture: Dict
    ) -> List[str]:
        """Ermittelt Terraform Dependencies für ein Component.

        Returns:
            Liste von component IDs die dependencies sind
        """
        dependencies = []

        # 1. Dependencies aus connections (graph-based)
        for conn in connections:
            if conn.get('to') == comp_id:
                from_id = conn.get('from')
                if from_id and from_id in components:
                    dependencies.append(from_id)

        # 2. Component-specific dependencies (aus config)
        comp = components.get(comp_id, {})
        comp_type = comp.get('type')
        config = comp.get('config', {})

        if comp_type == 'ec2':
            # EC2 depends on subnet, security group, key pair
            if 'subnet' in config and config['subnet'] in components:
                dependencies.append(config['subnet'])

            if 'securityGroups' in config:
                for sg in config['securityGroups']:
                    if sg in components:
                        dependencies.append(sg)

        elif comp_type == 'subnet':
            # Subnet depends on VPC
            if 'vpc' in config and config['vpc'] in components:
                dependencies.append(config['vpc'])

        elif comp_type == 'rds':
            # RDS depends on subnet group, security groups
            if 'subnetGroup' in config and config['subnetGroup'] in components:
                dependencies.append(config['subnetGroup'])

            if 'securityGroups' in config:
                for sg in config['securityGroups']:
                    if sg in components:
                        dependencies.append(sg)

        elif comp_type == 'alb':
            # ALB depends on subnets, security groups
            if 'subnets' in config:
                for subnet in config['subnets']:
                    if subnet in components:
                        dependencies.append(subnet)

        # Remove duplicates
        dependencies = list(set(dependencies))

        return dependencies

    def _get_primary_region(self, architecture: Dict) -> str:
        """Ermittelt primary AWS region aus components."""
        components = architecture.get('components', {})

        # Find first VPC and use its region
        for comp in components.values():
            if comp.get('type') == 'vpc':
                return comp.get('config', {}).get('region', 'us-east-1')

        # Fallback to metadata
        metadata = architecture.get('metadata', {})
        return metadata.get('region', 'us-east-1')

    def _extract_variables(self, architecture: Dict) -> List[Dict]:
        """Extrahiert Terraform Variables aus Architecture."""
        metadata = architecture.get('metadata', {})

        variables = [
            {
                'name': 'aws_region',
                'type': 'string',
                'description': 'AWS Region',
                'default': self._get_primary_region(architecture)
            },
            {
                'name': 'environment',
                'type': 'string',
                'description': 'Environment (dev, staging, prod)',
                'default': 'dev'
            },
            {
                'name': 'project_name',
                'type': 'string',
                'description': 'Project name',
                'default': metadata.get('name', 'infrastructure')
            }
        ]

        return variables

    def _extract_outputs(self, components: Dict[str, Any]) -> List[Dict]:
        """Extrahiert Terraform Outputs aus Components."""
        outputs = []

        for comp_id, comp in components.items():
            comp_type = comp.get('type')
            comp_name = comp.get('name', comp_id)

            # VPC Outputs
            if comp_type == 'vpc':
                outputs.append({
                    'name': f'{comp_id}_id',
                    'description': f'VPC ID for {comp_name}',
                    'value': f'aws_vpc.{comp_id}.id'
                })
                outputs.append({
                    'name': f'{comp_id}_cidr',
                    'description': f'VPC CIDR for {comp_name}',
                    'value': f'aws_vpc.{comp_id}.cidr_block'
                })

            # EC2 Outputs
            elif comp_type == 'ec2':
                outputs.append({
                    'name': f'{comp_id}_private_ip',
                    'description': f'Private IP for {comp_name}',
                    'value': f'aws_instance.{comp_id}.private_ip'
                })

                # Public IP nur wenn vorhanden
                if comp.get('config', {}).get('hasPublicIp'):
                    outputs.append({
                        'name': f'{comp_id}_public_ip',
                        'description': f'Public IP for {comp_name}',
                        'value': f'aws_instance.{comp_id}.public_ip'
                    })

            # RDS Outputs
            elif comp_type == 'rds':
                outputs.append({
                    'name': f'{comp_id}_endpoint',
                    'description': f'RDS endpoint for {comp_name}',
                    'value': f'aws_db_instance.{comp_id}.endpoint'
                })
                outputs.append({
                    'name': f'{comp_id}_address',
                    'description': f'RDS address for {comp_name}',
                    'value': f'aws_db_instance.{comp_id}.address'
                })

            # S3 Outputs
            elif comp_type == 's3':
                outputs.append({
                    'name': f'{comp_id}_bucket_name',
                    'description': f'S3 bucket name for {comp_name}',
                    'value': f'aws_s3_bucket.{comp_id}.id'
                })
                outputs.append({
                    'name': f'{comp_id}_bucket_arn',
                    'description': f'S3 bucket ARN for {comp_name}',
                    'value': f'aws_s3_bucket.{comp_id}.arn'
                })

            # Lambda Outputs
            elif comp_type == 'lambda':
                outputs.append({
                    'name': f'{comp_id}_arn',
                    'description': f'Lambda ARN for {comp_name}',
                    'value': f'aws_lambda_function.{comp_id}.arn'
                })
                outputs.append({
                    'name': f'{comp_id}_invoke_arn',
                    'description': f'Lambda Invoke ARN for {comp_name}',
                    'value': f'aws_lambda_function.{comp_id}.invoke_arn'
                })

            # ALB Outputs
            elif comp_type == 'alb':
                outputs.append({
                    'name': f'{comp_id}_dns_name',
                    'description': f'ALB DNS name for {comp_name}',
                    'value': f'aws_lb.{comp_id}.dns_name'
                })
                outputs.append({
                    'name': f'{comp_id}_arn',
                    'description': f'ALB ARN for {comp_name}',
                    'value': f'aws_lb.{comp_id}.arn'
                })

        return outputs

    def _get_resource_type(self, component_id: str) -> str:
        """Mappt component_id zu Terraform resource type.

        Args:
            component_id: Component ID (z.B. "vpc-1", "ec2-main")

        Returns:
            Terraform resource type (z.B. "vpc", "instance")
        """
        # Extract type from ID (convention: type-name)
        if '-' in component_id:
            comp_type = component_id.split('-')[0]
        else:
            comp_type = component_id

        # Map to AWS resource type
        type_mapping = {
            'vpc': 'vpc',
            'subnet': 'subnet',
            'ec2': 'instance',
            'rds': 'db_instance',
            's3': 's3_bucket',
            'lambda': 'lambda_function',
            'security_group': 'security_group',
            'internet_gateway': 'internet_gateway',
            'nat_gateway': 'nat_gateway',
            'alb': 'lb',
            'target_group': 'lb_target_group',
        }

        return type_mapping.get(comp_type, comp_type)
