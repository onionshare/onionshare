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
import platform
from .alert import Alert
from PyQt5 import QtCore, QtWidgets, QtGui

from onionshare import strings, common, settings

class ServerStatus(QtWidgets.QWidget):
    """
    The server status chunk of the GUI.
    """
    server_started = QtCore.pyqtSignal()
    server_stopped = QtCore.pyqtSignal()
    url_copied = QtCore.pyqtSignal()
    hidservauth_copied = QtCore.pyqtSignal()

    STATUS_STOPPED = 0
    STATUS_WORKING = 1
    STATUS_STARTED = 2

    def __init__(self, qtapp, app, web, file_selection, settings):
        super(ServerStatus, self).__init__()
        self.status = self.STATUS_STOPPED

        self.qtapp = qtapp
        self.app = app
        self.web = web
        self.file_selection = file_selection

        self.settings = settings

        # Helper boolean as this is used in a few places
        self.timer_enabled = False

        # Shutdown timeout layout
        self.server_shutdown_timeout_checkbox = QtWidgets.QCheckBox()
        self.server_shutdown_timeout_checkbox.setCheckState(QtCore.Qt.Unchecked)
        self.server_shutdown_timeout_checkbox.toggled.connect(self.shutdown_timeout_toggled)
        self.server_shutdown_timeout_checkbox.setText(strings._("gui_settings_shutdown_timeout_choice", True))
        self.server_shutdown_timeout_label = QtWidgets.QLabel(strings._('gui_settings_shutdown_timeout', True))
        self.server_shutdown_timeout = QtWidgets.QDateTimeEdit()

        # Set proposed timeout to be 5 minutes into the future
        self.server_shutdown_timeout.setDateTime(QtCore.QDateTime.currentDateTime().addSecs(300))

        # Onion services can take a little while to start, so reduce the risk of it expiring too soon by setting the minimum to 2 min from now
        self.server_shutdown_timeout.setMinimumDateTime(QtCore.QDateTime.currentDateTime().addSecs(120))
        self.server_shutdown_timeout.setCurrentSectionIndex(4)
        self.server_shutdown_timeout_label.hide()
        self.server_shutdown_timeout.hide()
        shutdown_timeout_layout = QtWidgets.QHBoxLayout()
        shutdown_timeout_layout.addWidget(self.server_shutdown_timeout_label)
        shutdown_timeout_layout.addWidget(self.server_shutdown_timeout)

        # Shutdown timeout container, so it can all be hidden and shown as a group
        shutdown_timeout_container_layout = QtWidgets.QVBoxLayout()
        shutdown_timeout_container_layout.addWidget(self.server_shutdown_timeout_checkbox)
        shutdown_timeout_container_layout.addLayout(shutdown_timeout_layout)
        self.server_shutdown_timeout_container = QtWidgets.QWidget()
        self.server_shutdown_timeout_container.setLayout(shutdown_timeout_container_layout)

        # Server layout
        self.server_button = QtWidgets.QPushButton()
        self.server_button.clicked.connect(self.server_button_clicked)

        # URL layout
        url_font = QtGui.QFont()
        self.url_description = QtWidgets.QLabel(strings._('gui_url_description', True))
        self.url_description.setWordWrap(True)
        self.url_description.setMinimumHeight(50)
        self.url_label = QtWidgets.QLabel()
        self.url_label.setStyleSheet('QLabel { color: #666666; font-size: 12px; }')
        self.url = QtWidgets.QLabel()
        self.url.setFont(url_font)
        self.url.setWordWrap(True)
        self.url.setMinimumHeight(60)
        self.url.setStyleSheet('QLabel { background-color: #ffffff; color: #000000; padding: 10px; border: 1px solid #666666; }')

        url_buttons_style = 'QPushButton { color: #3f7fcf; }'
        self.copy_url_button = QtWidgets.QPushButton(strings._('gui_copy_url', True))
        self.copy_url_button.setFlat(True)
        self.copy_url_button.setStyleSheet(url_buttons_style)
        self.copy_url_button.clicked.connect(self.copy_url)
        self.copy_hidservauth_button = QtWidgets.QPushButton(strings._('gui_copy_hidservauth', True))
        self.copy_hidservauth_button.setFlat(True)
        self.copy_hidservauth_button.setStyleSheet(url_buttons_style)
        self.copy_hidservauth_button.clicked.connect(self.copy_hidservauth)
        url_buttons_layout = QtWidgets.QHBoxLayout()
        url_buttons_layout.addWidget(self.copy_url_button)
        url_buttons_layout.addWidget(self.copy_hidservauth_button)
        url_buttons_layout.addStretch()

        url_layout = QtWidgets.QVBoxLayout()
        url_layout.addWidget(self.url_description)
        url_layout.addWidget(self.url_label)
        url_layout.addWidget(self.url)
        url_layout.addLayout(url_buttons_layout)

        # Add the widgets
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.server_button)
        layout.addLayout(url_layout)
        layout.addWidget(self.server_shutdown_timeout_container)
        self.setLayout(layout)

        self.update()

    def shutdown_timeout_toggled(self, checked):
        """
        Shutdown timer option was toggled. If checked, show the timer settings.
        """
        if checked:
            self.timer_enabled = True
            # Hide the checkbox, show the options
            self.server_shutdown_timeout_label.show()
            # Reset the default timer to 5 minutes into the future after toggling the option on
            self.server_shutdown_timeout.setDateTime(QtCore.QDateTime.currentDateTime().addSecs(300))
            self.server_shutdown_timeout.show()
        else:
            self.timer_enabled = False
            self.server_shutdown_timeout_label.hide()
            self.server_shutdown_timeout.hide()

    def shutdown_timeout_reset(self):
        """
        Reset the timeout in the UI after stopping a share
        """
        self.server_shutdown_timeout_checkbox.setCheckState(QtCore.Qt.Unchecked)
        self.server_shutdown_timeout.setDateTime(QtCore.QDateTime.currentDateTime().addSecs(300))
        self.server_shutdown_timeout.setMinimumDateTime(QtCore.QDateTime.currentDateTime().addSecs(120))

    def update(self):
        """
        Update the GUI elements based on the current state.
        """
        # Set the URL fields
        if self.status == self.STATUS_STARTED:
            self.url_description.show()

            if self.settings.get('close_after_first_download'):
                self.url_label.setText(strings._('gui_url_label_one_time', True))
            else:
                self.url_label.setText(strings._('gui_url_label', True))
            self.url_label.show()

            self.url.setText('http://{0:s}/{1:s}'.format(self.app.onion_host, self.web.slug))
            self.url.show()

            self.copy_url_button.show()

            if self.settings.get('save_private_key'):
                if not self.settings.get('slug'):
                    self.settings.set('slug', self.web.slug)
                    self.settings.save()

            if self.app.stealth:
                self.copy_hidservauth_button.show()
            else:
                self.copy_hidservauth_button.hide()
        else:
            self.url_description.hide()
            self.url_label.hide()
            self.url.hide()
            self.copy_url_button.hide()
            self.copy_hidservauth_button.hide()

        # Hide the FileList delete buttons when a share is running
        if self.status == self.STATUS_STARTED or self.status == self.STATUS_WORKING:
            for index in range(self.file_selection.file_list.count()):
                self.file_selection.file_list.item(index).item_button.hide()
        else:
            for index in range(self.file_selection.file_list.count()):
                self.file_selection.file_list.item(index).item_button.show()

        # Button
        button_stopped_style = 'QPushButton { background-color: #5fa416; color: #ffffff; padding: 10px; border: 0; border-radius: 5px; }'
        button_working_style = 'QPushButton { background-color: #4c8211; color: #ffffff; padding: 10px; border: 0; border-radius: 5px; font-style: italic; }'
        button_started_style = 'QPushButton { background-color: #d0011b; color: #ffffff; padding: 10px; border: 0; border-radius: 5px; }'
        if self.file_selection.get_num_files() == 0:
            self.server_button.hide()
        else:
            self.server_button.show()

            if self.status == self.STATUS_STOPPED:
                self.server_shutdown_timeout_checkbox.show()
                self.server_shutdown_timeout_container.show()
            else:
                self.server_shutdown_timeout_checkbox.hide()
                if self.server_shutdown_timeout_checkbox.isChecked():
                    self.server_shutdown_timeout_container.show()
                else:
                    self.server_shutdown_timeout_container.hide()

            if self.status == self.STATUS_STOPPED:
                self.server_button.setStyleSheet(button_stopped_style)
                self.server_button.setEnabled(True)
                self.server_button.setText(strings._('gui_start_server', True))
                self.server_shutdown_timeout.setEnabled(True)
                self.server_shutdown_timeout_checkbox.setEnabled(True)
            elif self.status == self.STATUS_STARTED:
                self.server_button.setStyleSheet(button_started_style)
                self.server_button.setEnabled(True)
                self.server_button.setText(strings._('gui_stop_server', True))
                self.server_shutdown_timeout.setEnabled(False)
                self.server_shutdown_timeout_checkbox.setEnabled(False)
            elif self.status == self.STATUS_WORKING:
                self.server_button.setStyleSheet(button_working_style)
                self.server_button.setEnabled(False)
                self.server_button.setText(strings._('gui_please_wait'))
                self.server_shutdown_timeout.setEnabled(False)
                self.server_shutdown_timeout_checkbox.setEnabled(False)
            else:
                self.server_button.setStyleSheet(button_working_style)
                self.server_button.setEnabled(False)
                self.server_button.setText(strings._('gui_please_wait'))
                self.server_shutdown_timeout.setEnabled(False)
                self.server_shutdown_timeout_checkbox.setEnabled(False)

    def server_button_clicked(self):
        """
        Toggle starting or stopping the server.
        """
        if self.status == self.STATUS_STOPPED:
            if self.timer_enabled:
                # Get the timeout chosen, stripped of its seconds. This prevents confusion if the share stops at (say) 37 seconds past the minute chosen
                self.timeout = self.server_shutdown_timeout.dateTime().toPyDateTime().replace(second=0, microsecond=0)
                # If the timeout has actually passed already before the user hit Start, refuse to start the server.
                if QtCore.QDateTime.currentDateTime().toPyDateTime() > self.timeout:
                    Alert(strings._('gui_server_timeout_expired', QtWidgets.QMessageBox.Warning))
                else:
                    self.start_server()
            else:
                self.start_server()
        elif self.status == self.STATUS_STARTED:
            self.stop_server()

    def start_server(self):
        """
        Start the server.
        """
        self.status = self.STATUS_WORKING
        self.update()
        self.server_started.emit()

    def start_server_finished(self):
        """
        The server has finished starting.
        """
        self.status = self.STATUS_STARTED
        self.copy_url()
        self.update()

    def stop_server(self):
        """
        Stop the server.
        """
        self.status = self.STATUS_WORKING
        self.shutdown_timeout_reset()
        self.update()
        self.server_stopped.emit()

    def stop_server_finished(self):
        """
        The server has finished stopping.
        """
        self.status = self.STATUS_STOPPED
        self.update()

    def copy_url(self):
        """
        Copy the onionshare URL to the clipboard.
        """
        url = 'http://{0:s}/{1:s}'.format(self.app.onion_host, self.web.slug)

        clipboard = self.qtapp.clipboard()
        clipboard.setText(url)

        self.url_copied.emit()

    def copy_hidservauth(self):
        """
        Copy the HidServAuth line to the clipboard.
        """
        clipboard = self.qtapp.clipboard()
        clipboard.setText(self.app.auth_string)

        self.hidservauth_copied.emit()
