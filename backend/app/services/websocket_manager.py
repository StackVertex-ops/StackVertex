"""WebSocket Manager.

Verwaltet WebSocket Connections für Real-time Deployment Updates.
"""

import logging
import json
from typing import Dict, Set
from uuid import UUID

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections for deployment updates."""

    _instance = None

    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize WebSocket manager."""
        if not hasattr(self, 'connections'):
            # deployment_id -> set of WebSocket connections
            self.connections: Dict[UUID, Set[WebSocket]] = {}
            logger.info("WebSocketManager initialized")

    async def connect(self, deployment_id: UUID, websocket: WebSocket):
        """Register new WebSocket connection.

        Args:
            deployment_id: Deployment ID to subscribe to
            websocket: WebSocket connection
        """
        await websocket.accept()

        if deployment_id not in self.connections:
            self.connections[deployment_id] = set()

        self.connections[deployment_id].add(websocket)
        logger.info(f"WebSocket connected for deployment {deployment_id}")

        # Send initial connection message
        await self.send_personal_message(
            websocket,
            {
                "type": "connected",
                "deployment_id": str(deployment_id),
                "message": "WebSocket connection established"
            }
        )

    def disconnect(self, deployment_id: UUID, websocket: WebSocket):
        """Unregister WebSocket connection.

        Args:
            deployment_id: Deployment ID
            websocket: WebSocket connection
        """
        if deployment_id in self.connections:
            self.connections[deployment_id].discard(websocket)

            # Cleanup empty sets
            if not self.connections[deployment_id]:
                del self.connections[deployment_id]

            logger.info(f"WebSocket disconnected for deployment {deployment_id}")

    async def send_personal_message(self, websocket: WebSocket, message: dict):
        """Send message to specific WebSocket.

        Args:
            websocket: WebSocket connection
            message: Message dict (will be JSON serialized)
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send WebSocket message: {e}")

    async def broadcast_to_deployment(self, deployment_id: UUID, message: dict):
        """Broadcast message to all connections for a deployment.

        Args:
            deployment_id: Deployment ID
            message: Message dict (will be JSON serialized)
        """
        if deployment_id not in self.connections:
            logger.debug(f"No WebSocket connections for deployment {deployment_id}")
            return

        # Copy set to avoid modification during iteration
        connections = self.connections[deployment_id].copy()

        disconnected = []
        for websocket in connections:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send to WebSocket: {e}")
                disconnected.append(websocket)

        # Clean up disconnected websockets
        for websocket in disconnected:
            self.disconnect(deployment_id, websocket)

    async def send_status_update(
        self,
        deployment_id: UUID,
        status: str,
        progress_percentage: int,
        current_step: str,
        elapsed_seconds: float,
        estimated_remaining_seconds: float = None,
        error_message: str = None
    ):
        """Send deployment status update.

        Args:
            deployment_id: Deployment ID
            status: Deployment status
            progress_percentage: Progress percentage (0-100)
            current_step: Current step description
            elapsed_seconds: Elapsed time in seconds
            estimated_remaining_seconds: Estimated remaining time
            error_message: Error message if failed
        """
        message = {
            "type": "status_update",
            "deployment_id": str(deployment_id),
            "status": status,
            "progress_percentage": progress_percentage,
            "current_step": current_step,
            "elapsed_seconds": round(elapsed_seconds, 2),
        }

        if estimated_remaining_seconds is not None:
            message["estimated_remaining_seconds"] = round(estimated_remaining_seconds, 2)

        if error_message:
            message["error_message"] = error_message

        await self.broadcast_to_deployment(deployment_id, message)

    def get_connection_count(self, deployment_id: UUID = None) -> int:
        """Get number of active connections.

        Args:
            deployment_id: Specific deployment ID, or None for total

        Returns:
            Number of connections
        """
        if deployment_id:
            return len(self.connections.get(deployment_id, set()))
        else:
            return sum(len(conns) for conns in self.connections.values())

    def get_active_deployments(self) -> list[UUID]:
        """Get list of deployment IDs with active WebSocket connections.

        Returns:
            List of deployment IDs
        """
        return list(self.connections.keys())


# Global singleton instance
ws_manager = WebSocketManager()
