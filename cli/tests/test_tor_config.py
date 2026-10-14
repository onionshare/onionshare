from unittest.mock import Mock

import pytest

from onionshare_cli.onion import Onion, TorErrorInvalidSetting
from onionshare_cli.tor_config import upstream_proxy_config


def settings(**overrides):
    values = dict(
        connection_type="bundled",
        proxy_enabled=True,
        proxy_type="socks5",
        proxy_address="127.0.0.1",
        proxy_port=1080,
        proxy_username="",
        proxy_password="",
        socket_file_path="/run/tor/control",
        socks_socket_path="/run/tor/socks",
        socks_address="127.0.0.1",
        socks_port=9050,
    )
    values.update(overrides)
    return values


@pytest.mark.parametrize(
    "kind,directive",
    [("socks4", "Socks4Proxy"), ("socks5", "Socks5Proxy"), ("http", "HTTPSProxy")],
)
def test_upstream_proxy_protocol(kind, directive):
    assert (
        upstream_proxy_config(settings(proxy_type=kind))
        == f"\n{directive} 127.0.0.1:1080\n"
    )


def test_upstream_proxy_auth_quoted():
    config = upstream_proxy_config(
        settings(proxy_username="test user", proxy_password='a#b"c')
    )
    assert 'Socks5ProxyUsername "test user"' in config
    assert 'Socks5ProxyPassword "a#b\\"c"' in config
    assert (
        upstream_proxy_config(
            settings(proxy_type="http", proxy_username="test", proxy_password="a b")
        )
        == '\nHTTPSProxy 127.0.0.1:1080\nHTTPSProxyAuthenticator "test:a b"\n'
    )


@pytest.mark.parametrize(
    "overrides",
    [
        {"proxy_address": ""},
        {"proxy_address": "http://127.0.0.1"},
        {"proxy_address": "host\nDisableNetwork 1"},
        {"proxy_address": "host:1080"},
        {"proxy_port": 0},
        {"proxy_port": -1},
        {"proxy_port": 65536},
        {"proxy_port": True},
        {"proxy_type": "unknown"},
        {"proxy_username": "user"},
        {"proxy_username": "user", "proxy_password": "line\nbreak"},
        {"proxy_username": "user", "proxy_password": "x" * 256},
        {"proxy_type": "http", "proxy_username": "a:b", "proxy_password": "pass"},
    ],
)
def test_invalid_upstream_proxy(overrides):
    with pytest.raises(ValueError):
        upstream_proxy_config(settings(**overrides))


@pytest.mark.parametrize("mode", ["control_port", "socket_file", "automatic"])
def test_external_tor_does_not_inherit_upstream_proxy(mode):
    assert upstream_proxy_config(settings(connection_type=mode, proxy_port=0)) == ""


def test_disabled_proxy_and_socks4_ignore_saved_credentials():
    assert upstream_proxy_config(settings(proxy_enabled=False, proxy_port=0)) == ""
    assert (
        upstream_proxy_config(settings(proxy_type="socks4", proxy_username="saved"))
        == "\nSocks4Proxy 127.0.0.1:1080\n"
    )


def test_ipv6_proxy_address():
    assert (
        upstream_proxy_config(settings(proxy_address="::1"))
        == "\nSocks5Proxy [::1]:1080\n"
    )


def test_socket_mode_never_uses_hidden_tcp_settings():
    onion = Mock(settings=settings(connection_type="socket_file"))
    assert Onion.get_tor_socks_proxy(onion) == ("unix", "/run/tor/socks", None)
    onion.settings["socks_socket_path"] = " "
    with pytest.raises(TorErrorInvalidSetting, match="TCP fallback is not used"):
        Onion.get_tor_socks_proxy(onion)


def test_tcp_mode_ignores_saved_socket_path():
    onion = Mock(settings=settings(connection_type="control_port"))
    assert Onion.get_tor_socks_proxy(onion) == ("tcp", "127.0.0.1", 9050)


@pytest.mark.parametrize("key", ["socket_file_path", "socks_socket_path"])
def test_socket_paths_validated_before_controller_connection(key):
    onion = Mock()
    with pytest.raises(TorErrorInvalidSetting, match="requires both"):
        Onion.connect(
            onion, custom_settings=settings(connection_type="socket_file", **{key: ""})
        )
    assert onion.c is None


def test_invalid_upstream_proxy_rejected_before_tor_start():
    onion = Mock()
    with pytest.raises(TorErrorInvalidSetting, match="port between"):
        Onion.connect(onion, custom_settings=settings(proxy_port=0))
    onion.common.build_tor_dir.assert_not_called()
