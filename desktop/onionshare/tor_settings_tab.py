# -*- coding: utf-8 -*-
"""
OnionShare | https://onionshare.org/

Copyright (C) 2014-2022 Micah Lee, et al. <micah@micahflee.com>

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
import os

from onionshare_cli.meek import Meek
from onionshare_cli.settings import Settings
from onionshare_cli.onion import Onion

from . import strings
from .widgets import Alert
from .tor_connection import TorConnectionWidget
from .moat_dialog import MoatDialog


class TorSettingsTab(QtWidgets.QWidget):
    """
    Settings dialog.
    """

    close_this_tab = QtCore.Signal()
    tor_is_connected = QtCore.Signal()
    tor_is_disconnected = QtCore.Signal()

    def __init__(
        self,
        common,
        tab_id,
        are_tabs_active,
        status_bar,
        from_autoconnect=False,
        parent=None,
    ):
        super(TorSettingsTab, self).__init__()

        self.common = common
        self.common.log("TorSettingsTab", "__init__")

        self.status_bar = status_bar
        self.meek = Meek(common, get_tor_paths=self.common.gui.get_tor_paths)

        self.system = platform.system()
        self.tab_id = tab_id
        self.parent = parent
        self.from_autoconnect = from_autoconnect

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

        (
            self.tor_path,
            self.tor_geo_ip_file_path,
            self.tor_geo_ipv6_file_path,
            self.obfs4proxy_file_path,
            self.snowflake_file_path,
            self.meek_client_file_path,
        ) = self.common.gui.get_tor_paths()

        bridges_label = QtWidgets.QLabel(strings._("gui_settings_tor_bridges_label"))
        bridges_label.setWordWrap(True)

        self.bridge_use_checkbox = QtWidgets.QCheckBox(
            strings._("gui_settings_bridge_use_checkbox")
        )
        self.bridge_use_checkbox.stateChanged.connect(
            self.bridge_use_checkbox_state_changed
        )

        # Built-in bridge
        self.bridge_builtin_radio = QtWidgets.QRadioButton(
            strings._("gui_settings_bridge_radio_builtin")
        )
        self.bridge_builtin_radio.toggled.connect(self.bridge_builtin_radio_toggled)
        self.bridge_builtin_dropdown = QtWidgets.QComboBox()
        self.bridge_builtin_dropdown.currentTextChanged.connect(
            self.bridge_builtin_dropdown_changed
        )
        if self.obfs4proxy_file_path and os.path.isfile(self.obfs4proxy_file_path):
            self.bridge_builtin_dropdown.addItem("obfs4")
            self.bridge_builtin_dropdown.addItem("meek-azure")
        if self.snowflake_file_path and os.path.isfile(self.snowflake_file_path):
            self.bridge_builtin_dropdown.addItem("snowflake")

        # Request a bridge from torproject.org (moat)
        self.bridge_moat_radio = QtWidgets.QRadioButton(
            strings._("gui_settings_bridge_moat_radio_option")
        )
        self.bridge_moat_radio.toggled.connect(self.bridge_moat_radio_toggled)
        self.bridge_moat_button = QtWidgets.QPushButton(
            strings._("gui_settings_bridge_moat_button")
        )
        self.bridge_moat_button.clicked.connect(self.bridge_moat_button_clicked)
        self.bridge_moat_textbox = QtWidgets.QPlainTextEdit()
        self.bridge_moat_textbox.setMinimumHeight(100)
        self.bridge_moat_textbox.setMaximumHeight(100)
        self.bridge_moat_textbox.setReadOnly(True)
        self.bridge_moat_textbox.setWordWrapMode(QtGui.QTextOption.NoWrap)
        bridge_moat_textbox_options_layout = QtWidgets.QVBoxLayout()
        bridge_moat_textbox_options_layout.addWidget(self.bridge_moat_button)
        bridge_moat_textbox_options_layout.addWidget(self.bridge_moat_textbox)
        self.bridge_moat_textbox_options = QtWidgets.QWidget()
        self.bridge_moat_textbox_options.setLayout(bridge_moat_textbox_options_layout)
        self.bridge_moat_textbox_options.hide()

        # Custom bridges radio and textbox
        self.bridge_custom_radio = QtWidgets.QRadioButton(
            strings._("gui_settings_bridge_custom_radio_option")
        )
        self.bridge_custom_radio.toggled.connect(self.bridge_custom_radio_toggled)
        self.bridge_custom_textbox = QtWidgets.QPlainTextEdit()
        self.bridge_custom_textbox.setMinimumHeight(100)
        self.bridge_custom_textbox.setMaximumHeight(100)
        self.bridge_custom_textbox.setPlaceholderText(
            strings._("gui_settings_bridge_custom_placeholder")
        )

        bridge_custom_textbox_options_layout = QtWidgets.QVBoxLayout()
        bridge_custom_textbox_options_layout.addWidget(self.bridge_custom_textbox)

        self.bridge_custom_textbox_options = QtWidgets.QWidget()
        self.bridge_custom_textbox_options.setLayout(
            bridge_custom_textbox_options_layout
        )
        self.bridge_custom_textbox_options.hide()

        # Bridge settings layout
        bridge_settings_layout = QtWidgets.QVBoxLayout()
        bridge_settings_layout.addWidget(self.bridge_builtin_radio)
        bridge_settings_layout.addWidget(self.bridge_builtin_dropdown)
        bridge_settings_layout.addWidget(self.bridge_moat_radio)
        bridge_settings_layout.addWidget(self.bridge_moat_textbox_options)
        bridge_settings_layout.addWidget(self.bridge_custom_radio)
        bridge_settings_layout.addWidget(self.bridge_custom_textbox_options)
        self.bridge_settings = QtWidgets.QWidget()
        self.bridge_settings.setLayout(bridge_settings_layout)

        # Bridges layout/widget
        bridges_layout = QtWidgets.QVBoxLayout()
        bridges_layout.addWidget(bridges_label)
        bridges_layout.addWidget(self.bridge_use_checkbox)
        bridges_layout.addWidget(self.bridge_settings)

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
        self.authenticate_no_auth_checkbox = QtWidgets.QCheckBox(
            strings._("gui_settings_authenticate_no_auth_option")
        )
        self.authenticate_no_auth_checkbox.toggled.connect(
            self.authenticate_no_auth_toggled
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

        # Group for Tor settings
        tor_settings_layout = QtWidgets.QVBoxLayout()
        tor_settings_layout.addWidget(self.connection_type_control_port_extras)
        tor_settings_layout.addWidget(self.connection_type_socket_file_extras)
        tor_settings_layout.addWidget(self.connection_type_socks)
        tor_settings_layout.addWidget(self.authenticate_no_auth_checkbox)
        tor_settings_layout.addWidget(self.authenticate_password_extras)
        self.tor_settings_group = QtWidgets.QGroupBox(
            strings._("gui_settings_controller_extras_label")
        )
        self.tor_settings_group.setLayout(tor_settings_layout)
        self.tor_settings_group.hide()

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
        connection_type_radio_group_layout.addStretch()
        connection_type_radio_group = QtWidgets.QGroupBox(
            strings._("gui_settings_connection_type_label")
        )
        connection_type_radio_group.setLayout(connection_type_radio_group_layout)

        # Quickstart settings
        self.autoconnect_checkbox = QtWidgets.QCheckBox(
            strings._("gui_enable_autoconnect_checkbox")
        )
        self.autoconnect_checkbox.toggled.connect(self.autoconnect_toggled)
        left_column_settings = QtWidgets.QVBoxLayout()
        connection_type_radio_group.setFixedHeight(300)
        left_column_settings.addWidget(connection_type_radio_group)
        left_column_settings.addSpacing(20)
        left_column_settings.addWidget(self.autoconnect_checkbox)
        left_column_settings.addStretch()
        left_column_settings.setContentsMargins(0, 0, 0, 0)
        left_column_setting_widget = QtWidgets.QWidget()
        left_column_setting_widget.setLayout(left_column_settings)

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

        # Connection type layout
        connection_type_layout = QtWidgets.QVBoxLayout()
        connection_type_layout.addWidget(self.tor_settings_group)
        connection_type_layout.addWidget(self.connection_type_bridges_radio_group)
        connection_type_layout.addStretch()

        # Settings are in columns
        columns_layout = QtWidgets.QHBoxLayout()
        columns_layout.addWidget(left_column_setting_widget)
        columns_layout.addSpacing(20)
        columns_layout.addLayout(connection_type_layout, stretch=1)
        columns_wrapper = QtWidgets.QWidget()
        columns_wrapper.setFixedHeight(400)
        columns_wrapper.setLayout(columns_layout)

        # Tor connection widget
        self.tor_con = TorConnectionWidget(self.common, self.status_bar)
        self.tor_con.success.connect(self.tor_con_success)
        self.tor_con.fail.connect(self.tor_con_fail)
        self.tor_con.hide()
        self.tor_con_type = None

        # Error label
        self.error_label = QtWidgets.QLabel()
        self.error_label.setStyleSheet(self.common.gui.css["tor_settings_error"])
        self.error_label.setWordWrap(True)

        # Buttons
        self.test_tor_button = QtWidgets.QPushButton(
            strings._("gui_settings_connection_type_test_button")
        )
        self.test_tor_button.clicked.connect(self.test_tor_clicked)
        self.save_button = QtWidgets.QPushButton(strings._("gui_settings_button_save"))
        self.save_button.clicked.connect(self.save_clicked)
        buttons_layout = QtWidgets.QHBoxLayout()
        buttons_layout.addWidget(self.error_label, stretch=1)
        buttons_layout.addSpacing(20)
        buttons_layout.addWidget(self.test_tor_button)
        buttons_layout.addWidget(self.save_button)

        # Main layout
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addWidget(columns_wrapper)
        main_layout.addStretch()
        main_layout.addWidget(self.tor_con)
        main_layout.addStretch()
        main_layout.addLayout(buttons_layout)
        self.main_widget = QtWidgets.QWidget()
        self.main_widget.setLayout(main_layout)

        # Tabs are active label
        active_tabs_label = QtWidgets.QLabel(
            strings._("gui_settings_stop_active_tabs_label")
        )
        active_tabs_label.setAlignment(QtCore.Qt.AlignHCenter)

        # Active tabs layout
        active_tabs_layout = QtWidgets.QVBoxLayout()
        active_tabs_layout.addStretch()
        active_tabs_layout.addWidget(active_tabs_label)
        active_tabs_layout.addStretch()
        self.active_tabs_widget = QtWidgets.QWidget()
        self.active_tabs_widget.setLayout(active_tabs_layout)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.main_widget)
        layout.addWidget(self.active_tabs_widget)
        self.setLayout(layout)

        self.active_tabs_changed(are_tabs_active)
        self.reload_settings()

    def reload_settings(self):
        # Load settings, and fill them in
        self.old_settings = Settings(self.common)
        self.old_settings.load()

        # Check if autoconnect was enabled
        if self.old_settings.get("auto_connect"):
            self.autoconnect_checkbox.setCheckState(QtCore.Qt.Checked)

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
            self.authenticate_no_auth_checkbox.setCheckState(QtCore.Qt.Checked)
        else:
            self.authenticate_no_auth_checkbox.setChecked(QtCore.Qt.Unchecked)
        self.authenticate_password_extras_password.setText(
            self.old_settings.get("auth_password")
        )

        if self.old_settings.get("bridges_enabled"):
            self.bridge_use_checkbox.setCheckState(QtCore.Qt.Checked)
            self.bridge_settings.show()

            bridges_type = self.old_settings.get("bridges_type")
            if bridges_type == "built-in":
                self.bridge_builtin_radio.setChecked(True)
                self.bridge_builtin_dropdown.show()
                self.bridge_moat_radio.setChecked(False)
                self.bridge_moat_textbox_options.hide()
                self.bridge_custom_radio.setChecked(False)
                self.bridge_custom_textbox_options.hide()

                bridges_builtin_pt = self.old_settings.get("bridges_builtin_pt")
                if bridges_builtin_pt == "obfs4":
                    self.bridge_builtin_dropdown.setCurrentText("obfs4")
                elif bridges_builtin_pt == "meek-azure":
                    self.bridge_builtin_dropdown.setCurrentText("meek-azure")
                else:
                    self.bridge_builtin_dropdown.setCurrentText("snowflake")

                self.bridge_moat_textbox_options.hide()
                self.bridge_custom_textbox_options.hide()

            elif bridges_type == "moat":
                self.bridge_builtin_radio.setChecked(False)
                self.bridge_builtin_dropdown.hide()
                self.bridge_moat_radio.setChecked(True)
                self.bridge_moat_textbox_options.show()
                self.bridge_custom_radio.setChecked(False)
                self.bridge_custom_textbox_options.hide()

            else:
                self.bridge_builtin_radio.setChecked(False)
                self.bridge_builtin_dropdown.hide()
                self.bridge_moat_radio.setChecked(False)
                self.bridge_moat_textbox_options.hide()
                self.bridge_custom_radio.setChecked(True)
                self.bridge_custom_textbox_options.show()

            bridges_moat = self.old_settings.get("bridges_moat")
            self.bridge_moat_textbox.document().setPlainText(bridges_moat)
            bridges_custom = self.old_settings.get("bridges_custom")
            self.bridge_custom_textbox.document().setPlainText(bridges_custom)

        else:
            self.bridge_use_checkbox.setCheckState(QtCore.Qt.Unchecked)
            self.bridge_settings.hide()

    def autoconnect_toggled(self):
        """
        Auto connect checkbox clicked
        """
        self.common.log("TorSettingsTab", "autoconnect_checkbox_clicked")

    def active_tabs_changed(self, are_tabs_active):
        if are_tabs_active:
            self.main_widget.hide()
            self.active_tabs_widget.show()
        else:
            self.main_widget.show()
            self.active_tabs_widget.hide()

    def connection_type_bundled_toggled(self, checked):
        """
        Connection type bundled was toggled
        """
        self.common.log("TorSettingsTab", "connection_type_bundled_toggled")
        if checked:
            self.tor_settings_group.hide()
            self.connection_type_socks.hide()
            self.connection_type_bridges_radio_group.show()

    def bridge_use_checkbox_state_changed(self, state):
        """
        'Use a bridge' checkbox changed
        """
        if state == QtCore.Qt.Checked:
            self.bridge_settings.show()
            self.bridge_builtin_radio.click()
            self.bridge_builtin_dropdown.setCurrentText("obfs4")
        else:
            self.bridge_settings.hide()

    def bridge_builtin_radio_toggled(self, checked):
        """
        'Select a built-in bridge' radio button toggled
        """
        if checked:
            self.bridge_builtin_dropdown.show()
            self.bridge_custom_textbox_options.hide()
            self.bridge_moat_textbox_options.hide()

    def bridge_builtin_dropdown_changed(self, selection):
        """
        Build-in bridge selection changed
        """
        if selection == "meek-azure":
            # Alert the user about meek's costliness if it looks like they're turning it on
            if not self.old_settings.get("bridges_builtin_pt") == "meek-azure":
                Alert(
                    self.common,
                    strings._("gui_settings_meek_lite_expensive_warning"),
                    QtWidgets.QMessageBox.Warning,
                )

    def bridge_moat_radio_toggled(self, checked):
        """
        Moat (request bridge) bridges option was toggled. If checked, show moat bridge options.
        """
        if checked:
            self.bridge_builtin_dropdown.hide()
            self.bridge_custom_textbox_options.hide()
            self.bridge_moat_textbox_options.show()

    def bridge_moat_button_clicked(self):
        """
        Request new bridge button clicked
        """
        self.common.log("TorSettingsTab", "bridge_moat_button_clicked")

        moat_dialog = MoatDialog(self.common, self.meek)
        moat_dialog.got_bridges.connect(self.bridge_moat_got_bridges)
        moat_dialog.exec_()

    def bridge_moat_got_bridges(self, bridges):
        """
        Got new bridges from moat
        """
        self.common.log("TorSettingsTab", "bridge_moat_got_bridges")
        self.bridge_moat_textbox.document().setPlainText(bridges)
        self.bridge_moat_textbox.show()

    def bridge_custom_radio_toggled(self, checked):
        """
        Custom bridges option was toggled. If checked, show custom bridge options.
        """
        if checked:
            self.bridge_builtin_dropdown.hide()
            self.bridge_moat_textbox_options.hide()
            self.bridge_custom_textbox_options.show()

    def connection_type_automatic_toggled(self, checked):
        """
        Connection type automatic was toggled. If checked, hide authentication fields.
        """
        self.common.log("TorSettingsTab", "connection_type_automatic_toggled")
        if checked:
            self.tor_settings_group.hide()
            self.connection_type_socks.hide()
            self.connection_type_bridges_radio_group.hide()

    def connection_type_control_port_toggled(self, checked):
        """
        Connection type control port was toggled. If checked, show extra fields
        for Tor control address and port. If unchecked, hide those extra fields.
        """
        self.common.log("TorSettingsTab", "connection_type_control_port_toggled")
        if checked:
            self.tor_settings_group.show()
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
        self.common.log("TorSettingsTab", "connection_type_socket_file_toggled")
        if checked:
            self.tor_settings_group.show()
            self.connection_type_socket_file_extras.show()
            self.connection_type_socks.show()
            self.connection_type_bridges_radio_group.hide()
        else:
            self.connection_type_socket_file_extras.hide()

    def authenticate_no_auth_toggled(self, checked):
        """
        Authentication option no authentication was toggled.
        """
        self.common.log("TorSettingsTab", "authenticate_no_auth_toggled")
        if checked:
            self.authenticate_password_extras.hide()
        else:
            self.authenticate_password_extras.show()

    def test_tor_clicked(self):
        """
        Test Tor Settings button clicked. With the given settings, see if we can
        successfully connect and authenticate to Tor.
        """
        self.common.log("TorSettingsTab", "test_tor_clicked")

        self.error_label.setText("")

        settings = self.settings_from_fields()
        if not settings:
            return

        self.test_tor_button.hide()
        self.save_button.hide()

        self.test_onion = Onion(
            self.common,
            use_tmp_dir=True,
            get_tor_paths=self.common.gui.get_tor_paths,
        )

        self.tor_con_type = "test"
        self.tor_con.show()
        self.tor_con.start(settings, True, self.test_onion)

    def save_clicked(self):
        """
        Save button clicked. Save current settings to disk.
        """
        self.common.log("TorSettingsTab", "save_clicked")

        self.error_label.setText("")

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
            # Save the new settings
            settings.save()

            # If Tor isn't connected, or if Tor settings have changed, Reinitialize
            # the Onion object
            reboot_onion = False
            if not self.common.gui.local_only and not (
                self.from_autoconnect and not settings.get("auto_connect")
            ):
                if self.common.gui.onion.is_authenticated():
                    self.common.log(
                        "TorSettingsTab", "save_clicked", "Connected to Tor"
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
                            "bridges_enabled",
                            "bridges_type",
                            "bridges_builtin_pt",
                            "bridges_moat",
                            "bridges_custom",
                        ],
                    ):

                        reboot_onion = True

                else:
                    self.common.log(
                        "TorSettingsTab", "save_clicked", "Not connected to Tor"
                    )
                    # Tor isn't connected, so try connecting
                    reboot_onion = True

                # Do we need to reinitialize Tor?
                if reboot_onion:
                    # Tell the tabs that Tor is disconnected
                    self.tor_is_disconnected.emit()

                    # Reinitialize the Onion object
                    self.common.log(
                        "TorSettingsTab", "save_clicked", "rebooting the Onion"
                    )
                    self.common.gui.onion.cleanup()

                    self.test_tor_button.hide()
                    self.save_button.hide()

                    self.tor_con_type = "save"
                    self.tor_con.show()
                    self.tor_con.start(settings)
                else:
                    self.parent.close_this_tab.emit()
            else:
                self.parent.close_this_tab.emit()

    def tor_con_success(self):
        """
        Finished testing tor connection.
        """
        self.tor_con.hide()
        self.test_tor_button.show()
        self.save_button.show()

        if self.tor_con_type == "test":
            Alert(
                self.common,
                strings._("settings_test_success").format(
                    self.test_onion.tor_version,
                    self.test_onion.supports_ephemeral,
                    self.test_onion.supports_stealth,
                    self.test_onion.supports_v3_onions,
                ),
                title=strings._("gui_settings_connection_type_test_button"),
            )
            self.test_onion.cleanup()

        elif self.tor_con_type == "save":
            if (
                self.common.gui.onion.is_authenticated()
                and not self.tor_con.wasCanceled()
            ):
                # Tell the tabs that Tor is connected
                self.tor_is_connected.emit()
                # Close the tab
                self.parent.close_this_tab.emit()

        self.tor_con_type = None

    def tor_con_fail(self, msg):
        """
        Finished testing tor connection.
        """
        self.tor_con.hide()
        self.test_tor_button.show()
        self.save_button.show()

        self.error_label.setText(msg)

        if self.tor_con_type == "test":
            self.test_onion.cleanup()

        self.tor_con_type = None

    def settings_from_fields(self):
        """
        Return a Settings object that's full of values from the settings dialog.
        """
        self.common.log("TorSettingsTab", "settings_from_fields")
        settings = Settings(self.common)
        settings.load()  # To get the last update timestamp

        # autoconnect
        settings.set("auto_connect", self.autoconnect_checkbox.isChecked())

        # Tor connection
        if self.connection_type_bundled_radio.isChecked():
            settings.set("connection_type", "bundled")
        if self.connection_type_automatic_radio.isChecked():
            settings.set("connection_type", "automatic")
        if self.connection_type_control_port_radio.isChecked():
            settings.set("connection_type", "control_port")
        if self.connection_type_socket_file_radio.isChecked():
            settings.set("connection_type", "socket_file")

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

        if self.authenticate_no_auth_checkbox.checkState() == QtCore.Qt.Checked:
            settings.set("auth_type", "no_auth")
        else:
            settings.set("auth_type", "password")

        settings.set("auth_password", self.authenticate_password_extras_password.text())

        # Whether we use bridges
        if self.bridge_use_checkbox.checkState() == QtCore.Qt.Checked:
            settings.set("bridges_enabled", True)

            if self.bridge_builtin_radio.isChecked():
                settings.set("bridges_type", "built-in")

                selection = self.bridge_builtin_dropdown.currentText()
                settings.set("bridges_builtin_pt", selection)

            if self.bridge_moat_radio.isChecked():
                settings.set("bridges_type", "moat")
                moat_bridges = self.bridge_moat_textbox.toPlainText()
                if (
                    self.connection_type_bundled_radio.isChecked()
                    and moat_bridges.strip() == ""
                ):
                    self.error_label.setText(
                        strings._("gui_settings_moat_bridges_invalid")
                    )
                    return False

                settings.set("bridges_moat", moat_bridges)

            if self.bridge_custom_radio.isChecked():
                settings.set("bridges_type", "custom")

                bridges = self.bridge_custom_textbox.toPlainText().split("\n")
                bridges_valid = self.common.check_bridges_valid(bridges)
                if bridges_valid:
                    new_bridges = "\n".join(bridges_valid) + "\n"
                    settings.set("bridges_custom", new_bridges)
                else:
                    self.error_label.setText(
                        strings._("gui_settings_tor_bridges_invalid")
                    )
                    return False
        else:
            settings.set("bridges_enabled", False)

        return settings

    def closeEvent(self, e):
        self.common.log("TorSettingsTab", "closeEvent")

        # On close, if Tor isn't connected, then quit OnionShare altogether
        if not self.common.gui.local_only:
            if not self.common.gui.onion.is_authenticated():
                self.common.log(
                    "TorSettingsTab",
                    "closeEvent",
                    "Closing while not connected to Tor",
                )

                # Wait 1ms for the event loop to finish, then quit
                QtCore.QTimer.singleShot(1, self.common.gui.qtapp.quit)

    def settings_have_changed(self):
        # Global settings have changed
        self.common.log("TorSettingsTab", "settings_have_changed")
