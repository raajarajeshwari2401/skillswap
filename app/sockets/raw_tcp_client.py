"""Demonstrable Raw Python TCP Client Module.
Academic Concept: Socket Programming client communicating with the Raw TCP Server.
Handles connection setup, JSON line encoding, response parsing, and error recovery.
"""

import socket
import json
from typing import Dict, Any, Optional


class RawSkillSwapTCPClient:
    """Client for communicating with the RawSkillSwapTCPServer."""

    def __init__(self, host: str = "127.0.0.1", port: int = 9099, timeout: float = 3.0):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.sock: Optional[socket.socket] = None

    def connect(self) -> None:
        """Establish TCP connection to the server."""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        self.sock.connect((self.host, self.port))

    def send_command(self, command: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send a JSON command string and return parsed JSON response."""
        if not self.sock:
            raise ConnectionError("Socket not connected. Call connect() first.")

        request = {
            "command": command.upper(),
            "payload": payload or {},
        }
        raw_message = (json.dumps(request) + "\n").encode("utf-8")
        self.sock.sendall(raw_message)

        # Read response line
        buffer = ""
        while "\n" not in buffer:
            chunk = self.sock.recv(2048)
            if not chunk:
                raise ConnectionError("Server closed connection unexpectedly.")
            buffer += chunk.decode("utf-8")

        line, _ = buffer.split("\n", 1)
        return json.loads(line)

    def ping(self) -> Dict[str, Any]:
        """Send PING command."""
        return self.send_command("PING")

    def authenticate(self, token: str) -> Dict[str, Any]:
        """Authenticate with server token."""
        return self.send_command("AUTH", {"token": token})

    def get_stats(self) -> Dict[str, Any]:
        """Request node statistics."""
        return self.send_command("STATS")

    def echo(self, data: Any) -> Dict[str, Any]:
        """Send payload to be echoed back."""
        return self.send_command("ECHO", {"data": data})

    def close(self) -> None:
        """Send QUIT and cleanly close socket connection."""
        if self.sock:
            try:
                self.send_command("QUIT")
            except Exception:
                pass
            finally:
                self.sock.close()
                self.sock = None


if __name__ == "__main__":
    client = RawSkillSwapTCPClient(port=9099)
    try:
        print("Connecting to Raw TCP Server on 127.0.0.1:9099...")
        client.connect()
        print("Ping response:", client.ping())
        print("Auth response:", client.authenticate("skillswap-secret-token"))
        print("Stats response:", client.get_stats())
        print("Echo response:", client.echo({"message": "Hello from SkillSwap Client"}))
    finally:
        client.close()
        print("Connection closed cleanly.")
