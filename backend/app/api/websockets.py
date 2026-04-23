"""WebSocket API Endpoints.

Real-time Deployment Status Updates via WebSocket.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.repositories.deployment import DeploymentRepository
from app.services.websocket_manager import ws_manager
from app.services.deployment_progress import get_progress_info

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/deployments/{deployment_id}")
async def websocket_deployment_endpoint(
    websocket: WebSocket,
    deployment_id: UUID,
):
    """WebSocket Endpoint für Deployment Status Updates.

    Client verbindet sich und erhält automatisch Status-Updates.

    Protocol:
        Client → Server: { "action": "subscribe" }
        Server → Client: { "type": "status_update", "status": "...", ... }

    Args:
        websocket: WebSocket connection
        deployment_id: Deployment ID to subscribe to
    """
    await ws_manager.connect(deployment_id, websocket)

    try:
        # Send initial status
        repo = DeploymentRepository()
        item = repo.get(deployment_id)

        if item:
            progress_info = get_progress_info(item)
            await ws_manager.send_status_update(
                deployment_id=deployment_id,
                status=item["status"],
                progress_percentage=progress_info["progress_percentage"],
                current_step=progress_info["current_step"],
                elapsed_seconds=progress_info["elapsed_seconds"],
                estimated_remaining_seconds=progress_info.get("estimated_remaining_seconds"),
                error_message=item.get("error_message")
            )

        # Keep connection alive and listen for client messages
        while True:
            data = await websocket.receive_json()

            # Handle client actions
            if data.get("action") == "ping":
                await ws_manager.send_personal_message(
                    websocket,
                    {"type": "pong", "deployment_id": str(deployment_id)}
                )
            elif data.get("action") == "get_status":
                # Client requests current status
                item = repo.get(deployment_id)
                if item:
                    progress_info = get_progress_info(item)
                    await ws_manager.send_personal_message(
                        websocket,
                        {
                            "type": "status_update",
                            "deployment_id": str(deployment_id),
                            "status": item["status"],
                            **progress_info
                        }
                    )

    except WebSocketDisconnect:
        ws_manager.disconnect(deployment_id, websocket)
        logger.info(f"Client disconnected from deployment {deployment_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        ws_manager.disconnect(deployment_id, websocket)


@router.get("/ws/stats")
async def websocket_stats():
    """Get WebSocket statistics.

    Returns:
        Connection statistics
    """
    return {
        "total_connections": ws_manager.get_connection_count(),
        "active_deployments": len(ws_manager.get_active_deployments()),
        "deployment_ids": [str(d_id) for d_id in ws_manager.get_active_deployments()]
    }
