"""Flask-SocketIO event handlers for authenticated real-time browser messaging.
"""

from flask import request
from flask_login import current_user
from flask_socketio import emit, join_room, leave_room
from app.extensions import socketio


@socketio.on("connect")
def handle_connect():
    """Authenticate incoming WebSocket connection and assign user to private notification room."""
    if current_user.is_authenticated:
        user_room = f"user_{current_user.id}"
        join_room(user_room)
        emit(
            "connection_status",
            {
                "status": "connected",
                "user_id": current_user.id,
                "room": user_room,
                "message": f"Real-time notifications active for {current_user.full_name}",
            },
        )
    else:
        # Unauthenticated guests can join public announcement channel
        join_room("public_announcements")
        emit(
            "connection_status",
            {"status": "guest", "room": "public_announcements"},
        )


@socketio.on("disconnect")
def handle_disconnect():
    """Clean up rooms upon client disconnection."""
    if current_user.is_authenticated:
        leave_room(f"user_{current_user.id}")


@socketio.on("ping_server")
def handle_ping(data):
    """Heartbeat response to test real-time socket latency."""
    emit("pong_server", {"received": data, "status": "healthy"})
