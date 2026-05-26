"""WebSocket $default Message Handler.

Handelt alle WebSocket Messages (ping, get_status, etc.).
Verwendet API Gateway Management API zum Senden von Messages zurück.
"""

import json
import logging
import os
from uuid import UUID

import boto3
from botocore.exceptions import ClientError

# Logger konfigurieren
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# AWS Clients
dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('DYNAMODB_TABLE_NAME', 'overcloud-dev-main')
table = dynamodb.Table(table_name)


def handler(event, context):
    """Lambda Handler für WebSocket $default (messages).

    Args:
        event: API Gateway WebSocket Event
        context: Lambda Context

    Returns:
        Response dict mit statusCode
    """
    connection_id = event['requestContext']['connectionId']
    domain_name = event['requestContext']['domainName']
    stage = event['requestContext']['stage']

    # API Gateway Management API Client (für postToConnection)
    endpoint_url = f"https://{domain_name}/{stage}"
    apigw_management = boto3.client('apigatewaymanagementapi', endpoint_url=endpoint_url)

    logger.info(f"WebSocket message from {connection_id}")

    try:
        # Parse Message Body
        body = event.get('body', '{}')
        if isinstance(body, str):
            message = json.loads(body)
        else:
            message = body

        action = message.get('action', 'unknown')

        logger.info(f"Action: {action}")

        # Handle Actions
        if action == 'ping':
            # Pong zurücksenden (Keep-Alive)
            response = {
                'type': 'pong',
                'connection_id': connection_id
            }
            apigw_management.post_to_connection(
                ConnectionId=connection_id,
                Data=json.dumps(response).encode('utf-8')
            )

            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'Pong sent'})
            }

        elif action == 'get_status':
            # Deployment Status abrufen und zurücksenden
            deployment_id = message.get('deployment_id')

            if not deployment_id:
                raise ValueError("deployment_id required for get_status")

            # Deployment aus DynamoDB holen
            from app.repositories.deployment import DeploymentRepository
            from app.services.deployment_progress import get_progress_info

            repo = DeploymentRepository()
            deployment = repo.get(UUID(deployment_id))

            if not deployment:
                raise ValueError(f"Deployment {deployment_id} not found")

            # Progress Info berechnen
            progress_info = get_progress_info(deployment)

            # Status Update senden
            response = {
                'type': 'status_update',
                'deployment_id': deployment_id,
                'status': deployment['status'],
                **progress_info
            }

            apigw_management.post_to_connection(
                ConnectionId=connection_id,
                Data=json.dumps(response).encode('utf-8')
            )

            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'Status sent'})
            }

        else:
            # Unknown action
            logger.warning(f"Unknown action: {action}")
            response = {
                'type': 'error',
                'error': f"Unknown action: {action}"
            }
            apigw_management.post_to_connection(
                ConnectionId=connection_id,
                Data=json.dumps(response).encode('utf-8')
            )

            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Unknown action'})
            }

    except ClientError as e:
        error_code = e.response['Error']['Code']

        if error_code == 'GoneException':
            # Connection nicht mehr aktiv - aus DynamoDB löschen
            logger.warning(f"Connection {connection_id} is gone")
            try:
                table.delete_item(
                    Key={
                        'pk': f'WSCONN#{connection_id}',
                        'sk': 'METADATA'
                    }
                )
            except Exception:
                pass

        logger.error(f"AWS error: {e}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)

        # Try sending error to client
        try:
            response = {
                'type': 'error',
                'error': str(e)
            }
            apigw_management.post_to_connection(
                ConnectionId=connection_id,
                Data=json.dumps(response).encode('utf-8')
            )
        except Exception:
            pass

        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }
