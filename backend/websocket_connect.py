"""WebSocket $connect Handler.

Wird aufgerufen wenn Client eine WebSocket Connection aufbaut.
Speichert Connection ID in DynamoDB für spätere Message Routing.
"""

import json
import logging
import os
from datetime import datetime, timezone

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
    """Lambda Handler für WebSocket $connect.

    Args:
        event: API Gateway WebSocket Event
        context: Lambda Context

    Returns:
        Response dict mit statusCode
    """
    connection_id = event['requestContext']['connectionId']
    domain_name = event['requestContext']['domainName']
    stage = event['requestContext']['stage']

    logger.info(f"WebSocket $connect: {connection_id}")

    try:
        # Extract Query Parameters (optional: deployment_id)
        query_params = event.get('queryStringParameters', {}) or {}
        deployment_id = query_params.get('deployment_id')

        # Speichere Connection in DynamoDB
        now = datetime.now(timezone.utc).isoformat()

        item = {
            'pk': f'WSCONN#{connection_id}',
            'sk': 'METADATA',
            'connection_id': connection_id,
            'connected_at': now,
            'deployment_id': deployment_id if deployment_id else None,
            'domain_name': domain_name,
            'stage': stage,
            'ttl': int(datetime.now(timezone.utc).timestamp()) + 7200,  # 2 hours TTL
        }

        table.put_item(Item=item)

        logger.info(f"Connection {connection_id} saved to DynamoDB")

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Connected'})
        }

    except ClientError as e:
        logger.error(f"DynamoDB error: {e}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Failed to save connection'})
        }
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }
