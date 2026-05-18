"""Deployment Executor - Führt Terraform in Kunden-Account aus.

Workflow:
1. Hole AWS Credentials für Kunden-Account
2. Generiere Terraform Code
3. Führe Terraform aus (init, plan, apply)
4. Kopiere User-Daten (S3 → Customer ECR/S3)
5. Verifiziere Deployment
"""

import subprocess
import tempfile
import logging
import json
from pathlib import Path
from typing import Dict, Optional

import boto3
from botocore.exceptions import ClientError

from app.services.aws_session import AWSSessionManager
from app.services.terraform_generator_v2 import TerraformGeneratorV2
from app.config import settings

logger = logging.getLogger(__name__)


class DeploymentExecutor:
    """Führt Terraform-Deployments in Kunden-AWS-Accounts aus."""

    def __init__(
        self,
        session_manager: Optional[AWSSessionManager] = None,
        terraform_generator: Optional[TerraformGeneratorV2] = None
    ):
        """Initialisiert Deployment Executor.

        Args:
            session_manager: AWS Session Manager
            terraform_generator: Terraform Generator
        """
        self.session_manager = session_manager or AWSSessionManager()
        self.terraform_generator = terraform_generator or TerraformGeneratorV2()

    async def deploy(
        self,
        deployment_id: str,
        architecture_json: dict,
        credential_id: str,
        org_id: str
    ) -> Dict:
        """Deployed Infrastruktur in Kunden-Account.

        Args:
            deployment_id: Deployment ID
            architecture_json: Architecture JSON
            credential_id: AWS Credential ID
            org_id: Organisation ID

        Returns:
            Deployment Result mit Outputs und Status

        Raises:
            Exception: Bei Deployment-Fehler
        """
        logger.info(f"Starte Deployment {deployment_id} in Kunden-Account")

        # 1. Get Customer AWS Session
        session = self.session_manager.get_session(credential_id)

        # 2. Verify Permissions
        self._verify_permissions(session)

        # 3. Generate Terraform
        terraform_files = self.terraform_generator.generate(architecture_json)

        # 4. Execute Terraform
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Write Terraform files
            for filename, content in terraform_files.items():
                (temp_path / filename).write_text(content)
                logger.info(f"Terraform file erstellt: {filename}")

            # Set AWS Credentials as Env Vars
            env = self._get_terraform_env(session)

            try:
                # Terraform Init
                logger.info("Terraform Init...")
                init_output = self._run_terraform_command(
                    ["terraform", "init", "-no-color"],
                    temp_path,
                    env
                )

                # Terraform Plan
                logger.info("Terraform Plan...")
                plan_output = self._run_terraform_command(
                    ["terraform", "plan", "-out=plan.tfplan", "-no-color"],
                    temp_path,
                    env
                )

                # Terraform Apply
                logger.info("Terraform Apply...")
                apply_output = self._run_terraform_command(
                    ["terraform", "apply", "-auto-approve", "plan.tfplan", "-no-color"],
                    temp_path,
                    env
                )

                # Get Terraform Outputs
                outputs = self._get_terraform_outputs(temp_path, env)

                logger.info(f"Terraform erfolgreich deployed: {deployment_id}")

            except Exception as e:
                logger.error(f"Terraform Deployment fehlgeschlagen: {e}")
                raise

        # 5. Copy User Data (OverCloud S3 → Customer ECR/S3)
        await self._copy_user_data(
            session=session,
            org_id=org_id,
            deployment_id=deployment_id,
            terraform_outputs=outputs
        )

        return {
            "status": "deployed",
            "outputs": outputs,
            "plan_summary": self._extract_plan_summary(plan_output),
            "apply_summary": apply_output
        }

    def _verify_permissions(self, session: boto3.Session):
        """Verifiziert notwendige AWS Permissions.

        Args:
            session: boto3 Session

        Raises:
            Exception: Bei fehlenden Permissions
        """
        logger.info("Verifiziere AWS Permissions...")

        # Test EC2 Access
        if not self.session_manager.test_permissions(session, "ec2"):
            raise Exception("Fehlende EC2 Permissions")

        # Test S3 Access
        if not self.session_manager.test_permissions(session, "s3"):
            raise Exception("Fehlende S3 Permissions")

        logger.info("Permissions OK")

    def _get_terraform_env(self, session: boto3.Session) -> dict:
        """Erstellt Environment Variables für Terraform.

        Args:
            session: boto3 Session

        Returns:
            Dict mit AWS Credentials
        """
        credentials = session.get_credentials()

        env = {
            "AWS_ACCESS_KEY_ID": credentials.access_key,
            "AWS_SECRET_ACCESS_KEY": credentials.secret_key,
            "AWS_DEFAULT_REGION": session.region_name
        }

        # Session Token (bei AssumeRole)
        if credentials.token:
            env["AWS_SESSION_TOKEN"] = credentials.token

        return env

    def _run_terraform_command(
        self,
        cmd: list,
        cwd: Path,
        env: dict
    ) -> str:
        """Führt Terraform Command aus.

        Args:
            cmd: Command List (z.B. ["terraform", "init"])
            cwd: Working Directory
            env: Environment Variables

        Returns:
            Command Output

        Raises:
            Exception: Bei Command-Fehler
        """
        logger.info(f"Führe aus: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            cwd=str(cwd),
            env=env,
            capture_output=True,
            text=True,
            timeout=settings.TERRAFORM_TIMEOUT
        )

        if result.returncode != 0:
            logger.error(f"Terraform Command fehlgeschlagen:\n{result.stderr}")
            raise Exception(f"Terraform failed: {result.stderr}")

        return result.stdout

    def _get_terraform_outputs(self, cwd: Path, env: dict) -> dict:
        """Extrahiert Terraform Outputs.

        Args:
            cwd: Working Directory
            env: Environment Variables

        Returns:
            Dict mit Terraform Outputs
        """
        try:
            result = subprocess.run(
                ["terraform", "output", "-json", "-no-color"],
                cwd=str(cwd),
                env=env,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                logger.warning("Keine Terraform Outputs gefunden")
                return {}

            outputs = json.loads(result.stdout)
            logger.info(f"Terraform Outputs: {list(outputs.keys())}")

            return outputs

        except Exception as e:
            logger.error(f"Fehler beim Extrahieren der Outputs: {e}")
            return {}

    def _extract_plan_summary(self, plan_output: str) -> dict:
        """Extrahiert Summary aus Terraform Plan Output.

        Args:
            plan_output: Terraform Plan Output

        Returns:
            Dict mit Summary (to_add, to_change, to_destroy)
        """
        # Parse Plan Output (simplified)
        lines = plan_output.split('\n')
        summary = {
            "to_add": 0,
            "to_change": 0,
            "to_destroy": 0
        }

        for line in lines:
            if "Plan:" in line:
                # Format: "Plan: 5 to add, 2 to change, 1 to destroy."
                parts = line.split(',')
                for part in parts:
                    if "to add" in part:
                        summary["to_add"] = int(part.split()[0])
                    elif "to change" in part:
                        summary["to_change"] = int(part.split()[0])
                    elif "to destroy" in part:
                        summary["to_destroy"] = int(part.split()[0])

        return summary

    async def _copy_user_data(
        self,
        session: boto3.Session,
        org_id: str,
        deployment_id: str,
        terraform_outputs: dict
    ):
        """Kopiert User-Daten von OverCloud S3 zu Customer ECR/S3.

        Args:
            session: Customer AWS Session
            org_id: Organisation ID
            deployment_id: Deployment ID
            terraform_outputs: Terraform Outputs
        """
        logger.info("Kopiere User-Daten zu Kunden-Account...")

        # Get OverCloud S3 Client
        overcloud_s3 = boto3.client('s3', region_name=settings.AWS_REGION)

        # Get Customer Clients
        customer_s3 = session.client('s3')
        customer_ecr = session.client('ecr')

        # 1. Copy Docker Images to ECR
        ecr_repo_url = terraform_outputs.get("ecr_repository_url", {}).get("value")
        if ecr_repo_url:
            await self._copy_docker_to_ecr(
                overcloud_s3=overcloud_s3,
                customer_ecr=customer_ecr,
                org_id=org_id,
                deployment_id=deployment_id,
                ecr_repo_url=ecr_repo_url
            )

        # 2. Copy Static Files to Customer S3
        customer_bucket = terraform_outputs.get("deployment_bucket_name", {}).get("value")
        if customer_bucket:
            await self._copy_static_files(
                overcloud_s3=overcloud_s3,
                customer_s3=customer_s3,
                org_id=org_id,
                deployment_id=deployment_id,
                customer_bucket=customer_bucket
            )

        logger.info("User-Daten erfolgreich kopiert")

    async def _copy_docker_to_ecr(
        self,
        overcloud_s3,
        customer_ecr,
        org_id: str,
        deployment_id: str,
        ecr_repo_url: str
    ):
        """Kopiert Docker Images von S3 zu ECR.

        Args:
            overcloud_s3: OverCloud S3 Client
            customer_ecr: Customer ECR Client
            org_id: Organisation ID
            deployment_id: Deployment ID
            ecr_repo_url: ECR Repository URL
        """
        logger.info(f"Kopiere Docker Images zu ECR: {ecr_repo_url}")

        # List Docker Images in S3
        prefix = f"{org_id}/{deployment_id}/docker-images/"
        response = overcloud_s3.list_objects_v2(
            Bucket=settings.S3_LARGE_ITEMS_BUCKET,
            Prefix=prefix
        )

        for obj in response.get('Contents', []):
            s3_key = obj['Key']
            logger.info(f"Verarbeite Docker Image: {s3_key}")

            # TODO: Implement Docker Image Copy
            # 1. Download from S3 to /tmp
            # 2. docker load -i /tmp/image.tar.gz
            # 3. docker tag image {ecr_repo_url}:tag
            # 4. docker push {ecr_repo_url}:tag
            # 5. Cleanup /tmp

            # Placeholder
            logger.warning("Docker Image Copy noch nicht implementiert")

    async def _copy_static_files(
        self,
        overcloud_s3,
        customer_s3,
        org_id: str,
        deployment_id: str,
        customer_bucket: str
    ):
        """Kopiert Static Files von OverCloud S3 zu Customer S3.

        Args:
            overcloud_s3: OverCloud S3 Client
            customer_s3: Customer S3 Client
            org_id: Organisation ID
            deployment_id: Deployment ID
            customer_bucket: Customer Bucket Name
        """
        logger.info(f"Kopiere Static Files zu S3: {customer_bucket}")

        # List Files in S3
        prefix = f"{org_id}/{deployment_id}/static-files/"
        response = overcloud_s3.list_objects_v2(
            Bucket=settings.S3_LARGE_ITEMS_BUCKET,
            Prefix=prefix
        )

        for obj in response.get('Contents', []):
            source_key = obj['Key']
            dest_key = source_key.replace(prefix, '')

            logger.info(f"Kopiere: {source_key} → {dest_key}")

            # Copy Object
            copy_source = {
                'Bucket': settings.S3_LARGE_ITEMS_BUCKET,
                'Key': source_key
            }

            customer_s3.copy_object(
                CopySource=copy_source,
                Bucket=customer_bucket,
                Key=dest_key
            )

        logger.info(f"Static Files kopiert: {customer_bucket}")

    async def destroy(
        self,
        deployment_id: str,
        credential_id: str,
        terraform_state_file: str
    ) -> Dict:
        """Zerstört Deployment via Terraform Destroy.

        Args:
            deployment_id: Deployment ID
            credential_id: AWS Credential ID
            terraform_state_file: Terraform State (aus DB/S3)

        Returns:
            Destroy Result
        """
        logger.info(f"Starte Terraform Destroy für {deployment_id}")

        # Get Customer AWS Session
        session = self.session_manager.get_session(credential_id)

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Restore Terraform State
            state_file = temp_path / "terraform.tfstate"
            state_file.write_text(terraform_state_file)

            # Set AWS Credentials
            env = self._get_terraform_env(session)

            try:
                # Terraform Destroy
                logger.info("Terraform Destroy...")
                destroy_output = self._run_terraform_command(
                    ["terraform", "destroy", "-auto-approve", "-no-color"],
                    temp_path,
                    env
                )

                logger.info(f"Terraform Destroy erfolgreich: {deployment_id}")

                return {
                    "status": "destroyed",
                    "output": destroy_output
                }

            except Exception as e:
                logger.error(f"Terraform Destroy fehlgeschlagen: {e}")
                raise
