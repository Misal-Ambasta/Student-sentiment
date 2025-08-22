import json
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from loguru import logger

router = APIRouter()

# Store active connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        if client_id not in self.active_connections:
            self.active_connections[client_id] = []
        self.active_connections[client_id].append(websocket)
        logger.info(f"Client {client_id} connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket, client_id: str):
        if client_id in self.active_connections:
            if websocket in self.active_connections[client_id]:
                self.active_connections[client_id].remove(websocket)
            if not self.active_connections[client_id]:
                del self.active_connections[client_id]
        logger.info(f"Client {client_id} disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast(self, message: Dict[str, Any], client_id: Optional[str] = None):
        if client_id:
            # Send to specific client
            if client_id in self.active_connections:
                for connection in self.active_connections[client_id]:
                    await connection.send_text(json.dumps(message))
        else:
            # Broadcast to all clients
            for client_id in self.active_connections:
                for connection in self.active_connections[client_id]:
                    await connection.send_text(json.dumps(message))

manager = ConnectionManager()

@router.websocket("/connect/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    try:
        await manager.connect(websocket, client_id)
        
        # Send welcome message
        await websocket.send_text(
            json.dumps({
                "type": "connection_established",
                "client_id": client_id,
                "message": "Connected to WebSocket server"
            })
        )
        
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                
                # Process message based on type
                if message.get("type") == "ping":
                    await websocket.send_text(
                        json.dumps({
                            "type": "pong",
                            "timestamp": message.get("timestamp")
                        })
                    )
                else:
                    # Echo message back (for testing)
                    await websocket.send_text(
                        json.dumps({
                            "type": "echo",
                            "message": message
                        })
                    )
            except json.JSONDecodeError:
                await websocket.send_text(
                    json.dumps({
                        "type": "error",
                        "message": "Invalid JSON format"
                    })
                )
    except WebSocketDisconnect:
        manager.disconnect(websocket, client_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, client_id)

# Function to broadcast file processing updates
async def broadcast_file_update(file_id: str, status: str, message: Optional[str] = None):
    """Broadcast file processing updates to all clients"""
    try:
        await manager.broadcast({
            "type": "file_update",
            "file_id": file_id,
            "status": status,
            "message": message
        })
        logger.info(f"Broadcasted file update for {file_id}: {status}")
    except Exception as e:
        logger.error(f"Error broadcasting file update: {e}")

# Function to broadcast chat updates
async def broadcast_chat_update(session_id: str, message: Dict[str, Any], client_id: Optional[str] = None):
    """Broadcast chat updates to specific client or all clients"""
    try:
        await manager.broadcast({
            "type": "chat_update",
            "session_id": session_id,
            "message": message
        }, client_id)
        logger.info(f"Broadcasted chat update for session {session_id}")
    except Exception as e:
        logger.error(f"Error broadcasting chat update: {e}")