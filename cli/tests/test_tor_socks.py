import os
import select
import shutil
import socket
import socketserver
import ssl
import struct
import subprocess
import threading
from contextlib import contextmanager
from unittest.mock import Mock, patch

import pytest
import requests
import socks

from onionshare_cli.tor_socks import (
    UnixSocks5Adapter,
    UnixSocksHTTPConnection,
    UnixSocksHTTPSConnection,
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
            _, port = echo_server.server_address

            socks_path = os.path.join(temp_dir.name, "socks")
            socks_server = ThreadingUnixStreamServer(socks_path, FakeSocks5Handler)
            thread = threading.Thread(target=socks_server.serve_forever, daemon=True)
            thread.start()

            try:
                # The destination is given as a hostname, so the address
                # should be sent to the SOCKS server as a domain name
                # (remote DNS, like socks5h)
                with UnixSocksSocket(socks_path, timeout=5) as s:
                    s.connect(("localhost", port))
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


def read_exact(sock, length):
    data = b""
    while len(data) < length:
        chunk = sock.recv(length - len(data))
        if not chunk:
            raise EOFError("SOCKS client disconnected")
        data += chunk
    return data


class SocksWebhookHandler(socketserver.BaseRequestHandler):
    """Record SOCKS destinations and serve HTTP without resolving the host."""

    def handle(self):
        self.request.settimeout(5)
        version, count = read_exact(self.request, 2)
        assert version == 5
        assert 0 in read_exact(self.request, count)
        self.request.sendall(b"\x05\x00")
        assert read_exact(self.request, 4) == b"\x05\x01\x00\x03"
        length = read_exact(self.request, 1)[0]
        host = read_exact(self.request, length).decode("ascii")
        port = struct.unpack("!H", read_exact(self.request, 2))[0]
        self.server.destinations.append((host, port))
        self.request.sendall(b"\x05\x00\x00\x01\x7f\x00\x00\x01\x00\x01")
        sock = self.request
        if self.server.tls_context:
            sock = self.server.tls_context.wrap_socket(sock, server_side=True)
        try:
            with sock.makefile("rb") as stream:
                request_line = stream.readline()
                headers = {}
                while True:
                    line = stream.readline()
                    if line in (b"\r\n", b""):
                        break
                    name, value = line.split(b":", 1)
                    headers[name.lower()] = value.strip()
                body = stream.read(int(headers.get(b"content-length", b"0")))
            self.server.requests.append((request_line, body))
            if b" /redirect " in request_line:
                sock.sendall(
                    b"HTTP/1.1 307 Temporary Redirect\r\n"
                    b"Location: /webhook\r\nContent-Length: 0\r\n"
                    b"Connection: close\r\n\r\n"
                )
            else:
                sock.sendall(
                    b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n"
                    b"Connection: close\r\n\r\nOK"
                )
        finally:
            if sock is not self.request:
                sock.close()


@contextmanager
def webhook_proxy(tmp_path, proxy_type, tls_context=None):
    if proxy_type == "unix":
        if not hasattr(socket, "AF_UNIX"):
            pytest.skip("requires unix domain sockets")
        address = str(tmp_path / "socks")
        server = ThreadingUnixStreamServer(address, SocksWebhookHandler)
        port = None
    else:
        server = socketserver.ThreadingTCPServer(("127.0.0.1", 0), SocksWebhookHandler)
        address, port = server.server_address
    server.daemon_threads = True
    server.destinations = []
    server.requests = []
    server.tls_context = tls_context
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with make_tor_socks_session(proxy_type, address, port) as session:
            yield session, server
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


@pytest.fixture
def webhook_tls(tmp_path):
    openssl = shutil.which("openssl")
    if openssl is None:
        pytest.skip("openssl is required for the local HTTPS test certificate")
    cert, key = tmp_path / "cert.pem", tmp_path / "key.pem"
    subprocess.run(
        [
            openssl,
            "req",
            "-x509",
            "-newkey",
            "rsa:2048",
            "-nodes",
            "-keyout",
            str(key),
            "-out",
            str(cert),
            "-days",
            "1",
            "-subj",
            "/CN=webhook.invalid",
            "-addext",
            "subjectAltName=DNS:webhook.invalid",
        ],
        check=True,
        capture_output=True,
    )
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(cert, key)
    return context, str(cert)


@pytest.mark.parametrize("proxy_type", ["tcp", "unix"])
@pytest.mark.parametrize("scheme", ["http", "https"])
@pytest.mark.parametrize("no_proxy", ["", "*"])
def test_webhook_ignores_environment_proxies(
    tmp_path, monkeypatch, request, proxy_type, scheme, no_proxy
):
    # An unusable environment proxy must not replace either Tor transport.
    for name in ("http_proxy", "https_proxy", "all_proxy"):
        monkeypatch.setenv(name, "http://127.0.0.1:1")
        monkeypatch.setenv(name.upper(), "http://127.0.0.1:1")
    monkeypatch.setenv("no_proxy", no_proxy)
    monkeypatch.setenv("NO_PROXY", no_proxy)
    context, verify = (
        request.getfixturevalue("webhook_tls") if scheme == "https" else (None, True)
    )
    original_getaddrinfo = socket.getaddrinfo

    def no_destination_dns(host, *args, **kwargs):
        assert host != "webhook.invalid", "destination DNS must be resolved by Tor"
        return original_getaddrinfo(host, *args, **kwargs)

    monkeypatch.setattr(socket, "getaddrinfo", no_destination_dns)
    with webhook_proxy(tmp_path, proxy_type, context) as (session, server):
        response = session.post(
            f"{scheme}://webhook.invalid/redirect",
            data=b"notification",
            timeout=5,
            verify=verify,
        )
        assert response.status_code == 200
        assert response.text == "OK"
        assert len(response.history) == 1
        port = 443 if scheme == "https" else 80
        assert server.destinations == [("webhook.invalid", port)] * 2
        assert server.requests == [
            (b"POST /redirect HTTP/1.1\r\n", b"notification"),
            (b"POST /webhook HTTP/1.1\r\n", b"notification"),
        ]


@pytest.mark.parametrize("scheme", ["http", "https"])
def test_missing_unix_proxy_never_connects_directly(tmp_path, scheme):
    path = str(tmp_path / "missing")
    with make_tor_socks_session("unix", path, None) as session:
        with (
            patch("socket.getaddrinfo", side_effect=AssertionError("direct DNS")),
            patch("onionshare_cli.tor_socks.UnixSocksSocket") as socket_class,
        ):
            socket_class.return_value.connect.side_effect = FileNotFoundError(path)
            with pytest.raises(requests.exceptions.ConnectionError):
                session.get(f"{scheme}://webhook.invalid/", timeout=1)
            socket_class.assert_called_once_with(path, timeout=1)
            socket_class.return_value.connect.assert_called_once_with(
                ("webhook.invalid", 443 if scheme == "https" else 80)
            )


@pytest.mark.parametrize("port", [True, False, None, "80", 1.5, -1, 0, 65536, 2**100])
def test_invalid_destination_port(port):
    with patch("socket.socket.connect") as connect:
        with pytest.raises(socks.GeneralProxyError, match="Invalid destination port"):
            UnixSocksSocket.connect(Mock(), ("webhook.invalid", port))
        connect.assert_not_called()


@pytest.mark.parametrize("port", [1, 65535])
def test_valid_destination_port_boundaries(port):
    sock = Mock(socks_path="/unused")
    with patch("socket.socket.connect") as connect:
        UnixSocksSocket.connect(sock, ("webhook.invalid", port))
        connect.assert_called_once_with(sock, "/unused")
        sock._negotiate_SOCKS5.assert_called_once_with("webhook.invalid", port)


@pytest.mark.parametrize(
    "scheme, connection_class",
    [("http", UnixSocksHTTPConnection), ("https", UnixSocksHTTPSConnection)],
)
def test_unix_pools_keep_their_own_socks_path(scheme, connection_class):
    with (
        make_tor_socks_session("unix", "/first/socks", None) as first,
        make_tor_socks_session("unix", "/second/socks", None) as second,
    ):
        pools = []
        for session, path in ((first, "/first/socks"), (second, "/second/socks")):
            manager = session.get_adapter(f"{scheme}://").poolmanager
            pool = manager.connection_from_url(f"{scheme}://webhook.invalid")
            assert pool is manager.connection_from_url(f"{scheme}://webhook.invalid")
            connection = pool._new_conn()
            assert isinstance(connection, connection_class)
            assert connection._socks_path == path
            pools.append(pool)
        assert pools[0] is not pools[1]
