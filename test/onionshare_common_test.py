"""
OnionShare | https://onionshare.org/

Copyright (C) 2017 Micah Lee <micah@micahflee.com>

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
from onionshare import common


def test_get_platform_returns_platform_system():
    """get_platform() returns platform.system() when ONIONSHARE_PLATFORM is not defined"""
    p = common.platform.system
    common.platform.system = lambda: 'Sega Saturn'
    assert common.get_platform() == 'Sega Saturn'
    common.platform.system = p

def test_get_available_port_returns_an_open_port():
    """get_available_port() should return an open port within the range"""
    for i in range(100):
        port = common.get_available_port(1024, 2048)
        assert 1024 <= port <= 2048
        socket.socket().bind(("127.0.0.1", port))
