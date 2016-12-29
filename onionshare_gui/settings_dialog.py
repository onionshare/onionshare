# -*- coding: utf-8 -*-
"""
OnionShare | https://onionshare.org/

Copyright (C) 2016 Micah Lee <micah@micahflee.com>

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

from onionshare import strings
from onionshare.settings import Settings

class SettingsDialog(QtWidgets.QDialog):
    """
    Settings dialog.
    """
    def __init__(self, parent=None):
        super(SettingsDialog, self).__init__(parent)

        self.setModal(True)
        self.setWindowTitle(strings._('gui_settings_window_title', True))

        # Connection type: either automatic, control port, or socket file

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

        # Cookie
        self.authenticate_cookie_radio = QtWidgets.QRadioButton(strings._('gui_settings_authenticate_cookie_option', True))
        self.authenticate_cookie_radio.toggled.connect(self.authenticate_cookie_toggled)

        authenticate_cookie_extras_label = QtWidgets.QLabel(strings._('gui_settings_cookie_label', True))
        self.authenticate_cookie_extras_cookie_path = QtWidgets.QLineEdit()
        authenticate_cookie_extras_layout = QtWidgets.QHBoxLayout()
        authenticate_cookie_extras_layout.addWidget(authenticate_cookie_extras_label)
        authenticate_cookie_extras_layout.addWidget(self.authenticate_cookie_extras_cookie_path)

        self.authenticate_cookie_extras = QtWidgets.QWidget()
        self.authenticate_cookie_extras.setLayout(authenticate_cookie_extras_layout)
        self.authenticate_cookie_extras.hide()

        # Authentication options layout
        authenticate_group_layout = QtWidgets.QVBoxLayout()
        authenticate_group_layout.addWidget(self.authenticate_no_auth_radio)
        authenticate_group_layout.addWidget(self.authenticate_password_radio)
        authenticate_group_layout.addWidget(self.authenticate_cookie_radio)
        authenticate_group_layout.addWidget(self.authenticate_password_extras)
        authenticate_group_layout.addWidget(self.authenticate_cookie_extras)
        self.authenticate_group = QtWidgets.QGroupBox(strings._("gui_settings_authenticate_label", True))
        self.authenticate_group.setLayout(authenticate_group_layout)


        # Buttons
        test_button = QtWidgets.QPushButton(strings._('gui_settings_button_test', True))
        test_button.clicked.connect(self.test_clicked)
        save_button = QtWidgets.QPushButton(strings._('gui_settings_button_save', True))
        save_button.clicked.connect(self.save_clicked)
        cancel_button = QtWidgets.QPushButton(strings._('gui_settings_button_cancel', True))
        cancel_button.clicked.connect(self.cancel_clicked)
        buttons_layout = QtWidgets.QHBoxLayout()
        buttons_layout.addWidget(test_button)
        buttons_layout.addWidget(save_button)
        buttons_layout.addWidget(cancel_button)

        # Layout
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(connection_type_group)
        layout.addWidget(self.authenticate_group)
        layout.addStretch()
        layout.addLayout(buttons_layout)
        self.setLayout(layout)


        # Load settings, and fill them in
        self.settings = Settings()
        connection_type = self.settings.get('connection_type')
        if connection_type == 'automatic':
            self.connection_type_automatic_radio.setChecked(True)
        elif connection_type == 'control_port':
            self.connect_type_control_port_radio.setChecked(True)
        elif connection_type == 'socket_file':
            self.connection_type_socket_file_radio.setChecked(True)
        self.connection_type_control_port_extras_address.setText(self.settings.get('control_port_address'))
        self.connection_type_control_port_extras_port.setText(self.settings.get('control_port_port'))
        self.connection_type_socket_file_extras_path.setText(self.settings.get('socket_file_path'))
        auth_type = self.settings.get('auth_type')
        if auth_type == 'no_auth':
            self.authenticate_no_auth_radio.setChecked(True)
        elif auth_type == 'password':
            self.authenticate_password_radio.setChecked(True)
        elif auth_type == 'cookie':
            self.authenticate_cookie_radio.setChecked(True)
        self.authenticate_password_extras_password.setText(self.settings.get('auth_password'))
        self.authenticate_cookie_extras_cookie_path.setText(self.settings.get('auth_cookie_path'))

        # Show the dialog
        self.exec_()

    def connection_type_automatic_toggled(self, checked):
        """
        Connection type automatic was toggled. If checked, disable all other
        fields. If unchecked, enable all other fields.
        """
        if checked:
            self.authenticate_group.setEnabled(False)
        else:
            self.authenticate_group.setEnabled(True)

    def connection_type_control_port_toggled(self, checked):
        """
        Connection type control port was toggled. If checked, show extra fields
        for Tor control address and port. If unchecked, hide those extra fields.
        """
        if checked:
            self.connection_type_control_port_extras.show()
        else:
            self.connection_type_control_port_extras.hide()


    def connection_type_socket_file_toggled(self, checked):
        """
        Connection type socket file was toggled. If checked, show extra fields
        for socket file. If unchecked, hide those extra fields.
        """
        if checked:
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

    def authenticate_cookie_toggled(self, checked):
        """
        Authentication option cookie was toggled. If checked, show extra fields
        for cookie auth. If unchecked, hide those extra fields.
        """
        if checked:
            self.authenticate_cookie_extras.show()
        else:
            self.authenticate_cookie_extras.hide()

    def test_clicked(self):
        """
        Test Settings button clicked. With the given settings, see if we can
        successfully connect and authenticate to Tor.
        """
        pass

    def save_clicked(self):
        """
        Save button clicked. Save current settings to disk.
        """
        pass

    def cancel_clicked(self):
        """
        Cancel button clicked.
        """
        self.close()
