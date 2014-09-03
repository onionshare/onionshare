"""
OnionShare | https://onionshare.org/

Copyright (C) 2014 Micah Lee <micah@micahflee.com>

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
from onionshare import OnionShare
from nose import with_setup

def test_choose_port_returns_a_port_number():
    "choose_port() returns a port number"
    app = OnionShare()
    app.choose_port()
    assert  1024 <= app.port <= 65535

def test_choose_port_returns_an_open_port():
    "choose_port() returns an open port"
    app = OnionShare()
    # choose a new port
    app.choose_port()
    socket.socket().bind(("127.0.0.1", app.port))
