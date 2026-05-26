"""WebSocket $disconnect Handler.

Wird aufgerufen wenn Client die WebSocket Connection trennt.
Löscht Connection ID aus DynamoDB.
"""

import json
import logging
import os

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
    """Lambda Handler für WebSocket $disconnect.

    Args:
        event: API Gateway WebSocket Event
        context: Lambda Context

    Returns:
        Response dict mit statusCode
    """
    connection_id = event['requestContext']['connectionId']

    logger.info(f"WebSocket $disconnect: {connection_id}")

    try:
        # Lösche Connection aus DynamoDB
        table.delete_item(
            Key={
                'pk': f'WSCONN#{connection_id}',
                'sk': 'METADATA'
            }
        )

        logger.info(f"Connection {connection_id} deleted from DynamoDB")

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Disconnected'})
        }

    except ClientError as e:
        logger.error(f"DynamoDB error: {e}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Failed to delete connection'})
        }
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }
