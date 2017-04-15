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
import sys, platform

from onionshare import strings, helpers
from onionshare.settings import Settings
from onionshare.onion import *

from .alert import Alert

class SettingsDialog(QtWidgets.QDialog):
    """
    Settings dialog.
    """
    def __init__(self, qtapp):
        super(SettingsDialog, self).__init__()
        self.qtapp = qtapp

        self.setModal(True)
        self.setWindowTitle(strings._('gui_settings_window_title', True))
        self.setWindowIcon(QtGui.QIcon(helpers.get_resource_path('images/logo.png')))

        # Sharing options

        # Close after first download
        self.close_after_first_download_checkbox = QtWidgets.QCheckBox()
        self.close_after_first_download_checkbox.setCheckState(QtCore.Qt.Checked)
        self.close_after_first_download_checkbox.setText(strings._("gui_settings_close_after_first_download_option", True))

        # Sharing options layout
        sharing_group_layout = QtWidgets.QVBoxLayout()
        sharing_group_layout.addWidget(self.close_after_first_download_checkbox)
        sharing_group = QtWidgets.QGroupBox(strings._("gui_settings_sharing_label", True))
        sharing_group.setLayout(sharing_group_layout)


        # Stealth options

        # Stealth
        stealth_details = QtWidgets.QLabel(strings._("gui_settings_stealth_option_details", True))
        stealth_details.setWordWrap(True)
        self.stealth_checkbox = QtWidgets.QCheckBox()
        self.stealth_checkbox.setCheckState(QtCore.Qt.Unchecked)
        self.stealth_checkbox.setText(strings._("gui_settings_stealth_option", True))

        # Stealth options layout
        stealth_group_layout = QtWidgets.QVBoxLayout()
        stealth_group_layout.addWidget(stealth_details)
        stealth_group_layout.addWidget(self.stealth_checkbox)
        stealth_group = QtWidgets.QGroupBox(strings._("gui_settings_stealth_label", True))
        stealth_group.setLayout(stealth_group_layout)


        # Connection type: either automatic, control port, or socket file

        # Bundled Tor
        self.connection_type_bundled_radio = QtWidgets.QRadioButton(strings._('gui_settings_connection_type_bundled_option', True))
        self.connection_type_bundled_radio.toggled.connect(self.connection_type_bundled_toggled)

        # Bundled Tor doesn't work on dev mode in Windows or Mac
        p = platform.system()
        if (p == 'Windows' or p == 'Darwin') and getattr(sys, 'onionshare_dev_mode', False):
            self.connection_type_bundled_radio.setEnabled(False)

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

        # Connection type layout
        connection_type_group_layout = QtWidgets.QVBoxLayout()
        connection_type_group_layout.addWidget(self.connection_type_bundled_radio)
        connection_type_group_layout.addWidget(self.connection_type_automatic_radio)
        connection_type_group_layout.addWidget(self.connection_type_control_port_radio)
        connection_type_group_layout.addWidget(self.connection_type_socket_file_radio)
        connection_type_group_layout.addWidget(self.connection_type_control_port_extras)
        connection_type_group_layout.addWidget(self.connection_type_socket_file_extras)
        connection_type_group = QtWidgets.QGroupBox(strings._("gui_settings_connection_type_label", True))
        connection_type_group.setLayout(connection_type_group_layout)


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


        # Buttons
        self.test_button = QtWidgets.QPushButton(strings._('gui_settings_button_test', True))
        self.test_button.clicked.connect(self.test_clicked)
        self.save_button = QtWidgets.QPushButton(strings._('gui_settings_button_save', True))
        self.save_button.clicked.connect(self.save_clicked)
        self.cancel_button = QtWidgets.QPushButton(strings._('gui_settings_button_cancel', True))
        self.cancel_button.clicked.connect(self.cancel_clicked)
        buttons_layout = QtWidgets.QHBoxLayout()
        buttons_layout.addWidget(self.test_button)
        buttons_layout.addWidget(self.save_button)
        buttons_layout.addWidget(self.cancel_button)

        # Tor networkconnection status
        self.tor_status = QtWidgets.QLabel()
        self.tor_status.setStyleSheet('color: #666666; padding-top: 10px')
        self.tor_status.hide()

        # Layout
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(sharing_group)
        layout.addWidget(stealth_group)
        layout.addWidget(connection_type_group)
        layout.addWidget(self.authenticate_group)
        layout.addStretch()
        layout.addLayout(buttons_layout)
        layout.addWidget(self.tor_status)
        self.setLayout(layout)


        # Load settings, and fill them in
        settings = Settings()
        settings.load()

        close_after_first_download = settings.get('close_after_first_download')
        if close_after_first_download:
            self.close_after_first_download_checkbox.setCheckState(QtCore.Qt.Checked)
        else:
            self.close_after_first_download_checkbox.setCheckState(QtCore.Qt.Unchecked)

        use_stealth = settings.get('use_stealth')
        if use_stealth:
            self.stealth_checkbox.setCheckState(QtCore.Qt.Checked)
        else:
            self.stealth_checkbox.setCheckState(QtCore.Qt.Unchecked)

        connection_type = settings.get('connection_type')
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
        self.connection_type_control_port_extras_address.setText(settings.get('control_port_address'))
        self.connection_type_control_port_extras_port.setText(str(settings.get('control_port_port')))
        self.connection_type_socket_file_extras_path.setText(settings.get('socket_file_path'))
        auth_type = settings.get('auth_type')
        if auth_type == 'no_auth':
            self.authenticate_no_auth_radio.setChecked(True)
        elif auth_type == 'password':
            self.authenticate_password_radio.setChecked(True)
        self.authenticate_password_extras_password.setText(settings.get('auth_password'))

        # Show the dialog
        self.exec_()

    def connection_type_bundled_toggled(self, checked):
        """
        Connection type bundled was toggled. If checked, hide authentication fields.
        """
        if checked:
            self.authenticate_group.hide()

    def connection_type_automatic_toggled(self, checked):
        """
        Connection type automatic was toggled. If checked, hide authentication fields.
        """
        if checked:
            self.authenticate_group.hide()

    def connection_type_control_port_toggled(self, checked):
        """
        Connection type control port was toggled. If checked, show extra fields
        for Tor control address and port. If unchecked, hide those extra fields.
        """
        if checked:
            self.authenticate_group.show()
            self.connection_type_control_port_extras.show()
        else:
            self.connection_type_control_port_extras.hide()


    def connection_type_socket_file_toggled(self, checked):
        """
        Connection type socket file was toggled. If checked, show extra fields
        for socket file. If unchecked, hide those extra fields.
        """
        if checked:
            self.authenticate_group.show()
            self.connection_type_socket_file_extras.show()
        else:
            self.connection_type_socket_file_extras.hide()

    def authenticate_no_auth_toggled(self, checked):
        """
        Authentication option no authentication was toggled.
        """
        pass

    def authenticate_password_toggled(self, checked):
        """
        Authentication option password was toggled. If checked, show extra fields
        for password auth. If unchecked, hide those extra fields.
        """
        if checked:
            self.authenticate_password_extras.show()
        else:
            self.authenticate_password_extras.hide()

    def test_clicked(self):
        """
        Test Settings button clicked. With the given settings, see if we can
        successfully connect and authenticate to Tor.
        """
        settings = self.settings_from_fields()

        def bundled_setup():
            self.tor_status.show()
            self.test_button.setEnabled(False)
            self.save_button.setEnabled(False)
            self.cancel_button.setEnabled(False)

        def bundled_cleanup():
            self.tor_status.hide()
            self.test_button.setEnabled(True)
            self.save_button.setEnabled(True)
            self.cancel_button.setEnabled(True)

        try:
            # Show Tor connection status if connection type is bundled tor
            if settings.get('connection_type') == 'bundled':
                bundled_setup()
                def bundled_tor_func(message):
                    self.tor_status.setText('<strong>{}</strong><br>{}'.format(strings._('connecting_to_tor', True), message))
                    self.qtapp.processEvents()
                    if 'Done' in message:
                        bundled_cleanup()
            else:
                bundled_tor_func = None

            onion = Onion(settings=settings, bundled_tor_func=bundled_tor_func)

            # If an exception hasn't been raised yet, the Tor settings work
            Alert(strings._('settings_test_success', True).format(onion.tor_version, onion.supports_ephemeral, onion.supports_stealth))

            # Clean up
            onion.cleanup()

        except (TorErrorInvalidSetting, TorErrorAutomatic, TorErrorSocketPort, TorErrorSocketFile, TorErrorMissingPassword, TorErrorUnreadableCookieFile, TorErrorAuthError, TorErrorProtocolError, BundledTorNotSupported, BundledTorTimeout) as e:
            Alert(e.args[0], QtWidgets.QMessageBox.Warning)
            if settings.get('connection_type') == 'bundled':
                bundled_cleanup()

    def save_clicked(self):
        """
        Save button clicked. Save current settings to disk.
        """
        settings = self.settings_from_fields()
        settings.save()
        self.close()

    def cancel_clicked(self):
        """
        Cancel button clicked.
        """
        self.close()

    def settings_from_fields(self):
        """
        Return a Settings object that's full of values from the settings dialog.
        """
        settings = Settings()

        settings.set('close_after_first_download', self.close_after_first_download_checkbox.isChecked())
        settings.set('use_stealth', self.stealth_checkbox.isChecked())

        if self.connection_type_bundled_radio.isChecked():
            settings.set('connection_type', 'bundled')
        if self.connection_type_automatic_radio.isChecked():
            settings.set('connection_type', 'automatic')
        if self.connection_type_control_port_radio.isChecked():
            settings.set('connection_type', 'control_port')
        if self.connection_type_socket_file_radio.isChecked():
            settings.set('connection_type', 'socket_file')

        settings.set('control_port_address', self.connection_type_control_port_extras_address.text())
        settings.set('control_port_port', int(self.connection_type_control_port_extras_port.text()))
        settings.set('socket_file_path', self.connection_type_socket_file_extras_path.text())

        if self.authenticate_no_auth_radio.isChecked():
            settings.set('auth_type', 'no_auth')
        if self.authenticate_password_radio.isChecked():
            settings.set('auth_type', 'password')

        settings.set('auth_password', self.authenticate_password_extras_password.text())

        return settings
