import http.client
import os
import socket
import tempfile
import time
from threading import Thread

from onionshare_cli.mode_settings import ModeSettings
from onionshare_cli.settings import Settings
from onionshare_cli.web import Web


class UnixHTTPConnection(http.client.HTTPConnection):
    """An HTTPConnection that talks to a server over a unix socket."""

    def __init__(self, socket_path):
        super().__init__("localhost")
        self.socket_path = socket_path

    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.connect(self.socket_path)


def wait_for_socket(path, timeout=10):
    """Wait until the server has bound the unix socket."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if os.path.exists(path):
            return True
        time.sleep(0.05)
    return False


class TestWebUnixSocket:
    def test_waitress_listens_on_unix_socket(self, temp_dir, common_obj):
        common_obj.settings = Settings(common_obj)
        mode_settings = ModeSettings(common_obj)
        web = Web(common_obj, False, mode_settings, "receive")

        socket_dir = tempfile.mkdtemp()
        socket_path = os.path.join(socket_dir, "web_socket")

        thread = Thread(target=web.start, args=(0, socket_path), daemon=True)
        thread.start()
        try:
            assert wait_for_socket(socket_path), "web server never bound the socket"
            assert oct(os.stat(socket_path).st_mode & 0o777) == "0o600"

            conn = UnixHTTPConnection(socket_path)
            try:
                conn.request("GET", "/")
                response = conn.getresponse()
                assert response.status == 200
                response.read()
            finally:
                conn.close()
        finally:
            web.stop(0)
            thread.join(timeout=5)

        assert not os.path.exists(socket_path)
        assert not os.path.exists(socket_dir)
