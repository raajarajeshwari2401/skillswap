"""Tests for Python raw TCP client-server socket programming."""

import time
import socket
import pytest
from app.sockets.raw_tcp_server import RawSkillSwapTCPServer
from app.sockets.raw_tcp_client import RawSkillSwapTCPClient


def test_raw_tcp_client_server_handshake():
    """Verify raw socket connection, structured JSON exchange, timeouts, and teardown."""
    test_port = 9199
    auth_secret = "test-secret-token-2026"

    # Start raw TCP server in daemon thread
    server = RawSkillSwapTCPServer(host="127.0.0.1", port=test_port, auth_token=auth_secret)
    server.start(in_background=True)
    time.sleep(0.1)  # Allow socket bind

    client = RawSkillSwapTCPClient(host="127.0.0.1", port=test_port, timeout=2.0)
    try:
        try:
            client.connect()
        except (PermissionError, OSError) as exc:
            if "10013" in str(exc):
                pytest.skip("Raw socket connections are restricted by sandbox/OS security policy.")
            raise

        # 1. Test PING -> PONG
        ping_res = client.ping()
        assert ping_res["status"] == "SUCCESS"
        assert ping_res["response"] == "PONG"

        # 2. Test Unauthorized STATS command
        bad_stats = client.get_stats()
        assert bad_stats["status"] == "UNAUTHORIZED"

        # 3. Test Invalid AUTH token
        bad_auth = client.authenticate("wrong-token")
        assert bad_auth["status"] == "UNAUTHORIZED"

        # 4. Test Valid AUTH token
        good_auth = client.authenticate(auth_secret)
        assert good_auth["status"] == "SUCCESS"

        # 5. Test Authorized STATS command
        stats = client.get_stats()
        assert stats["status"] == "SUCCESS"
        assert stats["stats"]["server"] == "SkillSwap-TCP-Node"

        # 6. Test ECHO command
        echo_res = client.echo({"message": "Python Sockets Live"})
        assert echo_res["status"] == "SUCCESS"
        assert echo_res["echo"]["data"]["message"] == "Python Sockets Live"

    finally:
        client.close()
        server.stop()
