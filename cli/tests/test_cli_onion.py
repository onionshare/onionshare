import os
import sys
from unittest.mock import Mock, call

import pytest
from stem import SocketError

from onionshare_cli import onion as onion_module
from onionshare_cli.censorship import CensorshipCircumventionError
from onionshare_cli.common import CannotFindTor, Common
from onionshare_cli.meek import MeekNotFound, MeekNotRunning
from onionshare_cli.onion import BundledTorMissingTransport, Onion


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
    # Use the real bridge validation
    check_builtin_bridge_lines = Common.check_builtin_bridge_lines
    check_builtin_bridges_valid = Common.check_builtin_bridges_valid

    def log(self, *args, **kwargs):
        pass


class FakeMeek:
    def __init__(self, common, get_tor_paths=None):
        self.get_tor_paths = get_tor_paths

    def start(self):
        pass

    def cleanup(self):
        pass


def fake_get_tor_paths():
    pass


OBFS4_BRIDGE = (
    "obfs4 192.0.2.10:443 10A6CD36A537FCE513A322361547444B393989F0 "
    "cert=K1gDtDAIcUfeLqbstggjIw2rtgIKqdIhUlHp82XRqNSq iat-mode=0"
)
MEEK_BRIDGE = (
    "meek_lite 192.0.2.20:80 url=https://example.rsc.cdn77.org "
    "front=www.example.net utls=HelloRandomizedALPN"
)
BRIDGES = {"obfs4": [OBFS4_BRIDGE], "meek": [MEEK_BRIDGE]}
EXISTING = {"obfs4": ["obfs4 192.0.2.99:443 39562501228A4D5E27FCA4C0C81A01EE23AE3EE4"]}


def make_onion(monkeypatch, authenticated):
    # Skip Onion.__init__, which sets up a real Tor environment
    o = Onion.__new__(Onion)
    o.common = FakeCommon()
    o.settings = FakeSettings()
    o.get_tor_paths = fake_get_tor_paths
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
        calls = record_circumvention(monkeypatch, BRIDGES)
        o.update_builtin_bridges()
        # Only the Meek attempt is made
        assert len(calls) == 1
        assert calls[0]["onion"] is None
        assert isinstance(calls[0]["meek"], FakeMeek)

    def test_tries_tor_first_when_connected(self, monkeypatch):
        o = make_onion(monkeypatch, authenticated=True)
        calls = record_circumvention(monkeypatch, BRIDGES)
        o.update_builtin_bridges()
        assert len(calls) == 1
        assert calls[0]["onion"] is o
        assert calls[0]["meek"] is None
        assert o.settings.get("bridges_builtin") == BRIDGES

    def test_missing_meek_keeps_existing_bridges(self, monkeypatch, capsys):
        o = make_onion(monkeypatch, authenticated=False)
        existing = EXISTING
        o.settings.set("bridges_builtin", existing)

        class MissingMeek(FakeMeek):
            def start(self):
                raise MeekNotFound(o.common)

        monkeypatch.setattr(onion_module, "Meek", MissingMeek)
        assert o.update_builtin_bridges() is False
        assert o.settings.get("bridges_builtin") == existing
        assert "meek" in capsys.readouterr().out.lower()

    def test_meek_not_running_keeps_existing_bridges(self, monkeypatch, capsys):
        o = make_onion(monkeypatch, authenticated=False)
        existing = EXISTING
        o.settings.set("bridges_builtin", existing)

        class BrokenMeek(FakeMeek):
            def start(self):
                raise MeekNotRunning(o.common, "boom")

        monkeypatch.setattr(onion_module, "Meek", BrokenMeek)
        assert o.update_builtin_bridges() is False
        assert o.settings.get("bridges_builtin") == existing
        assert "meek" in capsys.readouterr().out.lower()

    def test_meek_cleanup_runs_on_failure(self, monkeypatch):
        o = make_onion(monkeypatch, authenticated=False)
        cleaned = []

        class TrackedMeek(FakeMeek):
            def start(self):
                raise MeekNotFound(o.common)

            def cleanup(self):
                cleaned.append(True)

        monkeypatch.setattr(onion_module, "Meek", TrackedMeek)
        assert o.update_builtin_bridges() is False
        assert cleaned == [True]

    def test_meek_uses_the_same_tor_paths_as_onion(self, monkeypatch):
        # The desktop app passes its own get_tor_paths to Onion; Meek must be
        # given the same one rather than falling back to the CLI's lookup.
        o = make_onion(monkeypatch, authenticated=False)
        calls = record_circumvention(monkeypatch, BRIDGES)
        o.update_builtin_bridges()
        assert calls[0]["meek"].get_tor_paths is fake_get_tor_paths

    def test_meek_binaries_not_found_keeps_existing_bridges(self, monkeypatch):
        o = make_onion(monkeypatch, authenticated=False)
        o.settings.set("bridges_builtin", EXISTING)

        class UnfindableMeek(FakeMeek):
            def __init__(self, common, get_tor_paths=None):
                raise CannotFindTor()

        monkeypatch.setattr(onion_module, "Meek", UnfindableMeek)
        assert o.update_builtin_bridges() is False
        assert o.settings.get("bridges_builtin") == EXISTING

    def test_meek_request_error_keeps_existing_bridges(self, monkeypatch):
        o = make_onion(monkeypatch, authenticated=False)
        o.settings.set("bridges_builtin", EXISTING)
        cleaned = []

        class TrackedMeek(FakeMeek):
            def cleanup(self):
                cleaned.append(True)

        class FailingCircumvention:
            def __init__(self, common, meek=None, onion=None):
                pass

            def request_builtin_bridges(self):
                raise CensorshipCircumventionError("timed out")

        monkeypatch.setattr(onion_module, "Meek", TrackedMeek)
        monkeypatch.setattr(
            onion_module, "CensorshipCircumvention", FailingCircumvention
        )
        assert o.update_builtin_bridges() is False
        assert o.settings.get("bridges_builtin") == EXISTING
        assert cleaned == [True]

    def test_tor_request_error_falls_back_to_meek(self, monkeypatch):
        o = make_onion(monkeypatch, authenticated=True)
        calls = []

        class FlakyCircumvention:
            def __init__(self, common, meek=None, onion=None):
                self.onion = onion
                calls.append({"meek": meek, "onion": onion})

            def request_builtin_bridges(self):
                if self.onion:
                    raise CensorshipCircumventionError("timed out")
                return BRIDGES

        monkeypatch.setattr(onion_module, "Meek", FakeMeek)
        monkeypatch.setattr(onion_module, "CensorshipCircumvention", FlakyCircumvention)
        assert o.update_builtin_bridges() is True
        assert len(calls) == 2
        assert calls[0]["onion"] is o
        assert isinstance(calls[1]["meek"], FakeMeek)
        assert o.settings.get("bridges_builtin") == BRIDGES

    @pytest.mark.parametrize(
        "response",
        [
            ["not", "a", "dict"],
            {"obfs4": "not a list"},
            {"obfs4": [OBFS4_BRIDGE + "\nSocksPort 0.0.0.0:9050"]},
            {"obfs4": ["SocksPort 0.0.0.0:9050"]},
            {"obfs4\nSocksPort 0.0.0.0:9050": [OBFS4_BRIDGE]},
        ],
    )
    def test_malformed_bridges_are_not_saved(self, monkeypatch, response):
        o = make_onion(monkeypatch, authenticated=False)
        o.settings.set("bridges_builtin", EXISTING)
        record_circumvention(monkeypatch, response)
        assert o.update_builtin_bridges() is False
        assert o.settings.get("bridges_builtin") == EXISTING

    def test_only_well_formed_bridges_are_saved(self, monkeypatch):
        o = make_onion(monkeypatch, authenticated=False)
        response = {
            "obfs4": [OBFS4_BRIDGE, OBFS4_BRIDGE + "\r\nSocksPort 0.0.0.0:9050"],
            "meek": [MEEK_BRIDGE],
            "snowflake": [None, 5, ""],
        }
        record_circumvention(monkeypatch, response)
        assert o.update_builtin_bridges() is True
        assert o.settings.get("bridges_builtin") == BRIDGES


class TestCheckBridgeTransportsAvailable:
    @pytest.fixture
    def onion_with_torrc(self, monkeypatch, tmp_path):
        """An Onion that has every transport program, and a way to set its torrc."""
        o = make_onion(monkeypatch, authenticated=False)
        for name in ("obfs4proxy", "snowflake-client", "webtunnel-client"):
            program = tmp_path / name
            program.write_text("")
            program.chmod(0o755)
        o.obfs4proxy_file_path = str(tmp_path / "obfs4proxy")
        o.snowflake_file_path = str(tmp_path / "snowflake-client")
        o.webtunnel_file_path = str(tmp_path / "webtunnel-client")
        o.tor_torrc = str(tmp_path / "torrc")

        def write_torrc(*bridges):
            lines = ["SocksPort 9050", "ClientTransportPlugin obfs4 exec None"]
            if bridges:
                lines.append("UseBridges 1")
            lines += [f"Bridge {bridge}" for bridge in bridges]
            (tmp_path / "torrc").write_text("\n".join(lines) + "\n")

        o.write_torrc = write_torrc
        return o

    def test_no_bridges_needs_nothing(self, onion_with_torrc):
        o = onion_with_torrc
        o.obfs4proxy_file_path = None
        o.snowflake_file_path = None
        o.webtunnel_file_path = None
        o.write_torrc()
        o.check_bridge_transports_available()

    def test_passes_when_the_programs_are_present(self, onion_with_torrc):
        o = onion_with_torrc
        o.write_torrc(
            OBFS4_BRIDGE,
            MEEK_BRIDGE,
            "snowflake 192.0.2.3:80 2B280B23E1107BB62ABFC40DDCC8824814F80A72",
            "webtunnel 192.0.2.4:443 ABCDEF url=https://example.com/path",
        )
        o.check_bridge_transports_available()

    @pytest.mark.parametrize(
        "bridge,attribute,transport,program",
        [
            (OBFS4_BRIDGE, "obfs4proxy_file_path", "obfs4", "obfs4proxy"),
            (MEEK_BRIDGE, "obfs4proxy_file_path", "meek_lite", "obfs4proxy"),
            (
                "snowflake 192.0.2.3:80 2B280B23E1107BB62ABFC40DDCC8824814F80A72",
                "snowflake_file_path",
                "snowflake",
                "snowflake-client",
            ),
            (
                "webtunnel 192.0.2.4:443 ABCDEF url=https://example.com/path",
                "webtunnel_file_path",
                "webtunnel",
                "webtunnel-client",
            ),
        ],
    )
    @pytest.mark.parametrize("missing", [None, "/nonexistent/program"])
    def test_raises_when_the_program_is_missing(
        self, onion_with_torrc, capsys, bridge, attribute, transport, program, missing
    ):
        o = onion_with_torrc
        setattr(o, attribute, missing)
        o.write_torrc(bridge)
        with pytest.raises(BundledTorMissingTransport) as e:
            o.check_bridge_transports_available()
        assert e.value.args == (transport, program)
        # The CLI exits without printing the exception, so it must say why
        assert program in capsys.readouterr().out

    @pytest.mark.skipif(
        sys.platform == "win32", reason="Windows has no executable permission bit"
    )
    def test_raises_when_the_program_is_not_executable(self, onion_with_torrc):
        o = onion_with_torrc
        os.chmod(o.obfs4proxy_file_path, 0o644)
        o.write_torrc(OBFS4_BRIDGE)
        with pytest.raises(BundledTorMissingTransport):
            o.check_bridge_transports_available()

    def test_only_transports_in_use_are_needed(self, onion_with_torrc):
        o = onion_with_torrc
        o.snowflake_file_path = None
        o.webtunnel_file_path = None
        o.write_torrc(OBFS4_BRIDGE)
        o.check_bridge_transports_available()

    def test_plain_bridges_need_nothing(self, onion_with_torrc):
        o = onion_with_torrc
        o.obfs4proxy_file_path = None
        o.write_torrc(
            "192.0.2.5:443 10A6CD36A537FCE513A322361547444B393989F0",
            "[2001:db8::1]:443 10A6CD36A537FCE513A322361547444B393989F0",
        )
        o.check_bridge_transports_available()


class TestMeekExceptions:
    """The Meek exceptions should describe themselves when logged."""

    def test_meek_not_found_message(self):
        assert str(MeekNotFound(FakeCommon())) == "Could not find the meek binary"

    def test_meek_not_running_message(self):
        assert (
            str(MeekNotRunning(FakeCommon(), "boom"))
            == "Meek experienced an error starting up: boom"
        )
        assert (
            str(MeekNotRunning(FakeCommon())) == "Meek experienced an error starting up"
        )


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
