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

    @pytest.mark.skipif(sys.platform != "Darwin", reason="requires Darwin")
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
