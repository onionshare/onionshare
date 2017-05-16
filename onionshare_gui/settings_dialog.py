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
import sys, platform, datetime

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
    def __init__(self, onion, qtapp):
        super(SettingsDialog, self).__init__()
        common.log('SettingsDialog', '__init__')

        self.onion = onion
        self.qtapp = qtapp

        self.setModal(True)
        self.setWindowTitle(strings._('gui_settings_window_title', True))
        self.setWindowIcon(QtGui.QIcon(common.get_resource_path('images/logo.png')))

        system = platform.system()

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

        # Autoupdate options layout
        autoupdate_group_layout = QtWidgets.QVBoxLayout()
        autoupdate_group_layout.addWidget(self.autoupdate_checkbox)
        autoupdate_group_layout.addWidget(self.autoupdate_timestamp)
        autoupdate_group_layout.addWidget(self.check_for_updates_button)
        autoupdate_group = QtWidgets.QGroupBox(strings._("gui_settings_autoupdate_label", True))
        autoupdate_group.setLayout(autoupdate_group_layout)

        # Autoupdate is only available for Windows and Mac (Linux updates using package manager)
        if system != 'Windows' and system != 'Darwin':
            autoupdate_group.hide()

        # Connection type: either automatic, control port, or socket file

        # Bundled Tor
        self.connection_type_bundled_radio = QtWidgets.QRadioButton(strings._('gui_settings_connection_type_bundled_option', True))
        self.connection_type_bundled_radio.toggled.connect(self.connection_type_bundled_toggled)

        # Bundled Tor doesn't work on dev mode in Windows or Mac
        if (system == 'Windows' or system == 'Darwin') and getattr(sys, 'onionshare_dev_mode', False):
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

        # Connection type layout
        connection_type_group_layout = QtWidgets.QVBoxLayout()
        connection_type_group_layout.addWidget(self.connection_type_bundled_radio)
        connection_type_group_layout.addWidget(self.connection_type_automatic_radio)
        connection_type_group_layout.addWidget(self.connection_type_control_port_radio)
        connection_type_group_layout.addWidget(self.connection_type_socket_file_radio)
        connection_type_group_layout.addWidget(self.connection_type_control_port_extras)
        connection_type_group_layout.addWidget(self.connection_type_socket_file_extras)
        connection_type_group_layout.addWidget(self.connection_type_socks)
        connection_type_group_layout.addWidget(self.authenticate_group)
        connection_type_group_layout.addWidget(self.connection_type_test_button)
        connection_type_group = QtWidgets.QGroupBox(strings._("gui_settings_connection_type_label", True))
        connection_type_group.setLayout(connection_type_group_layout)

        # Buttons
        self.save_button = QtWidgets.QPushButton(strings._('gui_settings_button_save', True))
        self.save_button.clicked.connect(self.save_clicked)
        self.cancel_button = QtWidgets.QPushButton(strings._('gui_settings_button_cancel', True))
        self.cancel_button.clicked.connect(self.cancel_clicked)
        buttons_layout = QtWidgets.QHBoxLayout()
        buttons_layout.addWidget(self.save_button)
        buttons_layout.addWidget(self.cancel_button)

        # Tor network connection status
        self.tor_status = QtWidgets.QLabel()
        self.tor_status.setStyleSheet('background-color: #ffffff; color: #000000; padding: 10px')
        self.tor_status.hide()

        # Layout
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(sharing_group)
        layout.addWidget(stealth_group)
        layout.addWidget(autoupdate_group)
        layout.addWidget(connection_type_group)
        layout.addStretch()
        layout.addLayout(buttons_layout)
        layout.addWidget(self.tor_status)
        self.setLayout(layout)
        self.cancel_button.setFocus()

        # Load settings, and fill them in
        self.old_settings = Settings()
        self.old_settings.load()

        close_after_first_download = self.old_settings.get('close_after_first_download')
        if close_after_first_download:
            self.close_after_first_download_checkbox.setCheckState(QtCore.Qt.Checked)
        else:
            self.close_after_first_download_checkbox.setCheckState(QtCore.Qt.Unchecked)

        use_stealth = self.old_settings.get('use_stealth')
        if use_stealth:
            self.stealth_checkbox.setCheckState(QtCore.Qt.Checked)
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

        # Show the dialog
        self.exec_()

    def connection_type_bundled_toggled(self, checked):
        """
        Connection type bundled was toggled. If checked, hide authentication fields.
        """
        common.log('SettingsDialog', 'connection_type_bundled_toggled')
        if checked:
            self.authenticate_group.hide()
            self.connection_type_socks.hide()

    def connection_type_automatic_toggled(self, checked):
        """
        Connection type automatic was toggled. If checked, hide authentication fields.
        """
        common.log('SettingsDialog', 'connection_type_automatic_toggled')
        if checked:
            self.authenticate_group.hide()
            self.connection_type_socks.hide()

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
            onion.connect(settings=settings, tor_status_update_func=tor_status_update_func)

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

        # Check for updates
        def update_available(update_url, installed_version, latest_version):
            Alert(strings._("update_available", True).format(update_url, installed_version, latest_version))
        def update_not_available():
            Alert(strings._('update_not_available', True))

        u = UpdateChecker(self.onion)
        u.update_available.connect(update_available)
        u.update_not_available.connect(update_not_available)

        try:
            u.check(force=True)
        except UpdateCheckerCheckError:
            Alert(strings._('update_error_check_error', True), QtWidgets.QMessageBox.Warning)
        except UpdateCheckerInvalidLatestVersion as e:
            Alert(strings._('update_error_invalid_latest_version', True).format(e.latest_version), QtWidgets.QMessageBox.Warning)

        # Enable buttons
        self._enable_buttons()

        # Update the last checked label
        settings = Settings()
        settings.load()
        autoupdate_timestamp = settings.get('autoupdate_timestamp')
        self._update_autoupdate_timestamp(autoupdate_timestamp)

    def save_clicked(self):
        """
        Save button clicked. Save current settings to disk.
        """
        common.log('SettingsDialog', 'save_clicked')

        settings = self.settings_from_fields()
        settings.save()

        # If Tor isn't connected, or if Tor settings have changed, Reinitialize
        # the Onion object
        reboot_onion = False
        if self.onion.connected_to_tor:
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
                'socket_file_path', 'auth_type', 'auth_password']):

                reboot_onion = True

        else:
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

            if self.onion.connected_to_tor and not tor_con.wasCanceled():
                self.close()

        else:
            self.close()

    def cancel_clicked(self):
        """
        Cancel button clicked.
        """
        common.log('SettingsDialog', 'cancel_clicked')
        self.close()

    def settings_from_fields(self):
        """
        Return a Settings object that's full of values from the settings dialog.
        """
        common.log('SettingsDialog', 'settings_from_fields')
        settings = Settings()
        settings.load() # To get the last update timestamp

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
        settings.set('control_port_port', self.connection_type_control_port_extras_port.text())
        settings.set('socket_file_path', self.connection_type_socket_file_extras_path.text())

        settings.set('socks_address', self.connection_type_socks_address.text())
        settings.set('socks_port', self.connection_type_socks_port.text())

        if self.authenticate_no_auth_radio.isChecked():
            settings.set('auth_type', 'no_auth')
        if self.authenticate_password_radio.isChecked():
            settings.set('auth_type', 'password')

        settings.set('auth_password', self.authenticate_password_extras_password.text())

        return settings

    def closeEvent(self, e):
        common.log('SettingsDialog', 'closeEvent')

        # On close, if Tor isn't connected, then quit OnionShare altogether
        if not self.onion.connected_to_tor:
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
        self.tor_status.setText('<strong>{}</strong><br>{}'.format(strings._('connecting_to_tor', True), summary))
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

        self.check_for_updates_button.setEnabled(True)
        self.connection_type_test_button.setEnabled(True)
        self.save_button.setEnabled(True)
        self.cancel_button.setEnabled(True)
