# -*- coding: utf-8 -*-
"""
OnionShare | https://onionshare.org/

Copyright (C) 2014-2026 Micah Lee, et al. <micah@micahflee.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import socket
import sys

import requests
import socks
import urllib3
from urllib3.connection import HTTPConnection, HTTPSConnection
from urllib3.connectionpool import HTTPConnectionPool, HTTPSConnectionPool
from urllib3.exceptions import NewConnectionError
from urllib3.poolmanager import PoolManager


class UnixSocksSocket(socks.socksocket):
    """
    A SOCKS5 client socket, where the SOCKS server is listening on a
    unix domain socket file instead of a TCP address and port.

    Connections are negotiated in the same way as PySocks' socksocket,
    with remote DNS resolution (like socks5h), so .onion domains and
    other hostnames are resolved by Tor.
    """

    def __init__(self, socks_path, timeout=None):
        self.socks_path = socks_path
        super().__init__(family=socket.AF_UNIX, type=socket.SOCK_STREAM)
        self.set_proxy(proxy_type=socks.PROXY_TYPE_SOCKS5, addr=socks_path)
        if isinstance(timeout, (int, float)):
            self.settimeout(timeout)

    def connect(self, dest_pair):
        """
        Connects to the specified (host, port) pair through the SOCKS
        unix domain socket.
        """
        dest_addr, dest_port = dest_pair
        if not isinstance(dest_port, int):
            raise socks.GeneralProxyError("Invalid destination port")

        # Connect to the SOCKS server itself. This bypasses
        # socks.socksocket.connect(), which requires a (host, port) pair
        # and can't connect over unix domain sockets.
        socket.socket.connect(self, self.socks_path)

        # Negotiate the SOCKS5 connection to the destination
        try:
            self._negotiate_SOCKS5(dest_addr, dest_port)
        except socks.ProxyError:
            self.close()
            raise
        except OSError as error:
            self.close()
            raise socks.GeneralProxyError("Socket error", error)


class UnixSocksHTTPConnection(HTTPConnection):
    """
    A plain-text HTTP connection that connects through a SOCKS5
    unix domain socket.
    """

    def __init__(self, socks_path, *args, **kwargs):
        self._socks_path = socks_path
        super().__init__(*args, **kwargs)

    def _new_conn(self):
        try:
            sock = UnixSocksSocket(self._socks_path, timeout=self.timeout)
            sock.connect((self._dns_host, self.port))
        except (socks.ProxyError, socket.error) as e:
            raise NewConnectionError(
                self, f"Failed to establish a new connection: {e}"
            ) from e
        sys.audit("http.client.connect", self, self.host, self.port)
        return sock


class UnixSocksHTTPSConnection(HTTPSConnection):
    """
    A TLS-secured HTTP connection that connects through a SOCKS5
    unix domain socket.
    """

    def __init__(self, socks_path, *args, **kwargs):
        self._socks_path = socks_path
        super().__init__(*args, **kwargs)

    def _new_conn(self):
        try:
            sock = UnixSocksSocket(self._socks_path, timeout=self.timeout)
            sock.connect((self._dns_host, self.port))
        except (socks.ProxyError, socket.error) as e:
            raise NewConnectionError(
                self, f"Failed to establish a new connection: {e}"
            ) from e
        sys.audit("http.client.connect", self, self.host, self.port)
        return sock


class UnixSocksHTTPConnectionPool(HTTPConnectionPool):
    ConnectionCls = UnixSocksHTTPConnection


class UnixSocksHTTPSConnectionPool(HTTPSConnectionPool):
    ConnectionCls = UnixSocksHTTPSConnection


class UnixSocksPoolManager(PoolManager):
    pool_classes_by_scheme = {
        "http": UnixSocksHTTPConnectionPool,
        "https": UnixSocksHTTPSConnectionPool,
    }


class UnixSocks5Adapter(requests.adapters.HTTPAdapter):
    """
    A requests transport adapter that makes all requests through a
    SOCKS5 proxy listening on a unix domain socket file.
    """

    def __init__(self, socks_path, **kwargs):
        self._socks_path = socks_path
        super().__init__(**kwargs)

    def init_poolmanager(
        self,
        connections,
        maxsize,
        block=requests.adapters.DEFAULT_POOLBLOCK,
        **pool_kwargs,
    ):
        pool_kwargs["socks_path"] = self._socks_path
        self.poolmanager = UnixSocksPoolManager(
            num_pools=connections, maxsize=maxsize, block=block, **pool_kwargs
        )


def make_tor_socks_session(proxy_type, address, port):
    """
    Return a requests.Session configured to make requests through the
    Tor SOCKS proxy, as returned by Onion.get_tor_socks_proxy().

    For proxy_type "tcp", requests go through socks5h://address:port.
    For proxy_type "unix", address is the path of the SOCKS unix domain
    socket file and requests go through it.
    """
    session = requests.Session()
    if proxy_type == "unix":
        adapter = UnixSocks5Adapter(address)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
    else:
        session.proxies = {
            "http": f"socks5h://{address}:{port}",
            "https": f"socks5h://{address}:{port}",
        }
    return session
