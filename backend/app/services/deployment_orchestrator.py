"""Deployment Orchestrator Service.

Orchestriert Deployments zwischen Lambda (schnell) und ECS (lang).

Entscheidungslogik:
- Geschätzte Dauer < 10 Min → Lambda (inline)
- Geschätzte Dauer > 10 Min → ECS Fargate Spot Task (async)

ECS Tasks werden on-demand via boto3 ecs.run_task() gestartet.
"""

import json
import logging
import os
from typing import Any
from uuid import UUID

import boto3
from botocore.exceptions import ClientError

from app.repositories.deployment import DeploymentRepository

logger = logging.getLogger(__name__)


class DeploymentOrchestrator:
    """Orchestriert Deployments zwischen Lambda und ECS."""

    def __init__(self):
        """Initialisiert Orchestrator mit AWS Clients."""
        self.ecs = boto3.client('ecs')
        self.deployment_repo = DeploymentRepository()

        # ECS Configuration (aus Environment Variables)
        self.ecs_cluster_name = os.environ.get('ECS_CLUSTER_NAME', '')
        self.ecs_task_definition = os.environ.get('ECS_TASK_DEFINITION', '')
        self.ecs_subnets = os.environ.get('ECS_SUBNETS', '').split(',')
        self.ecs_security_group = os.environ.get('ECS_SECURITY_GROUP', '')
        self.websocket_api_endpoint = os.environ.get('WEBSOCKET_API_ENDPOINT', '')

        # Validierung
        if not all([
            self.ecs_cluster_name,
            self.ecs_task_definition,
            self.ecs_subnets,
            self.ecs_security_group
        ]):
            logger.warning(
                "ECS Configuration incomplete - ECS deployments will fail. "
                "Set ECS_CLUSTER_NAME, ECS_TASK_DEFINITION, ECS_SUBNETS, ECS_SECURITY_GROUP"
            )

    async def start_deployment(
        self,
        deployment_id: str,
        architecture: dict[str, Any],
        user_id: str,
        credential_id: str
    ) -> dict[str, Any]:
        """Startet Deployment (Lambda oder ECS basierend auf geschätzter Dauer).

        Args:
            deployment_id: Deployment ID
            architecture: Architecture JSON
            user_id: User ID
            credential_id: AWS Credential ID

        Returns:
            Deployment Info dict mit status, worker, task_arn (wenn ECS)

        Raises:
            Exception: Bei Fehler
        """
        logger.info(f"Starting deployment {deployment_id}")

        # Schätze Deployment-Dauer
        estimated_duration = self._estimate_duration(architecture)

        logger.info(
            f"Deployment {deployment_id}: estimated duration {estimated_duration}s "
            f"({estimated_duration / 60:.1f} min)"
        )

        # Entscheide: Lambda oder ECS?
        if estimated_duration < 600:  # < 10 Min
            # Lambda kann das handlen (inline execution)
            logger.info(f"Deployment {deployment_id}: using Lambda (fast)")
            return await self._run_in_lambda(deployment_id, architecture, user_id, credential_id)
        else:
            # ECS Task für lange Deployments (async execution)
            logger.info(f"Deployment {deployment_id}: using ECS (slow)")
            return await self._run_in_ecs(deployment_id, architecture, user_id, credential_id)

    async def _run_in_lambda(
        self,
        deployment_id: str,
        architecture: dict[str, Any],
        user_id: str,
        credential_id: str
    ) -> dict[str, Any]:
        """Führt Deployment inline in Lambda aus (für schnelle Deployments).

        Args:
            deployment_id: Deployment ID
            architecture: Architecture JSON
            user_id: User ID
            credential_id: AWS Credential ID

        Returns:
            Deployment Result

        Raises:
            Exception: Bei Fehler
        """
        logger.info(f"Running deployment {deployment_id} in Lambda")

        # Import hier um circular dependency zu vermeiden
        from app.services.deployment_executor import DeploymentExecutor

        try:
            # Update Status: in_progress
            self.deployment_repo.update_status(
                deployment_id=UUID(deployment_id),
                status='in_progress',
                error_message=None
            )

            # Execute Deployment
            executor = DeploymentExecutor()
            result = await executor.deploy(
                deployment_id=deployment_id,
                architecture_json=architecture,
                credential_id=credential_id,
                org_id=user_id  # TODO: use actual org_id
            )

            # Update Status: completed
            self.deployment_repo.update_status(
                deployment_id=UUID(deployment_id),
                status='completed',
                error_message=None
            )

            return {
                'deployment_id': deployment_id,
                'status': 'completed',
                'worker': 'lambda',
                'result': result
            }

        except Exception as e:
            logger.error(f"Lambda deployment {deployment_id} failed: {e}", exc_info=True)

            # Update Status: failed
            self.deployment_repo.update_status(
                deployment_id=UUID(deployment_id),
                status='failed',
                error_message=str(e)
            )

            raise

    async def _run_in_ecs(
        self,
        deployment_id: str,
        architecture: dict[str, Any],
        user_id: str,
        credential_id: str
    ) -> dict[str, Any]:
        """Startet ECS Fargate Spot Task on-demand für lange Deployments.

        Args:
            deployment_id: Deployment ID
            architecture: Architecture JSON
            user_id: User ID
            credential_id: AWS Credential ID

        Returns:
            Deployment Info mit task_arn

        Raises:
            Exception: Bei Fehler
        """
        logger.info(f"Starting ECS task for deployment {deployment_id}")

        try:
            # Update Status: queued
            self.deployment_repo.update_status(
                deployment_id=UUID(deployment_id),
                status='queued',
                error_message=None
            )

            # ECS Task starten
            response = self.ecs.run_task(
                cluster=self.ecs_cluster_name,
                taskDefinition=self.ecs_task_definition,
                launchType='FARGATE',

                # Fargate Spot (70% günstiger!)
                capacityProviderStrategy=[
                    {
                        'capacityProvider': 'FARGATE_SPOT',
                        'weight': 100,
                        'base': 0
                    }
                ],

                # Network Configuration
                networkConfiguration={
                    'awsvpcConfiguration': {
                        'subnets': self.ecs_subnets,
                        'securityGroups': [self.ecs_security_group],
                        'assignPublicIp': 'ENABLED'  # Benötigt für AWS API Calls
                    }
                },

                # Environment Variables (runtime injection)
                overrides={
                    'containerOverrides': [
                        {
                            'name': 'deployment-worker',
                            'environment': [
                                {'name': 'DEPLOYMENT_ID', 'value': deployment_id},
                                {
                                    'name': 'ARCHITECTURE_JSON',
                                    'value': json.dumps(architecture)
                                },
                                {'name': 'USER_ID', 'value': user_id},
                                {'name': 'CREDENTIAL_ID', 'value': credential_id},
                                {
                                    'name': 'WEBSOCKET_API_ENDPOINT',
                                    'value': self.websocket_api_endpoint
                                },
                            ]
                        }
                    ]
                }
            )

            # Extract Task ARN
            if not response.get('tasks'):
                raise RuntimeError("ECS run_task returned no tasks")

            task_arn = response['tasks'][0]['taskArn']

            logger.info(f"ECS Task started: {task_arn}")

            # Task ARN in DynamoDB speichern
            await self._save_task_info(deployment_id, task_arn)

            return {
                'deployment_id': deployment_id,
                'status': 'queued',
                'worker': 'ecs',
                'task_arn': task_arn
            }

        except ClientError as e:
            logger.error(f"ECS task start failed: {e}", exc_info=True)

            # Update Status: failed
            self.deployment_repo.update_status(
                deployment_id=UUID(deployment_id),
                status='failed',
                error_message=f"ECS task start failed: {str(e)}"
            )

            raise

    async def _save_task_info(self, deployment_id: str, task_arn: str) -> None:
        """Speichert ECS Task Info in DynamoDB.

        Args:
            deployment_id: Deployment ID
            task_arn: ECS Task ARN
        """
        try:
            # Update Deployment mit task_arn
            deployment = self.deployment_repo.get(UUID(deployment_id))

            if deployment:
                deployment['ecs_task_arn'] = task_arn
                self.deployment_repo.update(UUID(deployment_id), deployment)

                logger.info(f"Saved task_arn {task_arn} for deployment {deployment_id}")

        except Exception as e:
            logger.error(f"Failed to save task_arn: {e}", exc_info=True)
            # Non-critical error - don't fail deployment

    def _estimate_duration(self, architecture: dict[str, Any]) -> int:
        """Schätzt Deployment-Dauer in Sekunden basierend auf Komponenten.

        Heuristik:
        - VPC: +3 Min
        - RDS: +10 Min
        - ALB/ELB: +5 Min
        - Lambda/S3: +1 Min
        - Base: 2 Min

        Args:
            architecture: Architecture JSON

        Returns:
            Geschätzte Dauer in Sekunden
        """
        components = architecture.get('components', [])

        duration = 120  # Base: 2 Min

        for component in components:
            comp_type = component.get('type', '').lower()

            if 'rds' in comp_type or 'database' in comp_type:
                duration += 600  # RDS: +10 Min
            elif 'alb' in comp_type or 'elb' in comp_type or 'loadbalancer' in comp_type:
                duration += 300  # ALB: +5 Min
            elif 'vpc' in comp_type or 'network' in comp_type:
                duration += 180  # VPC: +3 Min
            elif 'ecs' in comp_type or 'cluster' in comp_type:
                duration += 240  # ECS: +4 Min
            elif 'lambda' in comp_type or 's3' in comp_type:
                duration += 60   # Simple: +1 Min
            else:
                duration += 30   # Unknown: +30s

        logger.info(f"Estimated duration: {duration}s for {len(components)} components")

        return duration
