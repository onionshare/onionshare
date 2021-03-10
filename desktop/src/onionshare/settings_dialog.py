# -*- coding: utf-8 -*-
"""
OnionShare | https://onionshare.org/

Copyright (C) 2014-2021 Micah Lee, et al. <micah@micahflee.com>

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

from PySide2 import QtCore, QtWidgets, QtGui
import sys
import platform
import datetime
import re
import os
from onionshare_cli.settings import Settings
from onionshare_cli.onion import (
    Onion,
    TorErrorInvalidSetting,
    TorErrorAutomatic,
    TorErrorSocketPort,
    TorErrorSocketFile,
    TorErrorMissingPassword,
    TorErrorUnreadableCookieFile,
    TorErrorAuthError,
    TorErrorProtocolError,
    BundledTorTimeout,
    BundledTorBroken,
    TorTooOldEphemeral,
    TorTooOldStealth,
    PortNotAvailable,
)

from . import strings
from .widgets import Alert
from .update_checker import (
    UpdateThread)
from .tor_connection_dialog import TorConnectionDialog
from .gui_common import GuiCommon


class SettingsDialog(QtWidgets.QDialog):
    """
    Settings dialog.
    """

    settings_saved = QtCore.Signal()

    def __init__(self, common):
        super(SettingsDialog, self).__init__()

        self.common = common

        self.common.log("SettingsDialog", "__init__")

        self.setModal(True)
        self.setWindowTitle(strings._("gui_settings_window_title"))
        self.setWindowIcon(QtGui.QIcon(GuiCommon.get_resource_path("images/logo.png")))

        self.system = platform.system()

        # If ONIONSHARE_HIDE_TOR_SETTINGS=1, hide Tor settings in the dialog
        self.hide_tor_settings = os.environ.get("ONIONSHARE_HIDE_TOR_SETTINGS") == "1"

        # Automatic updates options

        # Autoupdate
        self.autoupdate_checkbox = QtWidgets.QCheckBox()
        self.autoupdate_checkbox.setCheckState(QtCore.Qt.Unchecked)
        self.autoupdate_checkbox.setText(strings._("gui_settings_autoupdate_option"))

        # Last update time
        self.autoupdate_timestamp = QtWidgets.QLabel()

        # Check for updates button
        self.check_for_updates_button = QtWidgets.QPushButton(
            strings._("gui_settings_autoupdate_check_button")
        )
        self.check_for_updates_button.clicked.connect(self.check_for_updates)
        # We can't check for updates if not connected to Tor
        if not self.common.gui.onion.connected_to_tor:
            self.check_for_updates_button.setEnabled(False)

        # Autoupdate options layout
        autoupdate_group_layout = QtWidgets.QVBoxLayout()
        autoupdate_group_layout.addWidget(self.autoupdate_checkbox)
        autoupdate_group_layout.addWidget(self.autoupdate_timestamp)
        autoupdate_group_layout.addWidget(self.check_for_updates_button)
        autoupdate_group = QtWidgets.QGroupBox(
            strings._("gui_settings_autoupdate_label")
        )
        autoupdate_group.setLayout(autoupdate_group_layout)

        # Autoupdate is only available for Windows and Mac (Linux updates using package manager)
        if self.system != "Windows" and self.system != "Darwin":
            autoupdate_group.hide()

        # Language settings
        language_label = QtWidgets.QLabel(strings._("gui_settings_language_label"))
        self.language_combobox = QtWidgets.QComboBox()
        # Populate the dropdown with all of OnionShare's available languages
        language_names_to_locales = {
            v: k for k, v in self.common.settings.available_locales.items()
        }
        language_names = list(language_names_to_locales)
        language_names.sort()
        for language_name in language_names:
            locale = language_names_to_locales[language_name]
            self.language_combobox.addItem(language_name, locale)
        language_layout = QtWidgets.QHBoxLayout()
        language_layout.addWidget(language_label)
        language_layout.addWidget(self.language_combobox)
        language_layout.addStretch()

        # Connection type: either automatic, control port, or socket file

        # Bundled Tor
        self.connection_type_bundled_radio = QtWidgets.QRadioButton(
            strings._("gui_settings_connection_type_bundled_option")
        )
        self.connection_type_bundled_radio.toggled.connect(
            self.connection_type_bundled_toggled
        )

        # Bundled Tor doesn't work on dev mode in Windows or Mac
        if (self.system == "Windows" or self.system == "Darwin") and getattr(
            sys, "onionshare_dev_mode", False
        ):
            self.connection_type_bundled_radio.setEnabled(False)

        # Bridge options for bundled tor

        # No bridges option radio
        self.tor_bridges_no_bridges_radio = QtWidgets.QRadioButton(
            strings._("gui_settings_tor_bridges_no_bridges_radio_option")
        )
        self.tor_bridges_no_bridges_radio.toggled.connect(
            self.tor_bridges_no_bridges_radio_toggled
        )

        # obfs4 option radio
        # if the obfs4proxy binary is missing, we can't use obfs4 transports
        (
            self.tor_path,
            self.tor_geo_ip_file_path,
            self.tor_geo_ipv6_file_path,
            self.obfs4proxy_file_path,
        ) = self.common.gui.get_tor_paths()
        if not self.obfs4proxy_file_path or not os.path.isfile(
            self.obfs4proxy_file_path
        ):
            self.tor_bridges_use_obfs4_radio = QtWidgets.QRadioButton(
                strings._("gui_settings_tor_bridges_obfs4_radio_option_no_obfs4proxy")
            )
            self.tor_bridges_use_obfs4_radio.setEnabled(False)
        else:
            self.tor_bridges_use_obfs4_radio = QtWidgets.QRadioButton(
                strings._("gui_settings_tor_bridges_obfs4_radio_option")
            )
        self.tor_bridges_use_obfs4_radio.toggled.connect(
            self.tor_bridges_use_obfs4_radio_toggled
        )

        # meek_lite-azure option radio
        # if the obfs4proxy binary is missing, we can't use meek_lite-azure transports
        (
            self.tor_path,
            self.tor_geo_ip_file_path,
            self.tor_geo_ipv6_file_path,
            self.obfs4proxy_file_path,
        ) = self.common.gui.get_tor_paths()
        if not self.obfs4proxy_file_path or not os.path.isfile(
            self.obfs4proxy_file_path
        ):
            self.tor_bridges_use_meek_lite_azure_radio = QtWidgets.QRadioButton(
                strings._(
                    "gui_settings_tor_bridges_meek_lite_azure_radio_option_no_obfs4proxy"
                )
            )
            self.tor_bridges_use_meek_lite_azure_radio.setEnabled(False)
        else:
            self.tor_bridges_use_meek_lite_azure_radio = QtWidgets.QRadioButton(
                strings._("gui_settings_tor_bridges_meek_lite_azure_radio_option")
            )
        self.tor_bridges_use_meek_lite_azure_radio.toggled.connect(
            self.tor_bridges_use_meek_lite_azure_radio_toggled
        )

        # Custom bridges radio and textbox
        self.tor_bridges_use_custom_radio = QtWidgets.QRadioButton(
            strings._("gui_settings_tor_bridges_custom_radio_option")
        )
        self.tor_bridges_use_custom_radio.toggled.connect(
            self.tor_bridges_use_custom_radio_toggled
        )

        self.tor_bridges_use_custom_label = QtWidgets.QLabel(
            strings._("gui_settings_tor_bridges_custom_label")
        )
        self.tor_bridges_use_custom_label.setTextInteractionFlags(
            QtCore.Qt.TextBrowserInteraction
        )
        self.tor_bridges_use_custom_label.setOpenExternalLinks(True)
        self.tor_bridges_use_custom_textbox = QtWidgets.QPlainTextEdit()
        self.tor_bridges_use_custom_textbox.setMaximumHeight(200)
        self.tor_bridges_use_custom_textbox.setPlaceholderText(
            "[address:port] [identifier]"
        )

        tor_bridges_use_custom_textbox_options_layout = QtWidgets.QVBoxLayout()
        tor_bridges_use_custom_textbox_options_layout.addWidget(
            self.tor_bridges_use_custom_label
        )
        tor_bridges_use_custom_textbox_options_layout.addWidget(
            self.tor_bridges_use_custom_textbox
        )

        self.tor_bridges_use_custom_textbox_options = QtWidgets.QWidget()
        self.tor_bridges_use_custom_textbox_options.setLayout(
            tor_bridges_use_custom_textbox_options_layout
        )
        self.tor_bridges_use_custom_textbox_options.hide()

        # Bridges layout/widget
        bridges_layout = QtWidgets.QVBoxLayout()
        bridges_layout.addWidget(self.tor_bridges_no_bridges_radio)
        bridges_layout.addWidget(self.tor_bridges_use_obfs4_radio)
        bridges_layout.addWidget(self.tor_bridges_use_meek_lite_azure_radio)
        bridges_layout.addWidget(self.tor_bridges_use_custom_radio)
        bridges_layout.addWidget(self.tor_bridges_use_custom_textbox_options)

        self.bridges = QtWidgets.QWidget()
        self.bridges.setLayout(bridges_layout)

        # Automatic
        self.connection_type_automatic_radio = QtWidgets.QRadioButton(
            strings._("gui_settings_connection_type_automatic_option")
        )
        self.connection_type_automatic_radio.toggled.connect(
            self.connection_type_automatic_toggled
        )

        # Control port
        self.connection_type_control_port_radio = QtWidgets.QRadioButton(
            strings._("gui_settings_connection_type_control_port_option")
        )
        self.connection_type_control_port_radio.toggled.connect(
            self.connection_type_control_port_toggled
        )

        connection_type_control_port_extras_label = QtWidgets.QLabel(
            strings._("gui_settings_control_port_label")
        )
        self.connection_type_control_port_extras_address = QtWidgets.QLineEdit()
        self.connection_type_control_port_extras_port = QtWidgets.QLineEdit()
        connection_type_control_port_extras_layout = QtWidgets.QHBoxLayout()
        connection_type_control_port_extras_layout.addWidget(
            connection_type_control_port_extras_label
        )
        connection_type_control_port_extras_layout.addWidget(
            self.connection_type_control_port_extras_address
        )
        connection_type_control_port_extras_layout.addWidget(
            self.connection_type_control_port_extras_port
        )

        self.connection_type_control_port_extras = QtWidgets.QWidget()
        self.connection_type_control_port_extras.setLayout(
            connection_type_control_port_extras_layout
        )
        self.connection_type_control_port_extras.hide()

        # Socket file
        self.connection_type_socket_file_radio = QtWidgets.QRadioButton(
            strings._("gui_settings_connection_type_socket_file_option")
        )
        self.connection_type_socket_file_radio.toggled.connect(
            self.connection_type_socket_file_toggled
        )

        connection_type_socket_file_extras_label = QtWidgets.QLabel(
            strings._("gui_settings_socket_file_label")
        )
        self.connection_type_socket_file_extras_path = QtWidgets.QLineEdit()
        connection_type_socket_file_extras_layout = QtWidgets.QHBoxLayout()
        connection_type_socket_file_extras_layout.addWidget(
            connection_type_socket_file_extras_label
        )
        connection_type_socket_file_extras_layout.addWidget(
            self.connection_type_socket_file_extras_path
        )

        self.connection_type_socket_file_extras = QtWidgets.QWidget()
        self.connection_type_socket_file_extras.setLayout(
            connection_type_socket_file_extras_layout
        )
        self.connection_type_socket_file_extras.hide()

        # Tor SOCKS address and port
        gui_settings_socks_label = QtWidgets.QLabel(
            strings._("gui_settings_socks_label")
        )
        self.connection_type_socks_address = QtWidgets.QLineEdit()
        self.connection_type_socks_port = QtWidgets.QLineEdit()
        connection_type_socks_layout = QtWidgets.QHBoxLayout()
        connection_type_socks_layout.addWidget(gui_settings_socks_label)
        connection_type_socks_layout.addWidget(self.connection_type_socks_address)
        connection_type_socks_layout.addWidget(self.connection_type_socks_port)

        self.connection_type_socks = QtWidgets.QWidget()
        self.connection_type_socks.setLayout(connection_type_socks_layout)
        self.connection_type_socks.hide()

        # Authentication options

        # No authentication
        self.authenticate_no_auth_radio = QtWidgets.QRadioButton(
            strings._("gui_settings_authenticate_no_auth_option")
        )
        self.authenticate_no_auth_radio.toggled.connect(
            self.authenticate_no_auth_toggled
        )

        # Password
        self.authenticate_password_radio = QtWidgets.QRadioButton(
            strings._("gui_settings_authenticate_password_option")
        )
        self.authenticate_password_radio.toggled.connect(
            self.authenticate_password_toggled
        )

        authenticate_password_extras_label = QtWidgets.QLabel(
            strings._("gui_settings_password_label")
        )
        self.authenticate_password_extras_password = QtWidgets.QLineEdit("")
        authenticate_password_extras_layout = QtWidgets.QHBoxLayout()
        authenticate_password_extras_layout.addWidget(
            authenticate_password_extras_label
        )
        authenticate_password_extras_layout.addWidget(
            self.authenticate_password_extras_password
        )

        self.authenticate_password_extras = QtWidgets.QWidget()
        self.authenticate_password_extras.setLayout(authenticate_password_extras_layout)
        self.authenticate_password_extras.hide()

        # Authentication options layout
        authenticate_group_layout = QtWidgets.QVBoxLayout()
        authenticate_group_layout.addWidget(self.authenticate_no_auth_radio)
        authenticate_group_layout.addWidget(self.authenticate_password_radio)
        authenticate_group_layout.addWidget(self.authenticate_password_extras)
        self.authenticate_group = QtWidgets.QGroupBox(
            strings._("gui_settings_authenticate_label")
        )
        self.authenticate_group.setLayout(authenticate_group_layout)

        # Put the radios into their own group so they are exclusive
        connection_type_radio_group_layout = QtWidgets.QVBoxLayout()
        connection_type_radio_group_layout.addWidget(self.connection_type_bundled_radio)
        connection_type_radio_group_layout.addWidget(
            self.connection_type_automatic_radio
        )
        connection_type_radio_group_layout.addWidget(
            self.connection_type_control_port_radio
        )
        connection_type_radio_group_layout.addWidget(
            self.connection_type_socket_file_radio
        )
        connection_type_radio_group = QtWidgets.QGroupBox(
            strings._("gui_settings_connection_type_label")
        )
        connection_type_radio_group.setLayout(connection_type_radio_group_layout)

        # The Bridges options are not exclusive (enabling Bridges offers obfs4 or custom bridges)
        connection_type_bridges_radio_group_layout = QtWidgets.QVBoxLayout()
        connection_type_bridges_radio_group_layout.addWidget(self.bridges)
        self.connection_type_bridges_radio_group = QtWidgets.QGroupBox(
            strings._("gui_settings_tor_bridges")
        )
        self.connection_type_bridges_radio_group.setLayout(
            connection_type_bridges_radio_group_layout
        )
        self.connection_type_bridges_radio_group.hide()

        # Test tor settings button
        self.connection_type_test_button = QtWidgets.QPushButton(
            strings._("gui_settings_connection_type_test_button")
        )
        self.connection_type_test_button.clicked.connect(self.test_tor_clicked)
        connection_type_test_button_layout = QtWidgets.QHBoxLayout()
        connection_type_test_button_layout.addWidget(self.connection_type_test_button)
        connection_type_test_button_layout.addStretch()

        # Connection type layout
        connection_type_layout = QtWidgets.QVBoxLayout()
        connection_type_layout.addWidget(self.connection_type_control_port_extras)
        connection_type_layout.addWidget(self.connection_type_socket_file_extras)
        connection_type_layout.addWidget(self.connection_type_socks)
        connection_type_layout.addWidget(self.authenticate_group)
        connection_type_layout.addWidget(self.connection_type_bridges_radio_group)
        connection_type_layout.addLayout(connection_type_test_button_layout)

        # Buttons
        self.save_button = QtWidgets.QPushButton(strings._("gui_settings_button_save"))
        self.save_button.clicked.connect(self.save_clicked)
        self.cancel_button = QtWidgets.QPushButton(
            strings._("gui_settings_button_cancel")
        )
        self.cancel_button.clicked.connect(self.cancel_clicked)
        version_label = QtWidgets.QLabel(f"OnionShare {self.common.version}")
        version_label.setStyleSheet(self.common.gui.css["settings_version"])
        self.help_button = QtWidgets.QPushButton(strings._("gui_settings_button_help"))
        self.help_button.clicked.connect(self.help_clicked)
        buttons_layout = QtWidgets.QHBoxLayout()
        buttons_layout.addWidget(version_label)
        buttons_layout.addWidget(self.help_button)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.save_button)
        buttons_layout.addWidget(self.cancel_button)

        # Tor network connection status
        self.tor_status = QtWidgets.QLabel()
        self.tor_status.setStyleSheet(self.common.gui.css["settings_tor_status"])
        self.tor_status.hide()

        # Layout
        tor_layout = QtWidgets.QVBoxLayout()
        tor_layout.addWidget(connection_type_radio_group)
        tor_layout.addLayout(connection_type_layout)
        tor_layout.addWidget(self.tor_status)
        tor_layout.addStretch()

        layout = QtWidgets.QVBoxLayout()
        if not self.hide_tor_settings:
            layout.addLayout(tor_layout)
            layout.addSpacing(20)
        layout.addWidget(autoupdate_group)
        if autoupdate_group.isVisible():
            layout.addSpacing(20)
        layout.addLayout(language_layout)
        layout.addSpacing(20)
        layout.addStretch()
        layout.addLayout(buttons_layout)

        self.setLayout(layout)
        self.cancel_button.setFocus()

        self.reload_settings()

    def reload_settings(self):
        # Load settings, and fill them in
        self.old_settings = Settings(self.common)
        self.old_settings.load()

        use_autoupdate = self.old_settings.get("use_autoupdate")
        if use_autoupdate:
            self.autoupdate_checkbox.setCheckState(QtCore.Qt.Checked)
        else:
            self.autoupdate_checkbox.setCheckState(QtCore.Qt.Unchecked)

        autoupdate_timestamp = self.old_settings.get("autoupdate_timestamp")
        self._update_autoupdate_timestamp(autoupdate_timestamp)

        locale = self.old_settings.get("locale")
        locale_index = self.language_combobox.findData(locale)
        self.language_combobox.setCurrentIndex(locale_index)

        connection_type = self.old_settings.get("connection_type")
        if connection_type == "bundled":
            if self.connection_type_bundled_radio.isEnabled():
                self.connection_type_bundled_radio.setChecked(True)
            else:
                # If bundled tor is disabled, fallback to automatic
                self.connection_type_automatic_radio.setChecked(True)
        elif connection_type == "automatic":
            self.connection_type_automatic_radio.setChecked(True)
        elif connection_type == "control_port":
            self.connection_type_control_port_radio.setChecked(True)
        elif connection_type == "socket_file":
            self.connection_type_socket_file_radio.setChecked(True)
        self.connection_type_control_port_extras_address.setText(
            self.old_settings.get("control_port_address")
        )
        self.connection_type_control_port_extras_port.setText(
            str(self.old_settings.get("control_port_port"))
        )
        self.connection_type_socket_file_extras_path.setText(
            self.old_settings.get("socket_file_path")
        )
        self.connection_type_socks_address.setText(
            self.old_settings.get("socks_address")
        )
        self.connection_type_socks_port.setText(
            str(self.old_settings.get("socks_port"))
        )
        auth_type = self.old_settings.get("auth_type")
        if auth_type == "no_auth":
            self.authenticate_no_auth_radio.setChecked(True)
        elif auth_type == "password":
            self.authenticate_password_radio.setChecked(True)
        self.authenticate_password_extras_password.setText(
            self.old_settings.get("auth_password")
        )

        if self.old_settings.get("no_bridges"):
            self.tor_bridges_no_bridges_radio.setChecked(True)
            self.tor_bridges_use_obfs4_radio.setChecked(False)
            self.tor_bridges_use_meek_lite_azure_radio.setChecked(False)
            self.tor_bridges_use_custom_radio.setChecked(False)
        else:
            self.tor_bridges_no_bridges_radio.setChecked(False)
            self.tor_bridges_use_obfs4_radio.setChecked(
                self.old_settings.get("tor_bridges_use_obfs4")
            )
            self.tor_bridges_use_meek_lite_azure_radio.setChecked(
                self.old_settings.get("tor_bridges_use_meek_lite_azure")
            )

            if self.old_settings.get("tor_bridges_use_custom_bridges"):
                self.tor_bridges_use_custom_radio.setChecked(True)
                # Remove the 'Bridge' lines at the start of each bridge.
                # They are added automatically to provide compatibility with
                # copying/pasting bridges provided from https://bridges.torproject.org
                new_bridges = []
                bridges = self.old_settings.get("tor_bridges_use_custom_bridges").split(
                    "Bridge "
                )
                for bridge in bridges:
                    new_bridges.append(bridge)
                new_bridges = "".join(new_bridges)
                self.tor_bridges_use_custom_textbox.setPlainText(new_bridges)

    def connection_type_bundled_toggled(self, checked):
        """
        Connection type bundled was toggled. If checked, hide authentication fields.
        """
        self.common.log("SettingsDialog", "connection_type_bundled_toggled")
        if self.hide_tor_settings:
            return
        if checked:
            self.authenticate_group.hide()
            self.connection_type_socks.hide()
            self.connection_type_bridges_radio_group.show()

    def tor_bridges_no_bridges_radio_toggled(self, checked):
        """
        'No bridges' option was toggled. If checked, enable other bridge options.
        """
        if self.hide_tor_settings:
            return
        if checked:
            self.tor_bridges_use_custom_textbox_options.hide()

    def tor_bridges_use_obfs4_radio_toggled(self, checked):
        """
        obfs4 bridges option was toggled. If checked, disable custom bridge options.
        """
        if self.hide_tor_settings:
            return
        if checked:
            self.tor_bridges_use_custom_textbox_options.hide()

    def tor_bridges_use_meek_lite_azure_radio_toggled(self, checked):
        """
        meek_lite_azure bridges option was toggled. If checked, disable custom bridge options.
        """
        if self.hide_tor_settings:
            return
        if checked:
            self.tor_bridges_use_custom_textbox_options.hide()
            # Alert the user about meek's costliness if it looks like they're turning it on
            if not self.old_settings.get("tor_bridges_use_meek_lite_azure"):
                Alert(
                    self.common,
                    strings._("gui_settings_meek_lite_expensive_warning"),
                    QtWidgets.QMessageBox.Warning,
                )

    def tor_bridges_use_custom_radio_toggled(self, checked):
        """
        Custom bridges option was toggled. If checked, show custom bridge options.
        """
        if self.hide_tor_settings:
            return
        if checked:
            self.tor_bridges_use_custom_textbox_options.show()

    def connection_type_automatic_toggled(self, checked):
        """
        Connection type automatic was toggled. If checked, hide authentication fields.
        """
        self.common.log("SettingsDialog", "connection_type_automatic_toggled")
        if self.hide_tor_settings:
            return
        if checked:
            self.authenticate_group.hide()
            self.connection_type_socks.hide()
            self.connection_type_bridges_radio_group.hide()

    def connection_type_control_port_toggled(self, checked):
        """
        Connection type control port was toggled. If checked, show extra fields
        for Tor control address and port. If unchecked, hide those extra fields.
        """
        self.common.log("SettingsDialog", "connection_type_control_port_toggled")
        if self.hide_tor_settings:
            return
        if checked:
            self.authenticate_group.show()
            self.connection_type_control_port_extras.show()
            self.connection_type_socks.show()
            self.connection_type_bridges_radio_group.hide()
        else:
            self.connection_type_control_port_extras.hide()

    def connection_type_socket_file_toggled(self, checked):
        """
        Connection type socket file was toggled. If checked, show extra fields
        for socket file. If unchecked, hide those extra fields.
        """
        self.common.log("SettingsDialog", "connection_type_socket_file_toggled")
        if self.hide_tor_settings:
            return
        if checked:
            self.authenticate_group.show()
            self.connection_type_socket_file_extras.show()
            self.connection_type_socks.show()
            self.connection_type_bridges_radio_group.hide()
        else:
            self.connection_type_socket_file_extras.hide()

    def authenticate_no_auth_toggled(self, checked):
        """
        Authentication option no authentication was toggled.
        """
        self.common.log("SettingsDialog", "authenticate_no_auth_toggled")

    def authenticate_password_toggled(self, checked):
        """
        Authentication option password was toggled. If checked, show extra fields
        for password auth. If unchecked, hide those extra fields.
        """
        self.common.log("SettingsDialog", "authenticate_password_toggled")
        if checked:
            self.authenticate_password_extras.show()
        else:
            self.authenticate_password_extras.hide()

    def test_tor_clicked(self):
        """
        Test Tor Settings button clicked. With the given settings, see if we can
        successfully connect and authenticate to Tor.
        """
        self.common.log("SettingsDialog", "test_tor_clicked")
        settings = self.settings_from_fields()

        try:
            # Show Tor connection status if connection type is bundled tor
            if settings.get("connection_type") == "bundled":
                self.tor_status.show()
                self._disable_buttons()

                def tor_status_update_func(progress, summary):
                    self._tor_status_update(progress, summary)
                    return True

            else:
                tor_status_update_func = None

            onion = Onion(
                self.common,
                use_tmp_dir=True,
                get_tor_paths=self.common.gui.get_tor_paths,
            )
            onion.connect(
                custom_settings=settings,
                tor_status_update_func=tor_status_update_func,
            )

            # If an exception hasn't been raised yet, the Tor settings work
            Alert(
                self.common,
                strings._("settings_test_success").format(
                    onion.tor_version,
                    onion.supports_ephemeral,
                    onion.supports_stealth,
                    onion.supports_v3_onions,
                ),
            )

            # Clean up
            onion.cleanup()

        except (
            TorErrorInvalidSetting,
            TorErrorAutomatic,
            TorErrorSocketPort,
            TorErrorSocketFile,
            TorErrorMissingPassword,
            TorErrorUnreadableCookieFile,
            TorErrorAuthError,
            TorErrorProtocolError,
            BundledTorTimeout,
            BundledTorBroken,
            TorTooOldEphemeral,
            TorTooOldStealth,
            PortNotAvailable,
        ) as e:
            message = self.common.gui.get_translated_tor_error(e)
            Alert(
                self.common,
                message,
                QtWidgets.QMessageBox.Warning,
            )
            if settings.get("connection_type") == "bundled":
                self.tor_status.hide()
                self._enable_buttons()

    def check_for_updates(self):
        """
        Check for Updates button clicked. Manually force an update check.
        """
        self.common.log("SettingsDialog", "check_for_updates")
        # Disable buttons
        self._disable_buttons()
        self.common.gui.qtapp.processEvents()

        def update_timestamp():
            # Update the last checked label
            settings = Settings(self.common)
            settings.load()
            autoupdate_timestamp = settings.get("autoupdate_timestamp")
            self._update_autoupdate_timestamp(autoupdate_timestamp)

        def close_forced_update_thread():
            forced_update_thread.quit()
            # Enable buttons
            self._enable_buttons()
            # Update timestamp
            update_timestamp()

        # Check for updates
        def update_available(update_url, installed_version, latest_version):
            Alert(
                self.common,
                strings._("update_available").format(
                    update_url, installed_version, latest_version
                ),
            )
            close_forced_update_thread()

        def update_not_available():
            Alert(self.common, strings._("update_not_available"))
            close_forced_update_thread()

        def update_error():
            Alert(
                self.common,
                strings._("update_error_check_error"),
                QtWidgets.QMessageBox.Warning,
            )
            close_forced_update_thread()

        def update_invalid_version(latest_version):
            Alert(
                self.common,
                strings._("update_error_invalid_latest_version").format(latest_version),
                QtWidgets.QMessageBox.Warning,
            )
            close_forced_update_thread()

        forced_update_thread = UpdateThread(self.common, self.common.gui.onion, force=True)
        forced_update_thread.update_available.connect(update_available)
        forced_update_thread.update_not_available.connect(update_not_available)
        forced_update_thread.update_error.connect(update_error)
        forced_update_thread.update_invalid_version.connect(update_invalid_version)
        forced_update_thread.start()

    def save_clicked(self):
        """
        Save button clicked. Save current settings to disk.
        """
        self.common.log("SettingsDialog", "save_clicked")

        def changed(s1, s2, keys):
            """
            Compare the Settings objects s1 and s2 and return true if any values
            have changed for the given keys.
            """
            for key in keys:
                if s1.get(key) != s2.get(key):
                    return True
            return False

        settings = self.settings_from_fields()
        if settings:
            # If language changed, inform user they need to restart OnionShare
            if changed(settings, self.old_settings, ["locale"]):
                # Look up error message in different locale
                new_locale = settings.get("locale")
                if (
                    new_locale in strings.translations
                    and "gui_settings_language_changed_notice"
                    in strings.translations[new_locale]
                ):
                    notice = strings.translations[new_locale][
                        "gui_settings_language_changed_notice"
                    ]
                else:
                    notice = strings._("gui_settings_language_changed_notice")
                Alert(self.common, notice, QtWidgets.QMessageBox.Information)

            # Save the new settings
            settings.save()

            # If Tor isn't connected, or if Tor settings have changed, Reinitialize
            # the Onion object
            reboot_onion = False
            if not self.common.gui.local_only:
                if self.common.gui.onion.is_authenticated():
                    self.common.log(
                        "SettingsDialog", "save_clicked", "Connected to Tor"
                    )

                    if changed(
                        settings,
                        self.old_settings,
                        [
                            "connection_type",
                            "control_port_address",
                            "control_port_port",
                            "socks_address",
                            "socks_port",
                            "socket_file_path",
                            "auth_type",
                            "auth_password",
                            "no_bridges",
                            "tor_bridges_use_obfs4",
                            "tor_bridges_use_meek_lite_azure",
                            "tor_bridges_use_custom_bridges",
                        ],
                    ):

                        reboot_onion = True

                else:
                    self.common.log(
                        "SettingsDialog", "save_clicked", "Not connected to Tor"
                    )
                    # Tor isn't connected, so try connecting
                    reboot_onion = True

                # Do we need to reinitialize Tor?
                if reboot_onion:
                    # Reinitialize the Onion object
                    self.common.log(
                        "SettingsDialog", "save_clicked", "rebooting the Onion"
                    )
                    self.common.gui.onion.cleanup()

                    tor_con = TorConnectionDialog(self.common, settings)
                    tor_con.start()

                    self.common.log(
                        "SettingsDialog",
                        "save_clicked",
                        f"Onion done rebooting, connected to Tor: {self.common.gui.onion.connected_to_tor}",
                    )

                    if (
                        self.common.gui.onion.is_authenticated()
                        and not tor_con.wasCanceled()
                    ):
                        self.settings_saved.emit()
                        self.close()

                else:
                    self.settings_saved.emit()
                    self.close()
            else:
                self.settings_saved.emit()
                self.close()

    def cancel_clicked(self):
        """
        Cancel button clicked.
        """
        self.common.log("SettingsDialog", "cancel_clicked")
        if (
            not self.common.gui.local_only
            and not self.common.gui.onion.is_authenticated()
        ):
            Alert(
                self.common,
                strings._("gui_tor_connection_canceled"),
                QtWidgets.QMessageBox.Warning,
            )
            sys.exit()
        else:
            self.close()

    def help_clicked(self):
        """
        Help button clicked.
        """
        self.common.log("SettingsDialog", "help_clicked")
        SettingsDialog.open_help()

    @staticmethod
    def open_help():
        help_url = "https://docs.onionshare.org/"
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(help_url))

    def settings_from_fields(self):
        """
        Return a Settings object that's full of values from the settings dialog.
        """
        self.common.log("SettingsDialog", "settings_from_fields")
        settings = Settings(self.common)
        settings.load()  # To get the last update timestamp

        # Language
        locale_index = self.language_combobox.currentIndex()
        locale = self.language_combobox.itemData(locale_index)
        settings.set("locale", locale)

        # Tor connection
        if self.connection_type_bundled_radio.isChecked():
            settings.set("connection_type", "bundled")
        if self.connection_type_automatic_radio.isChecked():
            settings.set("connection_type", "automatic")
        if self.connection_type_control_port_radio.isChecked():
            settings.set("connection_type", "control_port")
        if self.connection_type_socket_file_radio.isChecked():
            settings.set("connection_type", "socket_file")

        if self.autoupdate_checkbox.isChecked():
            settings.set("use_autoupdate", True)
        else:
            settings.set("use_autoupdate", False)

        settings.set(
            "control_port_address",
            self.connection_type_control_port_extras_address.text(),
        )
        settings.set(
            "control_port_port", self.connection_type_control_port_extras_port.text()
        )
        settings.set(
            "socket_file_path", self.connection_type_socket_file_extras_path.text()
        )

        settings.set("socks_address", self.connection_type_socks_address.text())
        settings.set("socks_port", self.connection_type_socks_port.text())

        if self.authenticate_no_auth_radio.isChecked():
            settings.set("auth_type", "no_auth")
        if self.authenticate_password_radio.isChecked():
            settings.set("auth_type", "password")

        settings.set("auth_password", self.authenticate_password_extras_password.text())

        # Whether we use bridges
        if self.tor_bridges_no_bridges_radio.isChecked():
            settings.set("no_bridges", True)
            settings.set("tor_bridges_use_obfs4", False)
            settings.set("tor_bridges_use_meek_lite_azure", False)
            settings.set("tor_bridges_use_custom_bridges", "")
        if self.tor_bridges_use_obfs4_radio.isChecked():
            settings.set("no_bridges", False)
            settings.set("tor_bridges_use_obfs4", True)
            settings.set("tor_bridges_use_meek_lite_azure", False)
            settings.set("tor_bridges_use_custom_bridges", "")
        if self.tor_bridges_use_meek_lite_azure_radio.isChecked():
            settings.set("no_bridges", False)
            settings.set("tor_bridges_use_obfs4", False)
            settings.set("tor_bridges_use_meek_lite_azure", True)
            settings.set("tor_bridges_use_custom_bridges", "")
        if self.tor_bridges_use_custom_radio.isChecked():
            settings.set("no_bridges", False)
            settings.set("tor_bridges_use_obfs4", False)
            settings.set("tor_bridges_use_meek_lite_azure", False)

            # Insert a 'Bridge' line at the start of each bridge.
            # This makes it easier to copy/paste a set of bridges
            # provided from https://bridges.torproject.org
            new_bridges = []
            bridges = self.tor_bridges_use_custom_textbox.toPlainText().split("\n")
            bridges_valid = False
            for bridge in bridges:
                if bridge != "":
                    # Check the syntax of the custom bridge to make sure it looks legitimate
                    ipv4_pattern = re.compile(
                        "(obfs4\s+)?(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]):([0-9]+)(\s+)([A-Z0-9]+)(.+)$"
                    )
                    ipv6_pattern = re.compile(
                        "(obfs4\s+)?\[(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))\]:[0-9]+\s+[A-Z0-9]+(.+)$"
                    )
                    meek_lite_pattern = re.compile(
                        "(meek_lite)(\s)+([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+:[0-9]+)(\s)+([0-9A-Z]+)(\s)+url=(.+)(\s)+front=(.+)"
                    )
                    if (
                        ipv4_pattern.match(bridge)
                        or ipv6_pattern.match(bridge)
                        or meek_lite_pattern.match(bridge)
                    ):
                        new_bridges.append("".join(["Bridge ", bridge, "\n"]))
                        bridges_valid = True

            if bridges_valid:
                new_bridges = "".join(new_bridges)
                settings.set("tor_bridges_use_custom_bridges", new_bridges)
            else:
                Alert(self.common, strings._("gui_settings_tor_bridges_invalid"))
                settings.set("no_bridges", True)
                return False

        return settings

    def closeEvent(self, e):
        self.common.log("SettingsDialog", "closeEvent")

        # On close, if Tor isn't connected, then quit OnionShare altogether
        if not self.common.gui.local_only:
            if not self.common.gui.onion.is_authenticated():
                self.common.log(
                    "SettingsDialog", "closeEvent", "Closing while not connected to Tor"
                )

                # Wait 1ms for the event loop to finish, then quit
                QtCore.QTimer.singleShot(1, self.common.gui.qtapp.quit)

    def _update_autoupdate_timestamp(self, autoupdate_timestamp):
        self.common.log("SettingsDialog", "_update_autoupdate_timestamp")

        if autoupdate_timestamp:
            dt = datetime.datetime.fromtimestamp(autoupdate_timestamp)
            last_checked = dt.strftime("%B %d, %Y %H:%M")
        else:
            last_checked = strings._("gui_settings_autoupdate_timestamp_never")
        self.autoupdate_timestamp.setText(
            strings._("gui_settings_autoupdate_timestamp").format(last_checked)
        )

    def _tor_status_update(self, progress, summary):
        self.tor_status.setText(
            f"<strong>{strings._('connecting_to_tor')}</strong><br>{progress}% {summary}"
        )
        self.common.gui.qtapp.processEvents()
        if "Done" in summary:
            self.tor_status.hide()
            self._enable_buttons()

    def _disable_buttons(self):
        self.common.log("SettingsDialog", "_disable_buttons")

        self.check_for_updates_button.setEnabled(False)
        self.connection_type_test_button.setEnabled(False)
        self.save_button.setEnabled(False)
        self.cancel_button.setEnabled(False)

    def _enable_buttons(self):
        self.common.log("SettingsDialog", "_enable_buttons")
        # We can't check for updates if we're still not connected to Tor
        if not self.common.gui.onion.connected_to_tor:
            self.check_for_updates_button.setEnabled(False)
        else:
            self.check_for_updates_button.setEnabled(True)
        self.connection_type_test_button.setEnabled(True)
        self.save_button.setEnabled(True)
        self.cancel_button.setEnabled(True)
