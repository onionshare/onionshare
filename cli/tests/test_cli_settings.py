import json
import os
import tempfile
import sys

import pytest

from onionshare_cli import common, settings


@pytest.fixture
def settings_obj(sys_onionshare_dev_mode, platform_linux):
    _common = common.Common()
    _common.version = "DUMMY_VERSION_1.2.3"
    return settings.Settings(_common)


class TestSettings:
    def test_init(self, settings_obj):
        expected_settings = {
            "version": "DUMMY_VERSION_1.2.3",
            "connection_type": "bundled",
            "control_port_address": "127.0.0.1",
            "control_port_port": 9051,
            "socks_address": "127.0.0.1",
            "socks_port": 9050,
            "socket_file_path": "/var/run/tor/control",
            "cookie_auth_file": "/run/tor/control.authcookie",
            "auth_type": "no_auth",
            "auth_password": "",
            "use_autoupdate": True,
            "autoupdate_timestamp": None,
            "bridges_enabled": False,
            "bridges_type": "built-in",
            "bridges_builtin_pt": "obfs4",
            "bridges_moat": "",
            "bridges_custom": "",
            "bridges_builtin": {},
            "persistent_tabs": [],
            "theme": 0,
            "auto_connect": False,
        }
        for key in settings_obj._settings:
            # Skip locale, it will not always default to the same thing
            if key != "locale":
                assert settings_obj._settings[key] == settings_obj.default_settings[key]
                assert settings_obj._settings[key] == expected_settings[key]

    def test_fill_in_defaults(self, settings_obj):
        del settings_obj._settings["version"]
        settings_obj.fill_in_defaults()
        assert settings_obj._settings["version"] == "DUMMY_VERSION_1.2.3"

    def test_load(self, temp_dir, settings_obj):
        custom_settings = {
            "version": "CUSTOM_VERSION",
            "socks_port": 9999,
            "use_stealth": True,
        }
        tmp_file, tmp_file_path = tempfile.mkstemp(dir=temp_dir.name)
        with open(tmp_file, "w") as f:
            json.dump(custom_settings, f)
        settings_obj.filename = tmp_file_path
        settings_obj.load()

        assert settings_obj._settings["version"] == "CUSTOM_VERSION"
        assert settings_obj._settings["socks_port"] == 9999
        assert settings_obj._settings["use_stealth"] is True

        os.remove(tmp_file_path)
        assert os.path.exists(tmp_file_path) is False

    def test_save(self, monkeypatch, temp_dir, settings_obj):
        settings_filename = "default_settings.json"
        new_temp_dir = tempfile.mkdtemp(dir=temp_dir.name)
        settings_path = os.path.join(new_temp_dir, settings_filename)
        settings_obj.filename = settings_path
        settings_obj.save()
        with open(settings_path, "r") as f:
            settings = json.load(f)

        assert settings_obj._settings == settings

        os.remove(settings_path)
        assert os.path.exists(settings_path) is False

    def test_get(self, settings_obj):
        assert settings_obj.get("version") == "DUMMY_VERSION_1.2.3"
        assert settings_obj.get("connection_type") == "bundled"
        assert settings_obj.get("control_port_address") == "127.0.0.1"
        assert settings_obj.get("control_port_port") == 9051
        assert settings_obj.get("socks_address") == "127.0.0.1"
        assert settings_obj.get("socks_port") == 9050
        assert settings_obj.get("socket_file_path") == "/var/run/tor/control"
        assert settings_obj.get("auth_type") == "no_auth"
        assert settings_obj.get("auth_password") == ""
        assert settings_obj.get("use_autoupdate") is True
        assert settings_obj.get("autoupdate_timestamp") is None
        assert settings_obj.get("autoupdate_timestamp") is None
        assert settings_obj.get("bridges_enabled") is False
        assert settings_obj.get("bridges_type") == "built-in"
        assert settings_obj.get("bridges_builtin_pt") == "obfs4"
        assert settings_obj.get("bridges_moat") == ""
        assert settings_obj.get("bridges_custom") == ""

    def test_set_version(self, settings_obj):
        settings_obj.set("version", "CUSTOM_VERSION")
        assert settings_obj._settings["version"] == "CUSTOM_VERSION"

    def test_set_control_port_port(self, settings_obj):
        settings_obj.set("control_port_port", 999)
        assert settings_obj._settings["control_port_port"] == 999

        settings_obj.set("control_port_port", "NON_INTEGER")
        assert settings_obj._settings["control_port_port"] == 9051

    def test_set_socks_port(self, settings_obj):
        settings_obj.set("socks_port", 888)
        assert settings_obj._settings["socks_port"] == 888

        settings_obj.set("socks_port", "NON_INTEGER")
        assert settings_obj._settings["socks_port"] == 9050

    @pytest.mark.skipif(sys.platform != "darwin", reason="requires Darwin")
    def test_filename_darwin(self, monkeypatch, platform_darwin):
        obj = settings.Settings(common.Common())
        assert obj.filename == os.path.expanduser(
            "~/Library/Application Support/OnionShare-testdata/onionshare.json"
        )

    @pytest.mark.skipif(sys.platform != "linux", reason="requires Linux")
    def test_filename_linux(self, monkeypatch, platform_linux):
        obj = settings.Settings(common.Common())
        assert obj.filename == os.path.expanduser(
            "~/.config/onionshare-testdata/onionshare.json"
        )

    @pytest.mark.skipif(sys.platform != "win32", reason="requires Windows")
    def test_filename_windows(self, monkeypatch, platform_windows):
        obj = settings.Settings(common.Common())
        assert obj.filename == os.path.expanduser(
            "~\\AppData\\Roaming\\OnionShare-testdata\\onionshare.json"
        )

    def test_set_custom_bridge(self, settings_obj):
        settings_obj.set(
            "bridges_custom",
            "Bridge 45.3.20.65:9050 21300AD88890A49C429A6CB9959CFD44490A8F6E",
        )
        assert (
            settings_obj._settings["bridges_custom"]
            == "Bridge 45.3.20.65:9050 21300AD88890A49C429A6CB9959CFD44490A8F6E"
        )

    def test_set_webtunnel_builtin_pt(self, settings_obj):
        """bridges_builtin_pt accepts 'webtunnel' as a valid value."""
        settings_obj.set("bridges_builtin_pt", "webtunnel")
        assert settings_obj.get("bridges_builtin_pt") == "webtunnel"

    def test_check_bridges_valid_webtunnel(self, settings_obj):
        """
        check_bridges_valid must accept WebTunnel bridge lines.
        WebTunnel bridge format: webtunnel <IP>:<port> <fingerprint> url=https://...
        """
        _common = settings_obj.common
        valid = _common.check_bridges_valid([
            "webtunnel 192.0.2.42:443 D965164C1D9FB4FDD92E4FD5CDC6005E7820A687 url=https://example.com/secret-path",
        ])
        assert valid, "A well-formed webtunnel bridge line should be accepted"

    def test_check_bridges_valid_webtunnel_rejects_bad(self, settings_obj):
        """check_bridges_valid must reject malformed webtunnel bridge lines."""
        _common = settings_obj.common
        # Missing the required url= parameter
        result = _common.check_bridges_valid([
            "webtunnel 192.0.2.42:443 D965164C1D9FB4FDD92E4FD5CDC6005E7820A687",
        ])
        assert not result, "A webtunnel line without url= should be rejected"

    def test_env_override_string(self, monkeypatch, temp_dir, settings_obj):
        settings_obj.filename = os.path.join(temp_dir.name, "nonexistent.json")
        monkeypatch.setenv("ONIONSHARE_CONNECTION_TYPE", "control_port")
        settings_obj.load()
        assert settings_obj.get("connection_type") == "control_port"

    def test_env_override_int(self, monkeypatch, temp_dir, settings_obj):
        settings_obj.filename = os.path.join(temp_dir.name, "nonexistent.json")
        monkeypatch.setenv("ONIONSHARE_SOCKS_PORT", "9999")
        settings_obj.load()
        assert settings_obj.get("socks_port") == 9999
        assert isinstance(settings_obj.get("socks_port"), int)

    @pytest.mark.parametrize("value", ["1", "true", "TRUE", "yes", "on"])
    def test_env_override_bool_true(self, monkeypatch, temp_dir, settings_obj, value):
        settings_obj.filename = os.path.join(temp_dir.name, "nonexistent.json")
        monkeypatch.setenv("ONIONSHARE_AUTO_CONNECT", value)
        settings_obj.load()
        assert settings_obj.get("auto_connect") is True

    @pytest.mark.parametrize("value", ["0", "false", "FALSE", "no", "off"])
    def test_env_override_bool_false(self, monkeypatch, temp_dir, settings_obj, value):
        settings_obj.filename = os.path.join(temp_dir.name, "nonexistent.json")
        settings_obj.set("auto_connect", True)
        monkeypatch.setenv("ONIONSHARE_AUTO_CONNECT", value)
        settings_obj.load()
        assert settings_obj.get("auto_connect") is False

    def test_env_override_json_list(self, monkeypatch, temp_dir, settings_obj):
        settings_obj.filename = os.path.join(temp_dir.name, "nonexistent.json")
        monkeypatch.setenv("ONIONSHARE_PERSISTENT_TABS", '["tab1", "tab2"]')
        settings_obj.load()
        assert settings_obj.get("persistent_tabs") == ["tab1", "tab2"]

    def test_env_override_json_dict(self, monkeypatch, temp_dir, settings_obj):
        settings_obj.filename = os.path.join(temp_dir.name, "nonexistent.json")
        monkeypatch.setenv("ONIONSHARE_BRIDGES_BUILTIN", '{"obfs4": []}')
        settings_obj.load()
        assert settings_obj.get("bridges_builtin") == {"obfs4": []}

    def test_env_override_invalid_int_falls_back(
        self, monkeypatch, temp_dir, settings_obj
    ):
        settings_obj.filename = os.path.join(temp_dir.name, "nonexistent.json")
        monkeypatch.setenv("ONIONSHARE_SOCKS_PORT", "not-an-int")
        settings_obj.load()
        assert settings_obj.get("socks_port") == 9050

    def test_env_override_invalid_bool_falls_back(
        self, monkeypatch, temp_dir, settings_obj
    ):
        settings_obj.filename = os.path.join(temp_dir.name, "nonexistent.json")
        monkeypatch.setenv("ONIONSHARE_AUTO_CONNECT", "maybe")
        settings_obj.load()
        assert settings_obj.get("auto_connect") is False

    def test_env_override_invalid_json_falls_back(
        self, monkeypatch, temp_dir, settings_obj
    ):
        settings_obj.filename = os.path.join(temp_dir.name, "nonexistent.json")
        monkeypatch.setenv("ONIONSHARE_PERSISTENT_TABS", "not json")
        settings_obj.load()
        assert settings_obj.get("persistent_tabs") == []

    def test_env_override_wrong_json_type_falls_back(
        self, monkeypatch, temp_dir, settings_obj
    ):
        settings_obj.filename = os.path.join(temp_dir.name, "nonexistent.json")
        monkeypatch.setenv("ONIONSHARE_PERSISTENT_TABS", '{"not": "a list"}')
        settings_obj.load()
        assert settings_obj.get("persistent_tabs") == []

    def test_env_override_takes_precedence_over_file(
        self, monkeypatch, temp_dir, settings_obj
    ):
        settings_file = os.path.join(temp_dir.name, "settings.json")
        with open(settings_file, "w") as f:
            json.dump({"socks_port": 9999}, f)
        settings_obj.filename = settings_file
        monkeypatch.setenv("ONIONSHARE_SOCKS_PORT", "8888")
        settings_obj.load()
        assert settings_obj.get("socks_port") == 8888

    def test_env_override_not_persisted_on_save(
        self, monkeypatch, temp_dir, settings_obj
    ):
        settings_file = os.path.join(temp_dir.name, "settings.json")
        settings_obj.filename = settings_file
        monkeypatch.setenv("ONIONSHARE_AUTH_PASSWORD", "hunter2")
        settings_obj.load()
        assert settings_obj.get("auth_password") == "hunter2"
        settings_obj.save()
        with open(settings_file, "r") as f:
            saved = json.load(f)
        # The secret must not have been written to disk
        assert saved["auth_password"] == ""

    def test_env_override_cleared_by_set(self, monkeypatch, temp_dir, settings_obj):
        settings_obj.filename = os.path.join(temp_dir.name, "nonexistent.json")
        monkeypatch.setenv("ONIONSHARE_SOCKS_PORT", "8888")
        settings_obj.load()
        assert settings_obj.get("socks_port") == 8888
        settings_obj.set("socks_port", 7777)
        assert settings_obj.get("socks_port") == 7777

    def test_env_override_same_value_set_not_persisted(
        self, monkeypatch, temp_dir, settings_obj
    ):
        # The desktop settings dialog sets every field when saving; setting a
        # value identical to the environment override must not write it to disk.
        settings_file = os.path.join(temp_dir.name, "settings.json")
        settings_obj.filename = settings_file
        monkeypatch.setenv("ONIONSHARE_AUTH_PASSWORD", "hunter2")
        settings_obj.load()
        settings_obj.set("auth_password", "hunter2")
        settings_obj.save()
        with open(settings_file, "r") as f:
            saved = json.load(f)
        assert saved["auth_password"] == ""
        # The override is still in effect for this session
        assert settings_obj.get("auth_password") == "hunter2"

    def test_env_override_version_ignored(self, monkeypatch, temp_dir, settings_obj):
        settings_obj.filename = os.path.join(temp_dir.name, "nonexistent.json")
        monkeypatch.setenv("ONIONSHARE_VERSION", "9.9.9")
        settings_obj.load()
        assert settings_obj.get("version") == "DUMMY_VERSION_1.2.3"

    def test_env_override_unknown_setting_ignored(
        self, monkeypatch, temp_dir, settings_obj
    ):
        settings_obj.filename = os.path.join(temp_dir.name, "nonexistent.json")
        monkeypatch.setenv("ONIONSHARE_NOT_A_REAL_SETTING", "whatever")
        settings_obj.load()
        assert "not_a_real_setting" not in settings_obj._env_overrides

    def test_tor_env_host_and_port(self, monkeypatch, temp_dir, settings_obj):
        settings_obj.filename = os.path.join(temp_dir.name, "nonexistent.json")
        monkeypatch.setenv("TOR_CONTROL_HOST", "10.0.0.2")
        monkeypatch.setenv("TOR_CONTROL_PORT", "9151")
        settings_obj.load()
        assert settings_obj.get("control_port_address") == "10.0.0.2"
        assert settings_obj.get("control_port_port") == 9151

    def test_tor_env_passwd_implies_password_auth(
        self, monkeypatch, temp_dir, settings_obj
    ):
        settings_obj.filename = os.path.join(temp_dir.name, "nonexistent.json")
        monkeypatch.setenv("TOR_CONTROL_PASSWD", "hunter2")
        settings_obj.load()
        assert settings_obj.get("auth_password") == "hunter2"
        assert settings_obj.get("auth_type") == "password"

    def test_tor_env_cookie_auth_file(self, monkeypatch, temp_dir, settings_obj):
        settings_obj.filename = os.path.join(temp_dir.name, "nonexistent.json")
        monkeypatch.setenv("TOR_CONTROL_COOKIE_AUTH_FILE", "/tmp/my.cookie")
        settings_obj.load()
        assert settings_obj.get("cookie_auth_file") == "/tmp/my.cookie"

    def test_tor_env_overrides_file(self, monkeypatch, temp_dir, settings_obj):
        settings_file = os.path.join(temp_dir.name, "settings.json")
        with open(settings_file, "w") as f:
            json.dump({"control_port_port": 9999}, f)
        settings_obj.filename = settings_file
        monkeypatch.setenv("TOR_CONTROL_PORT", "1234")
        settings_obj.load()
        assert settings_obj.get("control_port_port") == 1234

    def test_tor_env_lower_precedence_than_onionshare(
        self, monkeypatch, temp_dir, settings_obj
    ):
        settings_obj.filename = os.path.join(temp_dir.name, "nonexistent.json")
        monkeypatch.setenv("TOR_CONTROL_HOST", "10.0.0.2")
        monkeypatch.setenv("ONIONSHARE_CONTROL_PORT_ADDRESS", "10.0.0.3")
        settings_obj.load()
        assert settings_obj.get("control_port_address") == "10.0.0.3"

    def test_tor_env_invalid_port_falls_back(self, monkeypatch, temp_dir, settings_obj):
        settings_obj.filename = os.path.join(temp_dir.name, "nonexistent.json")
        monkeypatch.setenv("TOR_CONTROL_PORT", "not-an-int")
        settings_obj.load()
        assert settings_obj.get("control_port_port") == 9051

    def test_tor_env_not_persisted_on_save(self, monkeypatch, temp_dir, settings_obj):
        settings_file = os.path.join(temp_dir.name, "settings.json")
        settings_obj.filename = settings_file
        monkeypatch.setenv("TOR_CONTROL_PASSWD", "hunter2")
        settings_obj.load()
        settings_obj.save()
        with open(settings_file, "r") as f:
            saved = json.load(f)
        assert saved["auth_password"] == ""
        assert saved["auth_type"] == "no_auth"

    def test_every_setting_has_an_env_var(self, monkeypatch, temp_dir, settings_obj):
        """Every onionshare.json parameter except version can be set via env."""
        raws = {
            bool: "true",
            int: "123",
            dict: '{"x": 1}',
            list: '["x"]',
            str: "envtest",
        }
        settings_obj.filename = os.path.join(temp_dir.name, "nonexistent.json")
        for key, default in settings_obj.default_settings.items():
            if key == "version":
                continue
            raw = raws[settings.ENV_SETTING_TYPES.get(key, type(default))]
            monkeypatch.setenv(f"ONIONSHARE_{key.upper()}", raw)
            settings_obj.load()
            assert settings_obj.get(key) == settings_obj._parse_env_value(key, raw), key

    def test_tor_env_host_selects_control_port(
        self, monkeypatch, temp_dir, settings_obj
    ):
        settings_obj.filename = os.path.join(temp_dir.name, "nonexistent.json")
        monkeypatch.setenv("TOR_CONTROL_HOST", "10.0.0.2")
        settings_obj.load()
        assert settings_obj.get("connection_type") == "control_port"

    def test_tor_env_passwd_selects_control_port(
        self, monkeypatch, temp_dir, settings_obj
    ):
        settings_obj.filename = os.path.join(temp_dir.name, "nonexistent.json")
        monkeypatch.setenv("TOR_CONTROL_PASSWD", "hunter2")
        settings_obj.load()
        assert settings_obj.get("connection_type") == "control_port"

    def test_tor_env_port_alone_keeps_connection_type(
        self, monkeypatch, temp_dir, settings_obj
    ):
        # TOR_CONTROL_PORT is also used by the "automatic" connection type
        settings_obj.filename = os.path.join(temp_dir.name, "nonexistent.json")
        monkeypatch.setenv("TOR_CONTROL_PORT", "9151")
        settings_obj.load()
        assert settings_obj.get("connection_type") == "bundled"

    def test_tor_env_onionshare_connection_type_wins(
        self, monkeypatch, temp_dir, settings_obj
    ):
        settings_obj.filename = os.path.join(temp_dir.name, "nonexistent.json")
        monkeypatch.setenv("TOR_CONTROL_HOST", "10.0.0.2")
        monkeypatch.setenv("ONIONSHARE_CONNECTION_TYPE", "socket_file")
        settings_obj.load()
        assert settings_obj.get("connection_type") == "socket_file"

    def test_tor_env_host_overrides_file_connection_type(
        self, monkeypatch, temp_dir, settings_obj
    ):
        settings_file = os.path.join(temp_dir.name, "settings.json")
        with open(settings_file, "w") as f:
            json.dump({"connection_type": "socket_file"}, f)
        settings_obj.filename = settings_file
        monkeypatch.setenv("TOR_CONTROL_HOST", "10.0.0.2")
        settings_obj.load()
        assert settings_obj.get("connection_type") == "control_port"
