"""Tests für WebSocket Support.

Testet WebSocket Connections und Real-time Updates.
"""

import pytest
from uuid import uuid4
from unittest.mock import Mock, AsyncMock, patch

from app.services.websocket_manager import WebSocketManager


class TestWebSocketManager:
    """Tests für WebSocketManager."""

    def test_create_manager_singleton(self):
        """Test: WebSocketManager ist Singleton."""
        manager1 = WebSocketManager()
        manager2 = WebSocketManager()

        assert manager1 is manager2

    @pytest.mark.asyncio
    async def test_connect_websocket(self):
        """Test: WebSocket verbinden."""
        manager = WebSocketManager()
        deployment_id = uuid4()

        # Mock WebSocket
        websocket = AsyncMock()

        await manager.connect(deployment_id, websocket)

        # Verify websocket accepted
        websocket.accept.assert_called_once()

        # Verify registered
        assert deployment_id in manager.connections
        assert websocket in manager.connections[deployment_id]

        # Cleanup
        manager.disconnect(deployment_id, websocket)

    def test_disconnect_websocket(self):
        """Test: WebSocket trennen."""
        manager = WebSocketManager()
        deployment_id = uuid4()

        websocket = Mock()
        manager.connections[deployment_id] = {websocket}

        manager.disconnect(deployment_id, websocket)

        # Verify removed
        assert deployment_id not in manager.connections

    @pytest.mark.asyncio
    async def test_send_personal_message(self):
        """Test: Nachricht an einzelne WebSocket senden."""
        manager = WebSocketManager()

        websocket = AsyncMock()
        message = {"type": "test", "data": "hello"}

        await manager.send_personal_message(websocket, message)

        websocket.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_broadcast_to_deployment(self):
        """Test: Broadcast an alle Connections eines Deployments."""
        manager = WebSocketManager()
        deployment_id = uuid4()

        # Mock multiple websockets
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        manager.connections[deployment_id] = {ws1, ws2}

        message = {"type": "update", "status": "success"}

        await manager.broadcast_to_deployment(deployment_id, message)

        # Verify both received message
        ws1.send_json.assert_called_once_with(message)
        ws2.send_json.assert_called_once_with(message)

        # Cleanup
        manager.connections.clear()

    @pytest.mark.asyncio
    async def test_broadcast_handles_disconnected_websocket(self):
        """Test: Broadcast entfernt disconnected WebSockets."""
        manager = WebSocketManager()
        deployment_id = uuid4()

        # One working, one broken websocket
        ws_working = AsyncMock()
        ws_broken = AsyncMock()
        ws_broken.send_json.side_effect = Exception("Connection lost")

        manager.connections[deployment_id] = {ws_working, ws_broken}

        await manager.broadcast_to_deployment(deployment_id, {"test": "msg"})

        # Broken websocket should be removed
        assert ws_broken not in manager.connections[deployment_id]
        assert ws_working in manager.connections[deployment_id]

        # Cleanup
        manager.connections.clear()

    @pytest.mark.asyncio
    async def test_send_status_update(self):
        """Test: Status Update senden."""
        manager = WebSocketManager()
        deployment_id = uuid4()

        websocket = AsyncMock()
        manager.connections[deployment_id] = {websocket}

        await manager.send_status_update(
            deployment_id=deployment_id,
            status="APPLYING",
            progress_percentage=60,
            current_step="Applying infrastructure",
            elapsed_seconds=45.5,
            estimated_remaining_seconds=30.0
        )

        # Verify message sent
        websocket.send_json.assert_called_once()
        call_args = websocket.send_json.call_args[0][0]

        assert call_args["type"] == "status_update"
        assert call_args["status"] == "APPLYING"
        assert call_args["progress_percentage"] == 60
        assert call_args["current_step"] == "Applying infrastructure"
        assert call_args["elapsed_seconds"] == 45.5
        assert call_args["estimated_remaining_seconds"] == 30.0

        # Cleanup
        manager.connections.clear()

    def test_get_connection_count_specific_deployment(self):
        """Test: Connection Count für spezifisches Deployment."""
        manager = WebSocketManager()
        deployment_id = uuid4()

        ws1 = Mock()
        ws2 = Mock()
        manager.connections[deployment_id] = {ws1, ws2}

        count = manager.get_connection_count(deployment_id)
        assert count == 2

        # Cleanup
        manager.connections.clear()

    def test_get_connection_count_total(self):
        """Test: Total Connection Count."""
        manager = WebSocketManager()

        dep1 = uuid4()
        dep2 = uuid4()

        manager.connections[dep1] = {Mock(), Mock()}
        manager.connections[dep2] = {Mock()}

        total_count = manager.get_connection_count()
        assert total_count == 3

        # Cleanup
        manager.connections.clear()

    def test_get_active_deployments(self):
        """Test: Liste aktiver Deployments."""
        manager = WebSocketManager()

        dep1 = uuid4()
        dep2 = uuid4()

        manager.connections[dep1] = {Mock()}
        manager.connections[dep2] = {Mock()}

        active = manager.get_active_deployments()

        assert len(active) == 2
        assert dep1 in active
        assert dep2 in active

        # Cleanup
        manager.connections.clear()

    @pytest.mark.asyncio
    async def test_broadcast_to_nonexistent_deployment(self):
        """Test: Broadcast an nicht-existentes Deployment."""
        manager = WebSocketManager()
        deployment_id = uuid4()

        # Should not raise exception
        await manager.broadcast_to_deployment(deployment_id, {"test": "msg"})
