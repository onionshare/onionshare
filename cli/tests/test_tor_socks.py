import os
import select
import socket
import socketserver
import struct
import threading

import pytest

from onionshare_cli.tor_socks import (
    UnixSocks5Adapter,
    UnixSocksSocket,
    make_tor_socks_session,
)


class EchoHandler(socketserver.BaseRequestHandler):
    """
    A plain TCP server that sends a greeting and echoes one line back.
    """

    def handle(self):
        self.request.sendall(b"hello through socks\n")
        data = self.request.recv(1024)
        self.request.sendall(data)


class FakeSocks5Handler(socketserver.BaseRequestHandler):
    """
    A fake SOCKS5 server that connects to the requested destination.
    """

    def handle(self):
        data = self.request.recv(256)
        assert data[0:1] == b"\x05"
        self.request.sendall(b"\x05\x00")

        req = self.request.recv(256)
        ver, cmd, rsv, atyp = req[0], req[1], req[2], req[3]
        assert ver == 5 and cmd == 1
        if atyp == 0x01:
            host = socket.inet_ntoa(req[4:8])
            port = struct.unpack(">H", req[8:10])[0]
        elif atyp == 0x03:
            length = req[4]
            host = req[5 : 5 + length].decode()
            port = struct.unpack(">H", req[5 + length : 7 + length])[0]
        elif atyp == 0x04:
            host = socket.inet_ntop(socket.AF_INET6, req[4:20])
            port = struct.unpack(">H", req[20:22])[0]
        else:
            raise ValueError(f"Unknown address type {atyp}")

        target = socket.create_connection((host, port))
        self.request.sendall(
            b"\x05\x00\x00\x01" + socket.inet_aton("127.0.0.1") + struct.pack(">H", 1)
        )

        # Relay between the client and the target until either closes
        sockets = [self.request, target]
        try:
            while True:
                readable, _, _ = select.select(sockets, [], [], 2)
                if not readable:
                    break
                for s in readable:
                    data = s.recv(1024)
                    if not data:
                        return
                    other = target if s is self.request else self.request
                    other.sendall(data)
        except OSError:
            pass
        finally:
            target.close()


class ThreadingUnixStreamServer(
    socketserver.ThreadingMixIn, socketserver.UnixStreamServer
):
    daemon_threads = True


def start_echo_server():
    server = socketserver.ThreadingTCPServer(("127.0.0.1", 0), EchoHandler)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


@pytest.mark.skipif(
    not hasattr(socket, "AF_UNIX"), reason="requires unix domain sockets"
)
class TestUnixSocksSocket:
    def test_connect_through_unix_socks(self, temp_dir):
        echo_server = start_echo_server()
        try:
            host, port = echo_server.server_address

            socks_path = os.path.join(temp_dir.name, "socks")
            socks_server = ThreadingUnixStreamServer(socks_path, FakeSocks5Handler)
            thread = threading.Thread(target=socks_server.serve_forever, daemon=True)
            thread.start()

            try:
                s = UnixSocksSocket(socks_path, timeout=5)
                # The destination is given as a hostname, so the address
                # should be sent to the SOCKS server as a domain name
                # (remote DNS, like socks5h)
                s.connect((host, port))
                assert s.recv(1024) == b"hello through socks\n"
                s.sendall(b"echo\n")
                assert s.recv(1024) == b"echo\n"
            finally:
                socks_server.shutdown()
                socks_server.server_close()
                os.unlink(socks_path)
        finally:
            echo_server.shutdown()
            echo_server.server_close()


class TestMakeTorSocksSession:
    def test_tcp_session(self):
        session = make_tor_socks_session("tcp", "127.0.0.1", 9050)
        expected_proxies = {
            "http": "socks5h://127.0.0.1:9050",
            "https": "socks5h://127.0.0.1:9050",
        }
        assert session.proxies == expected_proxies

    def test_unix_session(self):
        session = make_tor_socks_session("unix", "/run/tor/socks", None)
        for scheme in ("http://", "https://"):
            adapters = session.adapters[scheme]
            assert isinstance(adapters, UnixSocks5Adapter)
            assert adapters._socks_path == "/run/tor/socks"
