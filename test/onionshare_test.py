import socket
from onionshare import OnionShare
from nose import with_setup

def test_choose_port_returns_a_port_number():
    "choose_port() returns a port number"
    app = OnionShare()
    assert  1024 <= app.port <= 65535

def test_choose_port_returns_an_open_port():
    "choose_port() returns an open port"
    app = OnionShare()
    # choose a new port
    app.choose_port()
    socket.socket().bind(("127.0.0.1", app.port))
