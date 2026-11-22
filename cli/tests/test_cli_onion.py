from unittest.mock import Mock, call

import pytest
from stem import SocketError

from onionshare_cli import onion as onion_module
from onionshare_cli.onion import Onion


class FakeSettings:
    def __init__(self):
        self.values = {}

    def get(self, key):
        return self.values.get(key)

    def set(self, key, value):
        self.values[key] = value

    def save(self):
        pass


class FakeCommon:
    def log(self, *args, **kwargs):
        pass


class FakeMeek:
    def __init__(self, common):
        pass

    def start(self):
        pass

    def cleanup(self):
        pass


def make_onion(monkeypatch, authenticated):
    # Skip Onion.__init__, which sets up a real Tor environment
    o = Onion.__new__(Onion)
    o.common = FakeCommon()
    o.settings = FakeSettings()
    monkeypatch.setattr(o, "is_authenticated", lambda: authenticated)
    return o


def record_circumvention(monkeypatch, bridges):
    """Replace CensorshipCircumvention and record how it is constructed."""
    calls = []

    class FakeCircumvention:
        def __init__(self, common, meek=None, onion=None):
            calls.append({"meek": meek, "onion": onion})

        def request_builtin_bridges(self):
            return bridges

    monkeypatch.setattr(onion_module, "CensorshipCircumvention", FakeCircumvention)
    monkeypatch.setattr(onion_module, "Meek", FakeMeek)
    return calls


class TestUpdateBuiltinBridges:
    def test_skips_tor_when_not_connected(self, monkeypatch):
        o = make_onion(monkeypatch, authenticated=False)
        calls = record_circumvention(monkeypatch, {"obfs4": ["bridge"]})
        o.update_builtin_bridges()
        # Only the Meek attempt is made
        assert len(calls) == 1
        assert calls[0]["onion"] is None
        assert isinstance(calls[0]["meek"], FakeMeek)

    def test_tries_tor_first_when_connected(self, monkeypatch):
        o = make_onion(monkeypatch, authenticated=True)
        calls = record_circumvention(monkeypatch, {"obfs4": ["bridge"]})
        o.update_builtin_bridges()
        assert len(calls) == 1
        assert calls[0]["onion"] is o
        assert calls[0]["meek"] is None
        assert o.settings.get("bridges_builtin") == {"obfs4": ["bridge"]}


class TestAutomaticConnection:
    @pytest.fixture
    def automatic_connection(self, monkeypatch):
        o = make_onion(monkeypatch, authenticated=False)
        o.common.platform = "Linux"
        o.settings.set("connection_type", "automatic")
        monkeypatch.delenv("TOR_CONTROL_PORT", raising=False)

        controller = Mock(spec=onion_module.Controller)
        controller.get_version.return_value.version_str = "0.4.8.16"
        from_port = Mock(side_effect=SocketError("Connection refused"))
        from_socket = Mock(side_effect=SocketError("No control socket"))
        monkeypatch.setattr(onion_module.Controller, "from_port", from_port)
        monkeypatch.setattr(onion_module.Controller, "from_socket_file", from_socket)
        return o, controller, from_port, from_socket

    @pytest.mark.parametrize("available_port", [9151, 9153, 9051])
    def test_uses_first_available_port(self, automatic_connection, available_port):
        o, controller, from_port, from_socket = automatic_connection

        def connect_to_port(*, port):
            if port != available_port:
                raise SocketError("Connection refused")
            return controller

        from_port.side_effect = connect_to_port
        o.connect(custom_settings=o.settings)

        ports = [9151, 9153, 9051]
        assert from_port.call_args_list == [
            call(port=port) for port in ports[: ports.index(available_port) + 1]
        ]
        assert o.c is controller
        assert o.connected_to_tor
        controller.authenticate.assert_called_once_with()
        from_socket.assert_not_called()

    def test_falls_back_to_socket(self, automatic_connection):
        o, controller, from_port, from_socket = automatic_connection
        from_socket.side_effect = [SocketError("No default socket"), controller]

        o.connect(custom_settings=o.settings)

        assert from_port.call_args_list == [
            call(port=9151),
            call(port=9153),
            call(port=9051),
        ]
        assert o.c is controller
        controller.authenticate.assert_called_once_with()

    def test_raises_when_no_controller_is_available(self, automatic_connection):
        o, controller, from_port, from_socket = automatic_connection

        with pytest.raises(onion_module.TorErrorAutomatic):
            o.connect(custom_settings=o.settings)

        assert from_port.call_args_list == [
            call(port=9151),
            call(port=9153),
            call(port=9051),
        ]
        assert from_socket.called
        controller.authenticate.assert_not_called()

    def test_uses_environment_port(self, automatic_connection, monkeypatch):
        o, controller, from_port, from_socket = automatic_connection
        monkeypatch.setenv("TOR_CONTROL_PORT", "19051")
        from_port.side_effect = None
        from_port.return_value = controller

        o.connect(custom_settings=o.settings)

        from_port.assert_called_once_with(port=19051)
        controller.authenticate.assert_called_once_with()
        from_socket.assert_not_called()
