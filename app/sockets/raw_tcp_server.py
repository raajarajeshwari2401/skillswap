"""Demonstrable Raw Python TCP Server Module.
Academic Concept: Socket Programming using Python's standard `socket` and `threading` libraries.
Implements a multi-threaded server with structured JSON messaging, authentication, and timeouts.
"""

import socket
import threading
import json
import time
from typing import Optional


class RawSkillSwapTCPServer:
    """Threaded Raw TCP Server for inter-node communication and administrative queries."""

    def __init__(self, host: str = "127.0.0.1", port: int = 9099, auth_token: str = "skillswap-secret-token"):
        self.host = host
        self.port = port
        self.auth_token = auth_token
        self.server_socket: Optional[socket.socket] = None
        self.is_running = False
        self.active_connections = 0
        self._lock = threading.Lock()

    def start(self, in_background: bool = True) -> None:
        """Bind and listen on TCP port."""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.server_socket.settimeout(1.0)  # Allows checking self.is_running regularly
        self.is_running = True

        if in_background:
            thread = threading.Thread(target=self._listen_loop, daemon=True)
            thread.start()
        else:
            self._listen_loop()

    def _listen_loop(self) -> None:
        """Main accept loop for incoming TCP client sockets."""
        while self.is_running:
            try:
                client_sock, client_addr = self.server_socket.accept()
                with self._lock:
                    self.active_connections += 1
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_sock, client_addr),
                    daemon=True,
                )
                client_thread.start()
            except socket.timeout:
                continue
            except Exception:
                if self.is_running:
                    break

    def _handle_client(self, client_sock: socket.socket, client_addr: tuple) -> None:
        """Process structured newline-delimited JSON commands from a client."""
        client_sock.settimeout(5.0)  # 5-second socket read timeout
        is_authenticated = False
        buffer = ""

        try:
            while self.is_running:
                data = client_sock.recv(2048)
                if not data:
                    break

                buffer += data.decode("utf-8")
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        request = json.loads(line)
                    except json.JSONDecodeError:
                        self._send(client_sock, {"status": "ERROR", "message": "Invalid JSON format."})
                        continue

                    command = request.get("command", "").upper()
                    payload = request.get("payload", {})

                    if command == "PING":
                        self._send(client_sock, {"status": "SUCCESS", "response": "PONG", "timestamp": time.time()})

                    elif command == "AUTH":
                        provided_token = payload.get("token")
                        if provided_token == self.auth_token:
                            is_authenticated = True
                            self._send(client_sock, {"status": "SUCCESS", "message": "Authenticated successfully."})
                        else:
                            self._send(client_sock, {"status": "UNAUTHORIZED", "message": "Bad token."})

                    elif command == "STATS":
                        if not is_authenticated:
                            self._send(client_sock, {"status": "UNAUTHORIZED", "message": "Call AUTH first."})
                        else:
                            self._send(
                                client_sock,
                                {
                                    "status": "SUCCESS",
                                    "stats": {
                                        "server": "SkillSwap-TCP-Node",
                                        "timestamp": time.time(),
                                        "active_tcp_connections": self.active_connections,
                                        "engine": "Python-Raw-Socket",
                                    },
                                },
                            )

                    elif command == "ECHO":
                        self._send(client_sock, {"status": "SUCCESS", "echo": payload})

                    elif command == "QUIT":
                        self._send(client_sock, {"status": "SUCCESS", "message": "Closing session."})
                        return

                    else:
                        self._send(client_sock, {"status": "UNKNOWN_COMMAND", "command": command})

        except (socket.timeout, ConnectionResetError, BrokenPipeError):
            pass
        finally:
            with self._lock:
                self.active_connections = max(0, self.active_connections - 1)
            try:
                client_sock.close()
            except Exception:
                pass

    def _send(self, sock: socket.socket, obj: dict) -> None:
        """Serialize and transmit newline-terminated message."""
        payload = (json.dumps(obj) + "\n").encode("utf-8")
        sock.sendall(payload)

    def stop(self) -> None:
        """Gracefully close server socket and terminate listeners."""
        self.is_running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass


if __name__ == "__main__":
    server = RawSkillSwapTCPServer(port=9099)
    print("Starting Raw SkillSwap TCP Server on 127.0.0.1:9099...")
    server.start(in_background=False)
