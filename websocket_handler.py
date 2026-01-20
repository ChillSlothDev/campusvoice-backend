"""
WebSocket Connection Manager for Real-Time Updates
Handles live vote broadcasting to connected clients
"""

from typing import Dict, Set, Optional
from fastapi import WebSocket, WebSocketDisconnect
import json
import asyncio
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================
# CONNECTION MANAGER CLASS
# ============================================

class ConnectionManager:
    """
    Manages WebSocket connections and broadcasts updates
    
    Features:
    - Multiple clients per complaint
    - Auto-cleanup on disconnect
    - Broadcast to all connected clients
    - Real-time vote updates (<100ms)
    """
    
    def __init__(self):
        # Dictionary: complaint_id -> set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        
        # Track connection metadata
        self.connection_metadata: Dict[WebSocket, dict] = {}
        
        # Connection counters
        self.total_connections = 0
        self.total_disconnections = 0
    
    
    # ========================================
    # CONNECTION MANAGEMENT
    # ========================================
    
    async def connect(self, websocket: WebSocket, complaint_id: str, client_info: Optional[dict] = None):
        """
        Connect a client to a complaint's vote feed
        
        Args:
            websocket: WebSocket connection
            complaint_id: Complaint ID to subscribe to
            client_info: Optional client metadata (roll_number, etc.)
        """
        # Accept the WebSocket connection
        await websocket.accept()
        
        # Initialize set for this complaint if not exists
        if complaint_id not in self.active_connections:
            self.active_connections[complaint_id] = set()
        
        # Add connection to the set
        self.active_connections[complaint_id].add(websocket)
        
        # Store metadata
        self.connection_metadata[websocket] = {
            "complaint_id": complaint_id,
            "connected_at": datetime.utcnow().isoformat(),
            "client_info": client_info or {}
        }
        
        # Update counter
        self.total_connections += 1
        
        # Log connection
        logger.info(f"✅ Client connected to complaint {complaint_id}. Total active: {self.get_connection_count(complaint_id)}")
        
        # Send welcome message
        await self.send_personal_message(
            websocket,
            {
                "type": "connection",
                "message": "Connected to vote feed",
                "complaint_id": complaint_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    
    async def disconnect(self, websocket: WebSocket, complaint_id: str):
        """
        Disconnect a client from a complaint's vote feed
        
        Args:
            websocket: WebSocket connection
            complaint_id: Complaint ID to unsubscribe from
        """
        # Remove from active connections
        if complaint_id in self.active_connections:
            self.active_connections[complaint_id].discard(websocket)
            
            # Remove empty sets
            if not self.active_connections[complaint_id]:
                del self.active_connections[complaint_id]
        
        # Remove metadata
        if websocket in self.connection_metadata:
            del self.connection_metadata[websocket]
        
        # Update counter
        self.total_disconnections += 1
        
        # Log disconnection
        logger.info(f"❌ Client disconnected from complaint {complaint_id}. Remaining: {self.get_connection_count(complaint_id)}")
    
    
    # ========================================
    # MESSAGE SENDING
    # ========================================
    
    async def send_personal_message(self, websocket: WebSocket, message: dict):
        """
        Send message to a specific client
        
        Args:
            websocket: Target WebSocket connection
            message: Message dictionary to send
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
    
    
    async def broadcast_vote_update(self, complaint_id: str, vote_data: dict):
        """
        Broadcast vote update to all clients watching this complaint
        
        Args:
            complaint_id: Complaint ID
            vote_data: Vote update data
            
        Example vote_data:
            {
                "upvotes": 45,
                "downvotes": 3,
                "total_votes": 48,
                "action": "upvote_added",
                "timestamp": "2026-01-19T17:35:00"
            }
        """
        if complaint_id not in self.active_connections:
            logger.warning(f"No active connections for complaint {complaint_id}")
            return
        
        # Prepare broadcast message
        broadcast_message = {
            "type": "vote_update",
            "complaint_id": complaint_id,
            **vote_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Track disconnected clients
        disconnected_clients = set()
        
        # Send to all connected clients
        for websocket in self.active_connections[complaint_id]:
            try:
                await websocket.send_json(broadcast_message)
                logger.debug(f"📤 Broadcasted to client on complaint {complaint_id}")
            except WebSocketDisconnect:
                disconnected_clients.add(websocket)
                logger.warning(f"Client disconnected during broadcast")
            except Exception as e:
                disconnected_clients.add(websocket)
                logger.error(f"Error broadcasting to client: {e}")
        
        # Clean up disconnected clients
        for websocket in disconnected_clients:
            await self.disconnect(websocket, complaint_id)
        
        logger.info(f"✅ Broadcast to {len(self.active_connections[complaint_id])} clients for complaint {complaint_id}")
    
    
    async def broadcast_status_update(self, complaint_id: str, status_data: dict):
        """
        Broadcast status change to all clients watching this complaint
        
        Args:
            complaint_id: Complaint ID
            status_data: Status update data
            
        Example status_data:
            {
                "old_status": "raised",
                "new_status": "opened",
                "updated_by": "admin",
                "reason": "Complaint reviewed"
            }
        """
        if complaint_id not in self.active_connections:
            return
        
        broadcast_message = {
            "type": "status_update",
            "complaint_id": complaint_id,
            **status_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        disconnected_clients = set()
        
        for websocket in self.active_connections[complaint_id]:
            try:
                await websocket.send_json(broadcast_message)
            except Exception as e:
                disconnected_clients.add(websocket)
                logger.error(f"Error broadcasting status: {e}")
        
        for websocket in disconnected_clients:
            await self.disconnect(websocket, complaint_id)
        
        logger.info(f"✅ Status broadcast to {len(self.active_connections[complaint_id])} clients")
    
    
    async def broadcast_to_all(self, message: dict):
        """
        Broadcast message to ALL connected clients (all complaints)
        
        Args:
            message: Message to broadcast
        """
        broadcast_message = {
            "type": "global_broadcast",
            **message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        total_sent = 0
        
        for complaint_id, connections in self.active_connections.items():
            for websocket in connections:
                try:
                    await websocket.send_json(broadcast_message)
                    total_sent += 1
                except Exception as e:
                    logger.error(f"Error in global broadcast: {e}")
        
        logger.info(f"✅ Global broadcast sent to {total_sent} clients")
    
    
    # ========================================
    # STATISTICS & MONITORING
    # ========================================
    
    def get_connection_count(self, complaint_id: str) -> int:
        """
        Get number of active connections for a complaint
        
        Args:
            complaint_id: Complaint ID
            
        Returns:
            int: Number of active connections
        """
        if complaint_id not in self.active_connections:
            return 0
        return len(self.active_connections[complaint_id])
    
    
    def get_total_connections(self) -> int:
        """
        Get total number of active WebSocket connections
        
        Returns:
            int: Total active connections across all complaints
        """
        total = 0
        for connections in self.active_connections.values():
            total += len(connections)
        return total
    
    
    def get_stats(self) -> dict:
        """
        Get detailed connection statistics
        
        Returns:
            dict: Statistics dictionary
        """
        return {
            "active_complaints": len(self.active_connections),
            "total_active_connections": self.get_total_connections(),
            "total_connections_ever": self.total_connections,
            "total_disconnections": self.total_disconnections,
            "complaints_being_watched": list(self.active_connections.keys()),
            "connections_per_complaint": {
                complaint_id: len(connections)
                for complaint_id, connections in self.active_connections.items()
            }
        }
    
    
    def get_complaint_watchers(self, complaint_id: str) -> list:
        """
        Get list of clients watching a specific complaint
        
        Args:
            complaint_id: Complaint ID
            
        Returns:
            list: List of client metadata
        """
        if complaint_id not in self.active_connections:
            return []
        
        watchers = []
        for websocket in self.active_connections[complaint_id]:
            if websocket in self.connection_metadata:
                watchers.append(self.connection_metadata[websocket])
        
        return watchers
    
    
    # ========================================
    # CLEANUP
    # ========================================
    
    async def disconnect_all(self):
        """
        Disconnect all clients (use on shutdown)
        """
        logger.info("🛑 Disconnecting all WebSocket clients...")
        
        for complaint_id, connections in list(self.active_connections.items()):
            for websocket in list(connections):
                try:
                    await websocket.close(code=1000, reason="Server shutdown")
                except Exception as e:
                    logger.error(f"Error closing connection: {e}")
        
        self.active_connections.clear()
        self.connection_metadata.clear()
        
        logger.info("✅ All WebSocket connections closed")
    
    
    async def cleanup_stale_connections(self):
        """
        Remove stale/dead connections (run periodically)
        """
        logger.info("🧹 Cleaning up stale connections...")
        
        stale_count = 0
        
        for complaint_id, connections in list(self.active_connections.items()):
            disconnected = set()
            
            for websocket in list(connections):
                try:
                    # Send ping to check if alive
                    await websocket.send_json({"type": "ping"})
                except Exception:
                    disconnected.add(websocket)
                    stale_count += 1
            
            # Remove stale connections
            for websocket in disconnected:
                await self.disconnect(websocket, complaint_id)
        
        logger.info(f"✅ Cleaned up {stale_count} stale connections")


# ============================================
# GLOBAL MANAGER INSTANCE
# ============================================

# Create single global instance
manager = ConnectionManager()


# ============================================
# HELPER FUNCTIONS
# ============================================

async def send_vote_update(complaint_id: str, upvotes: int, downvotes: int, action: str):
    """
    Convenient function to send vote updates
    
    Args:
        complaint_id: Complaint ID
        upvotes: Current upvote count
        downvotes: Current downvote count
        action: Action performed (upvote_added, downvote_added, vote_removed, vote_changed)
    """
    await manager.broadcast_vote_update(
        complaint_id=complaint_id,
        vote_data={
            "upvotes": upvotes,
            "downvotes": downvotes,
            "total_votes": upvotes + downvotes,
            "action": action
        }
    )


async def send_status_update(complaint_id: str, old_status: str, new_status: str, updated_by: str = None, reason: str = None):
    """
    Convenient function to send status updates
    
    Args:
        complaint_id: Complaint ID
        old_status: Previous status
        new_status: New status
        updated_by: Who updated it
        reason: Reason for update
    """
    await manager.broadcast_status_update(
        complaint_id=complaint_id,
        status_data={
            "old_status": old_status,
            "new_status": new_status,
            "updated_by": updated_by,
            "reason": reason
        }
    )


# ============================================
# PERIODIC CLEANUP TASK
# ============================================

async def periodic_cleanup_task():
    """
    Background task to periodically clean stale connections
    Run this as a background task in FastAPI
    """
    while True:
        await asyncio.sleep(300)  # Every 5 minutes
        await manager.cleanup_stale_connections()


# ============================================
# EXPORT
# ============================================

__all__ = [
    "ConnectionManager",
    "manager",
    "send_vote_update",
    "send_status_update",
    "periodic_cleanup_task",
]
