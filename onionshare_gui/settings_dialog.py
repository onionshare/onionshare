# -*- coding: utf-8 -*-
"""
OnionShare | https://onionshare.org/

Copyright (C) 2017 Micah Lee <micah@micahflee.com>

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
from PyQt5 import QtCore, QtWidgets, QtGui
import sys, platform, datetime, re

from onionshare import strings, common
from onionshare.settings import Settings
from onionshare.onion import *

from .alert import Alert
from .update_checker import *
from .tor_connection_dialog import TorConnectionDialog

class SettingsDialog(QtWidgets.QDialog):
    """
    Settings dialog.
    """
    settings_saved = QtCore.pyqtSignal()

    def __init__(self, onion, qtapp, config=False, local_only=False):
        super(SettingsDialog, self).__init__()
        common.log('SettingsDialog', '__init__')

        self.onion = onion
        self.qtapp = qtapp
        self.config = config
        self.local_only = local_only

        self.setModal(True)
        self.setWindowTitle(strings._('gui_settings_window_title', True))
        self.setWindowIcon(QtGui.QIcon(common.get_resource_path('images/logo.png')))

        self.system = platform.system()

        # Sharing options

        # Close after first download
        self.close_after_first_download_checkbox = QtWidgets.QCheckBox()
        self.close_after_first_download_checkbox.setCheckState(QtCore.Qt.Checked)
        self.close_after_first_download_checkbox.setText(strings._("gui_settings_close_after_first_download_option", True))

        # Whether or not to show systray notifications
        self.systray_notifications_checkbox = QtWidgets.QCheckBox()
        self.systray_notifications_checkbox.setCheckState(QtCore.Qt.Checked)
        self.systray_notifications_checkbox.setText(strings._("gui_settings_systray_notifications", True))

        # Whether or not to use a shutdown timer
        self.shutdown_timeout_checkbox = QtWidgets.QCheckBox()
        self.shutdown_timeout_checkbox.setCheckState(QtCore.Qt.Checked)
        self.shutdown_timeout_checkbox.setText(strings._("gui_settings_shutdown_timeout_checkbox", True))

        # Whether or not to save the Onion private key for reuse
        self.save_private_key_checkbox = QtWidgets.QCheckBox()
        self.save_private_key_checkbox.setCheckState(QtCore.Qt.Unchecked)
        self.save_private_key_checkbox.setText(strings._("gui_save_private_key_checkbox", True))

        # Sharing options layout
        sharing_group_layout = QtWidgets.QVBoxLayout()
        sharing_group_layout.addWidget(self.close_after_first_download_checkbox)
        sharing_group_layout.addWidget(self.systray_notifications_checkbox)
        sharing_group_layout.addWidget(self.shutdown_timeout_checkbox)
        sharing_group_layout.addWidget(self.save_private_key_checkbox)
        sharing_group = QtWidgets.QGroupBox(strings._("gui_settings_sharing_label", True))
        sharing_group.setLayout(sharing_group_layout)

        # Stealth options

        # Stealth
        stealth_details = QtWidgets.QLabel(strings._("gui_settings_stealth_option_details", True))
        stealth_details.setWordWrap(True)
        stealth_details.setTextInteractionFlags(QtCore.Qt.TextBrowserInteraction)
        stealth_details.setOpenExternalLinks(True)
        stealth_details.setMinimumSize(stealth_details.sizeHint())
        self.stealth_checkbox = QtWidgets.QCheckBox()
        self.stealth_checkbox.setCheckState(QtCore.Qt.Unchecked)
        self.stealth_checkbox.setText(strings._("gui_settings_stealth_option", True))

        hidservauth_details = QtWidgets.QLabel(strings._('gui_settings_stealth_hidservauth_string', True))
        hidservauth_details.setWordWrap(True)
        hidservauth_details.setMinimumSize(hidservauth_details.sizeHint())
        hidservauth_details.hide()

        self.hidservauth_copy_button = QtWidgets.QPushButton(strings._('gui_copy_hidservauth', True))
        self.hidservauth_copy_button.clicked.connect(self.hidservauth_copy_button_clicked)
        self.hidservauth_copy_button.hide()

        # Stealth options layout
        stealth_group_layout = QtWidgets.QVBoxLayout()
        stealth_group_layout.addWidget(stealth_details)
        stealth_group_layout.addWidget(self.stealth_checkbox)
        stealth_group_layout.addWidget(hidservauth_details)
        stealth_group_layout.addWidget(self.hidservauth_copy_button)
        stealth_group = QtWidgets.QGroupBox(strings._("gui_settings_stealth_label", True))
        stealth_group.setLayout(stealth_group_layout)

        # Automatic updates options

        # Autoupdate
        self.autoupdate_checkbox = QtWidgets.QCheckBox()
        self.autoupdate_checkbox.setCheckState(QtCore.Qt.Unchecked)
        self.autoupdate_checkbox.setText(strings._("gui_settings_autoupdate_option", True))

        # Last update time
        self.autoupdate_timestamp = QtWidgets.QLabel()

        # Check for updates button
        self.check_for_updates_button = QtWidgets.QPushButton(strings._('gui_settings_autoupdate_check_button', True))
        self.check_for_updates_button.clicked.connect(self.check_for_updates)
        # We can't check for updates if not connected to Tor
        if not self.onion.connected_to_tor:
            self.check_for_updates_button.setEnabled(False)

        # Autoupdate options layout
        autoupdate_group_layout = QtWidgets.QVBoxLayout()
        autoupdate_group_layout.addWidget(self.autoupdate_checkbox)
        autoupdate_group_layout.addWidget(self.autoupdate_timestamp)
        autoupdate_group_layout.addWidget(self.check_for_updates_button)
        autoupdate_group = QtWidgets.QGroupBox(strings._("gui_settings_autoupdate_label", True))
        autoupdate_group.setLayout(autoupdate_group_layout)

        # Autoupdate is only available for Windows and Mac (Linux updates using package manager)
        if self.system != 'Windows' and self.system != 'Darwin':
            autoupdate_group.hide()

        # Connection type: either automatic, control port, or socket file

        # Bundled Tor
        self.connection_type_bundled_radio = QtWidgets.QRadioButton(strings._('gui_settings_connection_type_bundled_option', True))
        self.connection_type_bundled_radio.toggled.connect(self.connection_type_bundled_toggled)

        # Bundled Tor doesn't work on dev mode in Windows or Mac
        if (self.system == 'Windows' or self.system == 'Darwin') and getattr(sys, 'onionshare_dev_mode', False):
            self.connection_type_bundled_radio.setEnabled(False)

        # Bridge options for bundled tor

        # No bridges option radio
        self.tor_bridges_no_bridges_radio = QtWidgets.QRadioButton(strings._('gui_settings_tor_bridges_no_bridges_radio_option', True))
        self.tor_bridges_no_bridges_radio.toggled.connect(self.tor_bridges_no_bridges_radio_toggled)

        # obfs4 option radio
        # if the obfs4proxy binary is missing, we can't use obfs4 transports
        (self.tor_path, self.tor_geo_ip_file_path, self.tor_geo_ipv6_file_path, self.obfs4proxy_file_path) = common.get_tor_paths()
        if not os.path.isfile(self.obfs4proxy_file_path):
            self.tor_bridges_use_obfs4_radio = QtWidgets.QRadioButton(strings._('gui_settings_tor_bridges_obfs4_radio_option_no_obfs4proxy', True))
            self.tor_bridges_use_obfs4_radio.setEnabled(False)
        else:
            self.tor_bridges_use_obfs4_radio = QtWidgets.QRadioButton(strings._('gui_settings_tor_bridges_obfs4_radio_option', True))
        self.tor_bridges_use_obfs4_radio.toggled.connect(self.tor_bridges_use_obfs4_radio_toggled)

        # meek_lite-amazon option radio
        # if the obfs4proxy binary is missing, we can't use meek_lite-amazon transports
        (self.tor_path, self.tor_geo_ip_file_path, self.tor_geo_ipv6_file_path, self.obfs4proxy_file_path) = common.get_tor_paths()
        if not os.path.isfile(self.obfs4proxy_file_path):
            self.tor_bridges_use_meek_lite_amazon_radio = QtWidgets.QRadioButton(strings._('gui_settings_tor_bridges_meek_lite_amazon_radio_option_no_obfs4proxy', True))
            self.tor_bridges_use_meek_lite_amazon_radio.setEnabled(False)
        else:
            self.tor_bridges_use_meek_lite_amazon_radio = QtWidgets.QRadioButton(strings._('gui_settings_tor_bridges_meek_lite_amazon_radio_option', True))
        self.tor_bridges_use_meek_lite_amazon_radio.toggled.connect(self.tor_bridges_use_meek_lite_amazon_radio_toggled)

        # meek_lite-azure option radio
        # if the obfs4proxy binary is missing, we can't use meek_lite-azure transports
        (self.tor_path, self.tor_geo_ip_file_path, self.tor_geo_ipv6_file_path, self.obfs4proxy_file_path) = common.get_tor_paths()
        if not os.path.isfile(self.obfs4proxy_file_path):
            self.tor_bridges_use_meek_lite_azure_radio = QtWidgets.QRadioButton(strings._('gui_settings_tor_bridges_meek_lite_azure_radio_option_no_obfs4proxy', True))
            self.tor_bridges_use_meek_lite_azure_radio.setEnabled(False)
        else:
            self.tor_bridges_use_meek_lite_azure_radio = QtWidgets.QRadioButton(strings._('gui_settings_tor_bridges_meek_lite_azure_radio_option', True))
        self.tor_bridges_use_meek_lite_azure_radio.toggled.connect(self.tor_bridges_use_meek_lite_azure_radio_toggled)

        # meek_lite currently not supported on the version of obfs4proxy bundled with TorBrowser
        if self.system == 'Windows' or self.system == 'Darwin':
            self.tor_bridges_use_meek_lite_amazon_radio.hide()
            self.tor_bridges_use_meek_lite_azure_radio.hide()

        # Custom bridges radio and textbox
        self.tor_bridges_use_custom_radio = QtWidgets.QRadioButton(strings._('gui_settings_tor_bridges_custom_radio_option', True))
        self.tor_bridges_use_custom_radio.toggled.connect(self.tor_bridges_use_custom_radio_toggled)

        self.tor_bridges_use_custom_label = QtWidgets.QLabel(strings._('gui_settings_tor_bridges_custom_label', True))
        self.tor_bridges_use_custom_label.setTextInteractionFlags(QtCore.Qt.TextBrowserInteraction)
        self.tor_bridges_use_custom_label.setOpenExternalLinks(True)
        self.tor_bridges_use_custom_textbox = QtWidgets.QPlainTextEdit()
        self.tor_bridges_use_custom_textbox.setMaximumHeight(200)
        self.tor_bridges_use_custom_textbox.setPlaceholderText('[address:port] [identifier]')

        tor_bridges_use_custom_textbox_options_layout = QtWidgets.QVBoxLayout()
        tor_bridges_use_custom_textbox_options_layout.addWidget(self.tor_bridges_use_custom_label)
        tor_bridges_use_custom_textbox_options_layout.addWidget(self.tor_bridges_use_custom_textbox)

        self.tor_bridges_use_custom_textbox_options = QtWidgets.QWidget()
        self.tor_bridges_use_custom_textbox_options.setLayout(tor_bridges_use_custom_textbox_options_layout)
        self.tor_bridges_use_custom_textbox_options.hide()

        # Bridges layout/widget
        bridges_layout = QtWidgets.QVBoxLayout()
        bridges_layout.addWidget(self.tor_bridges_no_bridges_radio)
        bridges_layout.addWidget(self.tor_bridges_use_obfs4_radio)
        bridges_layout.addWidget(self.tor_bridges_use_meek_lite_amazon_radio)
        bridges_layout.addWidget(self.tor_bridges_use_meek_lite_azure_radio)
        bridges_layout.addWidget(self.tor_bridges_use_custom_radio)
        bridges_layout.addWidget(self.tor_bridges_use_custom_textbox_options)

        self.bridges = QtWidgets.QWidget()
        self.bridges.setLayout(bridges_layout)

        # Automatic
        self.connection_type_automatic_radio = QtWidgets.QRadioButton(strings._('gui_settings_connection_type_automatic_option', True))
        self.connection_type_automatic_radio.toggled.connect(self.connection_type_automatic_toggled)

        # Control port
        self.connection_type_control_port_radio = QtWidgets.QRadioButton(strings._('gui_settings_connection_type_control_port_option', True))
        self.connection_type_control_port_radio.toggled.connect(self.connection_type_control_port_toggled)

        connection_type_control_port_extras_label = QtWidgets.QLabel(strings._('gui_settings_control_port_label', True))
        self.connection_type_control_port_extras_address = QtWidgets.QLineEdit()
        self.connection_type_control_port_extras_port = QtWidgets.QLineEdit()
        connection_type_control_port_extras_layout = QtWidgets.QHBoxLayout()
        connection_type_control_port_extras_layout.addWidget(connection_type_control_port_extras_label)
        connection_type_control_port_extras_layout.addWidget(self.connection_type_control_port_extras_address)
        connection_type_control_port_extras_layout.addWidget(self.connection_type_control_port_extras_port)

        self.connection_type_control_port_extras = QtWidgets.QWidget()
        self.connection_type_control_port_extras.setLayout(connection_type_control_port_extras_layout)
        self.connection_type_control_port_extras.hide()

        # Socket file
        self.connection_type_socket_file_radio = QtWidgets.QRadioButton(strings._('gui_settings_connection_type_socket_file_option', True))
        self.connection_type_socket_file_radio.toggled.connect(self.connection_type_socket_file_toggled)

        connection_type_socket_file_extras_label = QtWidgets.QLabel(strings._('gui_settings_socket_file_label', True))
        self.connection_type_socket_file_extras_path = QtWidgets.QLineEdit()
        connection_type_socket_file_extras_layout = QtWidgets.QHBoxLayout()
        connection_type_socket_file_extras_layout.addWidget(connection_type_socket_file_extras_label)
        connection_type_socket_file_extras_layout.addWidget(self.connection_type_socket_file_extras_path)

        self.connection_type_socket_file_extras = QtWidgets.QWidget()
        self.connection_type_socket_file_extras.setLayout(connection_type_socket_file_extras_layout)
        self.connection_type_socket_file_extras.hide()

        # Tor SOCKS address and port
        gui_settings_socks_label = QtWidgets.QLabel(strings._('gui_settings_socks_label', True))
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
        self.authenticate_no_auth_radio = QtWidgets.QRadioButton(strings._('gui_settings_authenticate_no_auth_option', True))
        self.authenticate_no_auth_radio.toggled.connect(self.authenticate_no_auth_toggled)

        # Password
        self.authenticate_password_radio = QtWidgets.QRadioButton(strings._('gui_settings_authenticate_password_option', True))
        self.authenticate_password_radio.toggled.connect(self.authenticate_password_toggled)

        authenticate_password_extras_label = QtWidgets.QLabel(strings._('gui_settings_password_label', True))
        self.authenticate_password_extras_password = QtWidgets.QLineEdit('')
        authenticate_password_extras_layout = QtWidgets.QHBoxLayout()
        authenticate_password_extras_layout.addWidget(authenticate_password_extras_label)
        authenticate_password_extras_layout.addWidget(self.authenticate_password_extras_password)

        self.authenticate_password_extras = QtWidgets.QWidget()
        self.authenticate_password_extras.setLayout(authenticate_password_extras_layout)
        self.authenticate_password_extras.hide()

        # Authentication options layout
        authenticate_group_layout = QtWidgets.QVBoxLayout()
        authenticate_group_layout.addWidget(self.authenticate_no_auth_radio)
        authenticate_group_layout.addWidget(self.authenticate_password_radio)
        authenticate_group_layout.addWidget(self.authenticate_password_extras)
        self.authenticate_group = QtWidgets.QGroupBox(strings._("gui_settings_authenticate_label", True))
        self.authenticate_group.setLayout(authenticate_group_layout)

        # Test tor settings button
        self.connection_type_test_button = QtWidgets.QPushButton(strings._('gui_settings_connection_type_test_button', True))
        self.connection_type_test_button.clicked.connect(self.test_tor_clicked)

        # Put the radios into their own group so they are exclusive
        connection_type_radio_group_layout = QtWidgets.QVBoxLayout()
        connection_type_radio_group_layout.addWidget(self.connection_type_bundled_radio)
        connection_type_radio_group_layout.addWidget(self.connection_type_automatic_radio)
        connection_type_radio_group_layout.addWidget(self.connection_type_control_port_radio)
        connection_type_radio_group_layout.addWidget(self.connection_type_socket_file_radio)
        connection_type_radio_group = QtWidgets.QGroupBox(strings._("gui_settings_connection_type_label", True))
        connection_type_radio_group.setLayout(connection_type_radio_group_layout)

        # The Bridges options are not exclusive (enabling Bridges offers obfs4 or custom bridges)
        connection_type_bridges_radio_group_layout = QtWidgets.QVBoxLayout()
        connection_type_bridges_radio_group_layout.addWidget(self.bridges)
        self.connection_type_bridges_radio_group = QtWidgets.QGroupBox(strings._("gui_settings_tor_bridges", True))
        self.connection_type_bridges_radio_group.setLayout(connection_type_bridges_radio_group_layout)
        self.connection_type_bridges_radio_group.hide()

        # Connection type layout
        connection_type_layout = QtWidgets.QVBoxLayout()
        connection_type_layout.addWidget(self.connection_type_control_port_extras)
        connection_type_layout.addWidget(self.connection_type_socket_file_extras)
        connection_type_layout.addWidget(self.connection_type_socks)
        connection_type_layout.addWidget(self.authenticate_group)
        connection_type_layout.addWidget(self.connection_type_bridges_radio_group)
        connection_type_layout.addWidget(self.connection_type_test_button)

        # Buttons
        self.save_button = QtWidgets.QPushButton(strings._('gui_settings_button_save', True))
        self.save_button.clicked.connect(self.save_clicked)
        self.cancel_button = QtWidgets.QPushButton(strings._('gui_settings_button_cancel', True))
        self.cancel_button.clicked.connect(self.cancel_clicked)
        version_label = QtWidgets.QLabel('OnionShare {0:s}'.format(common.get_version()))
        version_label.setStyleSheet('color: #666666')
        self.help_button = QtWidgets.QPushButton(strings._('gui_settings_button_help', True))
        self.help_button.clicked.connect(self.help_clicked)
        buttons_layout = QtWidgets.QHBoxLayout()
        buttons_layout.addWidget(version_label)
        buttons_layout.addWidget(self.help_button)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.save_button)
        buttons_layout.addWidget(self.cancel_button)

        # Tor network connection status
        self.tor_status = QtWidgets.QLabel()
        self.tor_status.setStyleSheet('background-color: #ffffff; color: #000000; padding: 10px')
        self.tor_status.hide()

        # Layout
        left_col_layout = QtWidgets.QVBoxLayout()
        left_col_layout.addWidget(sharing_group)
        left_col_layout.addWidget(stealth_group)
        left_col_layout.addWidget(autoupdate_group)
        left_col_layout.addStretch()

        right_col_layout = QtWidgets.QVBoxLayout()
        right_col_layout.addWidget(connection_type_radio_group)
        right_col_layout.addLayout(connection_type_layout)
        right_col_layout.addWidget(self.tor_status)
        right_col_layout.addStretch()

        col_layout = QtWidgets.QHBoxLayout()
        col_layout.addLayout(left_col_layout)
        col_layout.addLayout(right_col_layout)

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(col_layout)
        layout.addLayout(buttons_layout)

        self.setLayout(layout)
        self.cancel_button.setFocus()

        # Load settings, and fill them in
        self.old_settings = Settings(self.config)
        self.old_settings.load()

        close_after_first_download = self.old_settings.get('close_after_first_download')
        if close_after_first_download:
            self.close_after_first_download_checkbox.setCheckState(QtCore.Qt.Checked)
        else:
            self.close_after_first_download_checkbox.setCheckState(QtCore.Qt.Unchecked)

        systray_notifications = self.old_settings.get('systray_notifications')
        if systray_notifications:
            self.systray_notifications_checkbox.setCheckState(QtCore.Qt.Checked)
        else:
            self.systray_notifications_checkbox.setCheckState(QtCore.Qt.Unchecked)

        shutdown_timeout = self.old_settings.get('shutdown_timeout')
        if shutdown_timeout:
            self.shutdown_timeout_checkbox.setCheckState(QtCore.Qt.Checked)
        else:
            self.shutdown_timeout_checkbox.setCheckState(QtCore.Qt.Unchecked)

        save_private_key = self.old_settings.get('save_private_key')
        if save_private_key:
            self.save_private_key_checkbox.setCheckState(QtCore.Qt.Checked)
        else:
            self.save_private_key_checkbox.setCheckState(QtCore.Qt.Unchecked)

        use_stealth = self.old_settings.get('use_stealth')
        if use_stealth:
            self.stealth_checkbox.setCheckState(QtCore.Qt.Checked)
            if save_private_key:
                hidservauth_details.show()
                self.hidservauth_copy_button.show()
        else:
            self.stealth_checkbox.setCheckState(QtCore.Qt.Unchecked)

        use_autoupdate = self.old_settings.get('use_autoupdate')
        if use_autoupdate:
            self.autoupdate_checkbox.setCheckState(QtCore.Qt.Checked)
        else:
            self.autoupdate_checkbox.setCheckState(QtCore.Qt.Unchecked)

        autoupdate_timestamp = self.old_settings.get('autoupdate_timestamp')
        self._update_autoupdate_timestamp(autoupdate_timestamp)

        connection_type = self.old_settings.get('connection_type')
        if connection_type == 'bundled':
            if self.connection_type_bundled_radio.isEnabled():
                self.connection_type_bundled_radio.setChecked(True)
            else:
                # If bundled tor is disabled, fallback to automatic
                self.connection_type_automatic_radio.setChecked(True)
        elif connection_type == 'automatic':
            self.connection_type_automatic_radio.setChecked(True)
        elif connection_type == 'control_port':
            self.connection_type_control_port_radio.setChecked(True)
        elif connection_type == 'socket_file':
            self.connection_type_socket_file_radio.setChecked(True)
        self.connection_type_control_port_extras_address.setText(self.old_settings.get('control_port_address'))
        self.connection_type_control_port_extras_port.setText(str(self.old_settings.get('control_port_port')))
        self.connection_type_socket_file_extras_path.setText(self.old_settings.get('socket_file_path'))
        self.connection_type_socks_address.setText(self.old_settings.get('socks_address'))
        self.connection_type_socks_port.setText(str(self.old_settings.get('socks_port')))
        auth_type = self.old_settings.get('auth_type')
        if auth_type == 'no_auth':
            self.authenticate_no_auth_radio.setChecked(True)
        elif auth_type == 'password':
            self.authenticate_password_radio.setChecked(True)
        self.authenticate_password_extras_password.setText(self.old_settings.get('auth_password'))

        if self.old_settings.get('no_bridges'):
            self.tor_bridges_no_bridges_radio.setChecked(True)
            self.tor_bridges_use_obfs4_radio.setChecked(False)
            self.tor_bridges_use_meek_lite_amazon_radio.setChecked(False)
            self.tor_bridges_use_meek_lite_azure_radio.setChecked(False)
            self.tor_bridges_use_custom_radio.setChecked(False)
        else:
            self.tor_bridges_no_bridges_radio.setChecked(False)
            self.tor_bridges_use_obfs4_radio.setChecked(self.old_settings.get('tor_bridges_use_obfs4'))
            self.tor_bridges_use_meek_lite_amazon_radio.setChecked(self.old_settings.get('tor_bridges_use_meek_lite_amazon'))
            self.tor_bridges_use_meek_lite_azure_radio.setChecked(self.old_settings.get('tor_bridges_use_meek_lite_azure'))

            if self.old_settings.get('tor_bridges_use_custom_bridges'):
                self.tor_bridges_use_custom_radio.setChecked(True)
                # Remove the 'Bridge' lines at the start of each bridge.
                # They are added automatically to provide compatibility with
                # copying/pasting bridges provided from https://bridges.torproject.org
                new_bridges = []
                bridges = self.old_settings.get('tor_bridges_use_custom_bridges').split('Bridge ')
                for bridge in bridges:
                    new_bridges.append(bridge)
                new_bridges = ''.join(new_bridges)
                self.tor_bridges_use_custom_textbox.setPlainText(new_bridges)

    def connection_type_bundled_toggled(self, checked):
        """
        Connection type bundled was toggled. If checked, hide authentication fields.
        """
        common.log('SettingsDialog', 'connection_type_bundled_toggled')
        if checked:
            self.authenticate_group.hide()
            self.connection_type_socks.hide()
            self.connection_type_bridges_radio_group.show()

    def tor_bridges_no_bridges_radio_toggled(self, checked):
        """
        'No bridges' option was toggled. If checked, enable other bridge options.
        """
        if checked:
            self.tor_bridges_use_custom_textbox_options.hide()

    def tor_bridges_use_obfs4_radio_toggled(self, checked):
        """
        obfs4 bridges option was toggled. If checked, disable custom bridge options.
        """
        if checked:
            self.tor_bridges_use_custom_textbox_options.hide()

    def tor_bridges_use_meek_lite_amazon_radio_toggled(self, checked):
        """
        meek_lite-amazon bridges option was toggled. If checked, disable custom bridge options.
        """
        if checked:
            self.tor_bridges_use_custom_textbox_options.hide()
            # Alert the user about meek's costliness if it looks like they're turning it on
            if not self.old_settings.get('tor_bridges_use_meek_lite_amazon'):
                Alert(strings._('gui_settings_meek_lite_expensive_warning', True), QtWidgets.QMessageBox.Warning)

    def tor_bridges_use_meek_lite_azure_radio_toggled(self, checked):
        """
        meek_lite_azure bridges option was toggled. If checked, disable custom bridge options.
        """
        if checked:
            self.tor_bridges_use_custom_textbox_options.hide()
            # Alert the user about meek's costliness if it looks like they're turning it on
            if not self.old_settings.get('tor_bridges_use_meek_lite_azure'):
                Alert(strings._('gui_settings_meek_lite_expensive_warning', True), QtWidgets.QMessageBox.Warning)

    def tor_bridges_use_custom_radio_toggled(self, checked):
        """
        Custom bridges option was toggled. If checked, show custom bridge options.
        """
        if checked:
            self.tor_bridges_use_custom_textbox_options.show()

    def connection_type_automatic_toggled(self, checked):
        """
        Connection type automatic was toggled. If checked, hide authentication fields.
        """
        common.log('SettingsDialog', 'connection_type_automatic_toggled')
        if checked:
            self.authenticate_group.hide()
            self.connection_type_socks.hide()
            self.connection_type_bridges_radio_group.hide()

    def connection_type_control_port_toggled(self, checked):
        """
        Connection type control port was toggled. If checked, show extra fields
        for Tor control address and port. If unchecked, hide those extra fields.
        """
        common.log('SettingsDialog', 'connection_type_control_port_toggled')
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
        common.log('SettingsDialog', 'connection_type_socket_file_toggled')
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
        common.log('SettingsDialog', 'authenticate_no_auth_toggled')

    def authenticate_password_toggled(self, checked):
        """
        Authentication option password was toggled. If checked, show extra fields
        for password auth. If unchecked, hide those extra fields.
        """
        common.log('SettingsDialog', 'authenticate_password_toggled')
        if checked:
            self.authenticate_password_extras.show()
        else:
            self.authenticate_password_extras.hide()

    def hidservauth_copy_button_clicked(self):
        """
        Toggle the 'Copy HidServAuth' button
        to copy the saved HidServAuth to clipboard.
        """
        common.log('SettingsDialog', 'hidservauth_copy_button_clicked', 'HidServAuth was copied to clipboard')
        clipboard = self.qtapp.clipboard()
        clipboard.setText(self.old_settings.get('hidservauth_string'))

    def test_tor_clicked(self):
        """
        Test Tor Settings button clicked. With the given settings, see if we can
        successfully connect and authenticate to Tor.
        """
        common.log('SettingsDialog', 'test_tor_clicked')
        settings = self.settings_from_fields()

        try:
            # Show Tor connection status if connection type is bundled tor
            if settings.get('connection_type') == 'bundled':
                self.tor_status.show()
                self._disable_buttons()

                def tor_status_update_func(progress, summary):
                    self._tor_status_update(progress, summary)
                    return True
            else:
                tor_status_update_func = None

            onion = Onion()
            onion.connect(settings=settings, config=self.config, tor_status_update_func=tor_status_update_func)

            # If an exception hasn't been raised yet, the Tor settings work
            Alert(strings._('settings_test_success', True).format(onion.tor_version, onion.supports_ephemeral, onion.supports_stealth))

            # Clean up
            onion.cleanup()

        except (TorErrorInvalidSetting, TorErrorAutomatic, TorErrorSocketPort, TorErrorSocketFile, TorErrorMissingPassword, TorErrorUnreadableCookieFile, TorErrorAuthError, TorErrorProtocolError, BundledTorNotSupported, BundledTorTimeout) as e:
            Alert(e.args[0], QtWidgets.QMessageBox.Warning)
            if settings.get('connection_type') == 'bundled':
                self.tor_status.hide()
                self._enable_buttons()

    def check_for_updates(self):
        """
        Check for Updates button clicked. Manually force an update check.
        """
        common.log('SettingsDialog', 'check_for_updates')
        # Disable buttons
        self._disable_buttons()
        self.qtapp.processEvents()

        def update_timestamp():
            # Update the last checked label
            settings = Settings(self.config)
            settings.load()
            autoupdate_timestamp = settings.get('autoupdate_timestamp')
            self._update_autoupdate_timestamp(autoupdate_timestamp)

        def close_forced_update_thread():
            forced_update_thread.quit()
            # Enable buttons
            self._enable_buttons()
            # Update timestamp
            update_timestamp()

        # Check for updates
        def update_available(update_url, installed_version, latest_version):
            Alert(strings._("update_available", True).format(update_url, installed_version, latest_version))
            close_forced_update_thread()

        def update_not_available():
            Alert(strings._('update_not_available', True))
            close_forced_update_thread()

        def update_error():
            Alert(strings._('update_error_check_error', True), QtWidgets.QMessageBox.Warning)
            close_forced_update_thread()

        def update_invalid_version():
            Alert(strings._('update_error_invalid_latest_version', True).format(e.latest_version), QtWidgets.QMessageBox.Warning)
            close_forced_update_thread()

        forced_update_thread = UpdateThread(self.onion, self.config, force=True)
        forced_update_thread.update_available.connect(update_available)
        forced_update_thread.update_not_available.connect(update_not_available)
        forced_update_thread.update_error.connect(update_error)
        forced_update_thread.update_invalid_version.connect(update_invalid_version)
        forced_update_thread.start()

    def save_clicked(self):
        """
        Save button clicked. Save current settings to disk.
        """
        common.log('SettingsDialog', 'save_clicked')

        settings = self.settings_from_fields()
        if settings:
            settings.save()

            # If Tor isn't connected, or if Tor settings have changed, Reinitialize
            # the Onion object
            reboot_onion = False
            if not self.local_only:
                if self.onion.is_authenticated():
                    common.log('SettingsDialog', 'save_clicked', 'Connected to Tor')
                    def changed(s1, s2, keys):
                        """
                        Compare the Settings objects s1 and s2 and return true if any values
                        have changed for the given keys.
                        """
                        for key in keys:
                            if s1.get(key) != s2.get(key):
                                return True
                        return False

                    if changed(settings, self.old_settings, [
                        'connection_type', 'control_port_address',
                        'control_port_port', 'socks_address', 'socks_port',
                        'socket_file_path', 'auth_type', 'auth_password',
                        'no_bridges', 'tor_bridges_use_obfs4',
                        'tor_bridges_use_meek_lite_amazon', 'tor_bridges_use_meek_lite_azure',
                        'tor_bridges_use_custom_bridges']):

                        reboot_onion = True

                else:
                    common.log('SettingsDialog', 'save_clicked', 'Not connected to Tor')
                    # Tor isn't connected, so try connecting
                    reboot_onion = True

                # Do we need to reinitialize Tor?
                if reboot_onion:
                    # Reinitialize the Onion object
                    common.log('SettingsDialog', 'save_clicked', 'rebooting the Onion')
                    self.onion.cleanup()

                    tor_con = TorConnectionDialog(self.qtapp, settings, self.onion)
                    tor_con.start()

                    common.log('SettingsDialog', 'save_clicked', 'Onion done rebooting, connected to Tor: {}'.format(self.onion.connected_to_tor))

                    if self.onion.is_authenticated() and not tor_con.wasCanceled():
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
        common.log('SettingsDialog', 'cancel_clicked')
        if not self.onion.is_authenticated():
            Alert(strings._('gui_tor_connection_canceled', True), QtWidgets.QMessageBox.Warning)
            sys.exit()
        else:
            self.close()

    def help_clicked(self):
        """
        Help button clicked.
        """
        common.log('SettingsDialog', 'help_clicked')
        help_site = 'https://github.com/micahflee/onionshare/wiki'
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(help_site))

    def settings_from_fields(self):
        """
        Return a Settings object that's full of values from the settings dialog.
        """
        common.log('SettingsDialog', 'settings_from_fields')
        settings = Settings(self.config)
        settings.load() # To get the last update timestamp

        settings.set('close_after_first_download', self.close_after_first_download_checkbox.isChecked())
        settings.set('systray_notifications', self.systray_notifications_checkbox.isChecked())
        settings.set('shutdown_timeout', self.shutdown_timeout_checkbox.isChecked())
        if self.save_private_key_checkbox.isChecked():
            settings.set('save_private_key', True)
            settings.set('private_key', self.old_settings.get('private_key'))
            settings.set('slug', self.old_settings.get('slug'))
            settings.set('hidservauth_string', self.old_settings.get('hidservauth_string'))
        else:
            settings.set('save_private_key', False)
            settings.set('private_key', '')
            settings.set('slug', '')
            # Also unset the HidServAuth if we are removing our reusable private key
            settings.set('hidservauth_string', '')
        settings.set('use_stealth', self.stealth_checkbox.isChecked())
        # Always unset the HidServAuth if Stealth mode is unset
        if not self.stealth_checkbox.isChecked():
            settings.set('hidservauth_string', '')

        if self.connection_type_bundled_radio.isChecked():
            settings.set('connection_type', 'bundled')
        if self.connection_type_automatic_radio.isChecked():
            settings.set('connection_type', 'automatic')
        if self.connection_type_control_port_radio.isChecked():
            settings.set('connection_type', 'control_port')
        if self.connection_type_socket_file_radio.isChecked():
            settings.set('connection_type', 'socket_file')

        if self.autoupdate_checkbox.isChecked():
            settings.set('use_autoupdate', True)
        else:
            settings.set('use_autoupdate', False)

        settings.set('control_port_address', self.connection_type_control_port_extras_address.text())
        settings.set('control_port_port', self.connection_type_control_port_extras_port.text())
        settings.set('socket_file_path', self.connection_type_socket_file_extras_path.text())

        settings.set('socks_address', self.connection_type_socks_address.text())
        settings.set('socks_port', self.connection_type_socks_port.text())

        if self.authenticate_no_auth_radio.isChecked():
            settings.set('auth_type', 'no_auth')
        if self.authenticate_password_radio.isChecked():
            settings.set('auth_type', 'password')

        settings.set('auth_password', self.authenticate_password_extras_password.text())

        # Whether we use bridges
        if self.tor_bridges_no_bridges_radio.isChecked():
            settings.set('no_bridges', True)
            settings.set('tor_bridges_use_obfs4', False)
            settings.set('tor_bridges_use_meek_lite_amazon', False)
            settings.set('tor_bridges_use_meek_lite_azure', False)
            settings.set('tor_bridges_use_custom_bridges', '')
        if self.tor_bridges_use_obfs4_radio.isChecked():
            settings.set('no_bridges', False)
            settings.set('tor_bridges_use_obfs4', True)
            settings.set('tor_bridges_use_meek_lite_amazon', False)
            settings.set('tor_bridges_use_meek_lite_azure', False)
            settings.set('tor_bridges_use_custom_bridges', '')
        if self.tor_bridges_use_meek_lite_amazon_radio.isChecked():
            settings.set('no_bridges', False)
            settings.set('tor_bridges_use_obfs4', False)
            settings.set('tor_bridges_use_meek_lite_amazon', True)
            settings.set('tor_bridges_use_meek_lite_azure', False)
            settings.set('tor_bridges_use_custom_bridges', '')
        if self.tor_bridges_use_meek_lite_azure_radio.isChecked():
            settings.set('no_bridges', False)
            settings.set('tor_bridges_use_obfs4', False)
            settings.set('tor_bridges_use_meek_lite_amazon', False)
            settings.set('tor_bridges_use_meek_lite_azure', True)
            settings.set('tor_bridges_use_custom_bridges', '')
        if self.tor_bridges_use_custom_radio.isChecked():
            settings.set('no_bridges', False)
            settings.set('tor_bridges_use_obfs4', False)
            settings.set('tor_bridges_use_meek_lite_amazon', False)
            settings.set('tor_bridges_use_meek_lite_azure', False)

            # Insert a 'Bridge' line at the start of each bridge.
            # This makes it easier to copy/paste a set of bridges
            # provided from https://bridges.torproject.org
            new_bridges = []
            bridges = self.tor_bridges_use_custom_textbox.toPlainText().split('\n')
            bridges_valid = False
            for bridge in bridges:
                if bridge != '':
                    # Check the syntax of the custom bridge to make sure it looks legitimate
                    ipv4_pattern = re.compile("(obfs4\s+)?(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]):([0-9]+)(\s+)([A-Z0-9]+)(.+)$")
                    ipv6_pattern = re.compile("(obfs4\s+)?\[(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))\]:[0-9]+\s+[A-Z0-9]+(.+)$")
                    meek_lite_pattern = re.compile("(meek_lite)(\s)+([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+:[0-9]+)(\s)+([0-9A-Z]+)(\s)+url=(.+)(\s)+front=(.+)")
                    if ipv4_pattern.match(bridge) or \
                       ipv6_pattern.match(bridge):
                        new_bridges.append(''.join(['Bridge ', bridge, '\n']))
                        bridges_valid = True
                    if self.system != 'Windows' and self.system != 'Darwin' and meek_lite_pattern.match(bridge):
                        new_bridges.append(''.join(['Bridge ', bridge, '\n']))
                        bridges_valid = True

            if bridges_valid:
                new_bridges = ''.join(new_bridges)
                settings.set('tor_bridges_use_custom_bridges', new_bridges)
            else:
                Alert(strings._('gui_settings_tor_bridges_invalid', True))
                settings.set('no_bridges', True)
                return False

        return settings

    def closeEvent(self, e):
        common.log('SettingsDialog', 'closeEvent')

        # On close, if Tor isn't connected, then quit OnionShare altogether
        if not self.local_only:
            if not self.onion.is_authenticated():
                common.log('SettingsDialog', 'closeEvent', 'Closing while not connected to Tor')

                # Wait 1ms for the event loop to finish, then quit
                QtCore.QTimer.singleShot(1, self.qtapp.quit)

    def _update_autoupdate_timestamp(self, autoupdate_timestamp):
        common.log('SettingsDialog', '_update_autoupdate_timestamp')

        if autoupdate_timestamp:
            dt = datetime.datetime.fromtimestamp(autoupdate_timestamp)
            last_checked = dt.strftime('%B %d, %Y %H:%M')
        else:
            last_checked = strings._('gui_settings_autoupdate_timestamp_never', True)
        self.autoupdate_timestamp.setText(strings._('gui_settings_autoupdate_timestamp', True).format(last_checked))

    def _tor_status_update(self, progress, summary):
        self.tor_status.setText('<strong>{}</strong><br>{}% {}'.format(strings._('connecting_to_tor', True), progress, summary))
        self.qtapp.processEvents()
        if 'Done' in summary:
            self.tor_status.hide()
            self._enable_buttons()

    def _disable_buttons(self):
        common.log('SettingsDialog', '_disable_buttons')

        self.check_for_updates_button.setEnabled(False)
        self.connection_type_test_button.setEnabled(False)
        self.save_button.setEnabled(False)
        self.cancel_button.setEnabled(False)

    def _enable_buttons(self):
        common.log('SettingsDialog', '_enable_buttons')
        # We can't check for updates if we're still not connected to Tor
        if not self.onion.connected_to_tor:
            self.check_for_updates_button.setEnabled(False)
        else:
            self.check_for_updates_button.setEnabled(True)
        self.connection_type_test_button.setEnabled(True)
        self.save_button.setEnabled(True)
        self.cancel_button.setEnabled(True)
