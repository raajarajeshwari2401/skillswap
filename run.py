"""Main development entry point for SkillSwap.
Starts Flask with real-time Socket.IO and boots background Raw TCP Server.
"""

import os
from app import create_app
from app.extensions import socketio, db
from app.sockets.raw_tcp_server import RawSkillSwapTCPServer

env = os.environ.get("FLASK_ENV", "development")
app = create_app(env)

# Initialize Raw TCP Server in background thread for academic demonstration
tcp_host = app.config.get("RAW_SOCKET_HOST", "127.0.0.1")
tcp_port = app.config.get("RAW_SOCKET_PORT", 9099)
tcp_server = RawSkillSwapTCPServer(host=tcp_host, port=tcp_port)

if __name__ == "__main__":
    with app.app_context():
        # Ensure database tables exist locally
        db.create_all()

    print(f"[*] Starting Raw TCP Socket Server on {tcp_host}:{tcp_port}...")
    tcp_server.start(in_background=True)

    print("[*] Starting SkillSwap Web Application on http://127.0.0.1:5000...")
    socketio.run(
        app,
        host="127.0.0.1",
        port=5000,
        debug=True,
        use_reloader=False,  # Set False so background TCP thread is not spawned twice
    )
