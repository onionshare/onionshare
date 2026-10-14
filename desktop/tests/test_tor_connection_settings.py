import sys
from unittest.mock import patch

from PySide6 import QtWidgets
import pytest

from onionshare.gui_common import GuiCommon
from onionshare.tor_settings_tab import TorSettingsTab
from onionshare_cli.onion import TorErrorInvalidSetting


@pytest.fixture
def settings_tab():
    common = sys.onionshare_common
    old_gui = getattr(common, "gui", None)
    # Only inspect/save field values; these tests never start a Tor process.
    with patch.object(GuiCommon, "get_tor_paths", return_value=("/unused",) * 7):
        common.gui = GuiCommon(common, sys.onionshare_qtapp, local_only=True)
        status = QtWidgets.QStatusBar()
        tab = TorSettingsTab(common, 0, False, status)
        tab.bridge_use_checkbox.setChecked(False)
        yield tab
        tab.deleteLater()
        common.gui = old_gui


def test_socket_mode_requires_both_visible_paths(settings_tab):
    tab = settings_tab
    tab.connection_type_socket_file_radio.setChecked(True)
    assert not tab.connection_type_socks_socket.isHidden()
    assert tab.connection_type_socks.isHidden()
    tab.connection_type_socket_file_extras_path.setText("/run/tor/control")
    tab.connection_type_socks_socket_path.setText("")
    assert tab.settings_from_fields() is False
    assert "both" in tab.error_label.text()
    tab.connection_type_socks_socket_path.setText("/run/tor/socks")
    settings = tab.settings_from_fields()
    assert settings.get("connection_type") == "socket_file"
    assert settings.get("socks_socket_path") == "/run/tor/socks"


def test_tcp_mode_has_all_fields_and_ignores_empty_socket(settings_tab):
    tab = settings_tab
    tab.connection_type_control_port_radio.setChecked(True)
    assert not tab.connection_type_control_port_extras.isHidden()
    assert not tab.connection_type_socks.isHidden()
    assert tab.connection_type_socks_socket.isHidden()
    tab.connection_type_socks_socket_path.setText("")
    tab.connection_type_socks_port.setText("12345")
    settings = tab.settings_from_fields()
    assert settings.get("connection_type") == "control_port"
    assert settings.get("socks_port") == 12345
    assert tab.proxy_group.isHidden()


def test_bundled_upstream_proxy_validation_and_auth_fields(settings_tab):
    tab = settings_tab
    tab.connection_type_bundled_radio.setChecked(True)
    assert not tab.proxy_group.isHidden()
    tab.proxy_use_checkbox.setChecked(True)
    tab.proxy_type_combobox.setCurrentIndex(tab.proxy_type_combobox.findData("socks5"))
    tab.proxy_address.setText("127.0.0.1")
    tab.proxy_port.setText("")
    assert tab.settings_from_fields() is False
    tab.proxy_port.setText("1080")
    tab.proxy_username.setText("user")
    tab.proxy_password.setText("")
    assert tab.settings_from_fields() is False
    tab.proxy_password.setText("password")
    assert tab.settings_from_fields().get("proxy_enabled") is True
    tab.proxy_type_combobox.setCurrentIndex(tab.proxy_type_combobox.findData("socks4"))
    assert tab.proxy_credentials.isHidden()
    assert tab.settings_from_fields() is not False
    tab.proxy_type_combobox.setCurrentIndex(tab.proxy_type_combobox.findData("http"))
    assert not tab.proxy_credentials.isHidden()
    assert tab.proxy_username.text() == "user"
    assert tab.proxy_password.text() == "password"
    tab.proxy_type_combobox.setCurrentIndex(tab.proxy_type_combobox.findData("socks5"))
    assert not tab.proxy_credentials.isHidden()


def test_connection_errors_include_actionable_detail(settings_tab):
    message = settings_tab.common.gui.get_translated_tor_error(
        TorErrorInvalidSetting("Supply both socket paths")
    )
    assert "Supply both socket paths" in message
