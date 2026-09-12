import socket
import unittest
from unittest.mock import patch

from voxtype.control import toggle


class ControlTests(unittest.TestCase):
    def test_toggle_sends_the_minimal_control_message(self):
        client, server = socket.socketpair()
        with server, patch("voxtype.control._connect", return_value=client):
            toggle()
            self.assertEqual(server.recv(4096), b'{"command":"toggle"}\n')


if __name__ == "__main__":
    unittest.main()
