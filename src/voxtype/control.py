from __future__ import annotations

import socket
import time

from .paths import runtime_dir


def _connect(timeout: float) -> socket.socket:
    path = runtime_dir() / "control.sock"
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        client.settimeout(timeout)
        client.connect(str(path))
        return client
    except (FileNotFoundError, ConnectionRefusedError) as first_error:
        client.close()
        import subprocess

        subprocess.run(
            ["systemctl", "--user", "start", "voxtype.service"], check=False
        )
        for _ in range(20):
            time.sleep(0.025)
            client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            try:
                client.settimeout(timeout)
                client.connect(str(path))
                return client
            except (FileNotFoundError, ConnectionRefusedError):
                client.close()
        raise first_error


def send_command(command: str, timeout: float = 2.0) -> dict:
    import json

    with _connect(timeout) as client:
        client.sendall((json.dumps({"command": command}) + "\n").encode())
        return json.loads(client.recv(4096).decode())


def toggle() -> None:
    try:
        with _connect(2.0) as client:
            client.sendall(b'{"command":"toggle"}\n')
    except OSError as exc:
        raise SystemExit(f"voxtype-ctl: could not reach VoxType: {exc}") from exc
