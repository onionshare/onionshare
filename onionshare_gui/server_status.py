# -*- coding: utf-8 -*-
"""
OnionShare | https://onionshare.org/

Copyright (C) 2014-2018 Micah Lee <micah@micahflee.com>

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
import textwrap
from PyQt5 import QtCore, QtWidgets, QtGui

from onionshare import strings

from .widgets import Alert

class ServerStatus(QtWidgets.QWidget):
    """
    The server status chunk of the GUI.
    """
    server_started = QtCore.pyqtSignal()
    server_started_finished = QtCore.pyqtSignal()
    server_stopped = QtCore.pyqtSignal()
    server_canceled = QtCore.pyqtSignal()
    button_clicked = QtCore.pyqtSignal()
    url_copied = QtCore.pyqtSignal()
    hidservauth_copied = QtCore.pyqtSignal()

    MODE_SHARE = 'share'
    MODE_RECEIVE = 'receive'

    STATUS_STOPPED = 0
    STATUS_WORKING = 1
    STATUS_STARTED = 2

    def __init__(self, common, qtapp, app, file_selection=None, local_only=False):
        super(ServerStatus, self).__init__()

        self.common = common

        self.status = self.STATUS_STOPPED
        self.mode = None # Gets set in self.set_mode

        self.qtapp = qtapp
        self.app = app

        self.web = None
        self.autostart_timer_datetime = None
        self.local_only = local_only

        self.resizeEvent(None)

        # Auto-start timer layout
        self.autostart_timer_label = QtWidgets.QLabel(strings._('gui_settings_autostart_timer'))
        self.autostart_timer_widget = QtWidgets.QDateTimeEdit()
        self.autostart_timer_widget.setDisplayFormat("hh:mm A MMM d, yy")
        if self.local_only:
            # For testing
            self.autostart_timer_widget.setDateTime(QtCore.QDateTime.currentDateTime().addSecs(15))
            self.autostart_timer_widget.setMinimumDateTime(QtCore.QDateTime.currentDateTime())
        else:
            # Set proposed timer to be 5 minutes into the future
            self.autostart_timer_widget.setDateTime(QtCore.QDateTime.currentDateTime().addSecs(300))
            # Onion services can take a little while to start, so reduce the risk of it expiring too soon by setting the minimum to 60s from now
            self.autostart_timer_widget.setMinimumDateTime(QtCore.QDateTime.currentDateTime().addSecs(60))
        self.autostart_timer_widget.setCurrentSection(QtWidgets.QDateTimeEdit.MinuteSection)
        autostart_timer_layout = QtWidgets.QHBoxLayout()
        autostart_timer_layout.addWidget(self.autostart_timer_label)
        autostart_timer_layout.addWidget(self.autostart_timer_widget)

        # Auto-start timer container, so it can all be hidden and shown as a group
        autostart_timer_container_layout = QtWidgets.QVBoxLayout()
        autostart_timer_container_layout.addLayout(autostart_timer_layout)
        self.autostart_timer_container = QtWidgets.QWidget()
        self.autostart_timer_container.setLayout(autostart_timer_container_layout)
        self.autostart_timer_container.hide()

        # Auto-stop timer layout
        self.autostop_timer_label = QtWidgets.QLabel(strings._('gui_settings_autostop_timer'))
        self.autostop_timer_widget = QtWidgets.QDateTimeEdit()
        self.autostop_timer_widget.setDisplayFormat("hh:mm A MMM d, yy")
        if self.local_only:
            # For testing
            self.autostop_timer_widget.setDateTime(QtCore.QDateTime.currentDateTime().addSecs(15))
            self.autostop_timer_widget.setMinimumDateTime(QtCore.QDateTime.currentDateTime())
        else:
            # Set proposed timer to be 5 minutes into the future
            self.autostop_timer_widget.setDateTime(QtCore.QDateTime.currentDateTime().addSecs(300))
            # Onion services can take a little while to start, so reduce the risk of it expiring too soon by setting the minimum to 60s from now
            self.autostop_timer_widget.setMinimumDateTime(QtCore.QDateTime.currentDateTime().addSecs(60))
        self.autostop_timer_widget.setCurrentSection(QtWidgets.QDateTimeEdit.MinuteSection)
        autostop_timer_layout = QtWidgets.QHBoxLayout()
        autostop_timer_layout.addWidget(self.autostop_timer_label)
        autostop_timer_layout.addWidget(self.autostop_timer_widget)

        # Auto-stop timer container, so it can all be hidden and shown as a group
        autostop_timer_container_layout = QtWidgets.QVBoxLayout()
        autostop_timer_container_layout.addLayout(autostop_timer_layout)
        self.autostop_timer_container = QtWidgets.QWidget()
        self.autostop_timer_container.setLayout(autostop_timer_container_layout)
        self.autostop_timer_container.hide()

        # Server layout
        self.server_button = QtWidgets.QPushButton()
        self.server_button.clicked.connect(self.server_button_clicked)

        # URL layout
        url_font = QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.FixedFont)
        self.url_description = QtWidgets.QLabel()
        self.url_description.setWordWrap(True)
        self.url_description.setMinimumHeight(50)
        self.url = QtWidgets.QLabel()
        self.url.setFont(url_font)
        self.url.setWordWrap(True)
        self.url.setMinimumSize(self.url.sizeHint())
        self.url.setStyleSheet(self.common.css['server_status_url'])

        self.copy_url_button = QtWidgets.QPushButton(strings._('gui_copy_url'))
        self.copy_url_button.setFlat(True)
        self.copy_url_button.setStyleSheet(self.common.css['server_status_url_buttons'])
        self.copy_url_button.setMinimumHeight(65)
        self.copy_url_button.clicked.connect(self.copy_url)
        self.copy_hidservauth_button = QtWidgets.QPushButton(strings._('gui_copy_hidservauth'))
        self.copy_hidservauth_button.setFlat(True)
        self.copy_hidservauth_button.setStyleSheet(self.common.css['server_status_url_buttons'])
        self.copy_hidservauth_button.clicked.connect(self.copy_hidservauth)
        url_buttons_layout = QtWidgets.QHBoxLayout()
        url_buttons_layout.addWidget(self.copy_url_button)
        url_buttons_layout.addWidget(self.copy_hidservauth_button)
        url_buttons_layout.addStretch()

        url_layout = QtWidgets.QVBoxLayout()
        url_layout.addWidget(self.url_description)
        url_layout.addWidget(self.url)
        url_layout.addLayout(url_buttons_layout)

        # Add the widgets
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.server_button)
        layout.addLayout(url_layout)
        layout.addWidget(self.autostart_timer_container)
        layout.addWidget(self.autostop_timer_container)
        self.setLayout(layout)

    def set_mode(self, share_mode, file_selection=None):
        """
        The server status is in share mode.
        """
        self.mode = share_mode

        if self.mode == ServerStatus.MODE_SHARE:
            self.file_selection = file_selection

        self.update()

    def resizeEvent(self, event):
        """
        When the widget is resized, try and adjust the display of a v3 onion URL.
        """
        try:
            # Wrap the URL label
            url_length=len(self.get_url())
            if url_length > 60:
                width = self.frameGeometry().width()
                if width < 530:
                    wrapped_onion_url = textwrap.fill(self.get_url(), 46)
                    self.url.setText(wrapped_onion_url)
                else:
                    self.url.setText(self.get_url())
        except:
            pass

    def autostart_timer_reset(self):
        """
        Reset the auto-start timer in the UI after stopping a share
        """
        self.autostart_timer_widget.setDateTime(QtCore.QDateTime.currentDateTime().addSecs(300))
        if not self.local_only:
            self.autostart_timer_widget.setMinimumDateTime(QtCore.QDateTime.currentDateTime().addSecs(60))

    def autostop_timer_reset(self):
        """
        Reset the auto-stop timer in the UI after stopping a share
        """
        self.autostop_timer_widget.setDateTime(QtCore.QDateTime.currentDateTime().addSecs(300))
        if not self.local_only:
            self.autostop_timer_widget.setMinimumDateTime(QtCore.QDateTime.currentDateTime().addSecs(60))

    def show_url(self):
        """
        Show the URL in the UI.
        """
        self.url_description.show()

        info_image = self.common.get_resource_path('images/info.png')

        if self.mode == ServerStatus.MODE_SHARE:
            self.url_description.setText(strings._('gui_share_url_description').format(info_image))
        else:
            self.url_description.setText(strings._('gui_receive_url_description').format(info_image))

        # Show a Tool Tip explaining the lifecycle of this URL
        if self.common.settings.get('save_private_key'):
            if self.mode == ServerStatus.MODE_SHARE and self.common.settings.get('close_after_first_download'):
                self.url_description.setToolTip(strings._('gui_url_label_onetime_and_persistent'))
            else:
                self.url_description.setToolTip(strings._('gui_url_label_persistent'))
        else:
            if self.mode == ServerStatus.MODE_SHARE and self.common.settings.get('close_after_first_download'):
                self.url_description.setToolTip(strings._('gui_url_label_onetime'))
            else:
                self.url_description.setToolTip(strings._('gui_url_label_stay_open'))

        self.url.setText(self.get_url())
        self.url.show()
        self.copy_url_button.show()

        if self.app.stealth:
            self.copy_hidservauth_button.show()
        else:
            self.copy_hidservauth_button.hide()

    def update(self):
        """
        Update the GUI elements based on the current state.
        """
        # Set the URL fields
        if self.status == self.STATUS_STARTED:
            self.show_url()

            if self.common.settings.get('save_private_key'):
                if not self.common.settings.get('slug'):
                    self.common.settings.set('slug', self.web.slug)
                    self.common.settings.save()

            if self.common.settings.get('autostart_timer'):
                self.autostart_timer_container.hide()

            if self.common.settings.get('autostop_timer'):
                self.autostop_timer_container.hide()
        else:
            self.url_description.hide()
            self.url.hide()
            self.copy_url_button.hide()
            self.copy_hidservauth_button.hide()

        # Button
        if self.mode == ServerStatus.MODE_SHARE and self.file_selection.get_num_files() == 0:
            self.server_button.hide()
        else:
            self.server_button.show()

            if self.status == self.STATUS_STOPPED:
                self.server_button.setStyleSheet(self.common.css['server_status_button_stopped'])
                self.server_button.setEnabled(True)
                if self.mode == ServerStatus.MODE_SHARE:
                    self.server_button.setText(strings._('gui_share_start_server'))
                else:
                    self.server_button.setText(strings._('gui_receive_start_server'))
                self.server_button.setToolTip('')
                if self.common.settings.get('autostart_timer'):
                    self.autostart_timer_container.show()
                if self.common.settings.get('autostop_timer'):
                    self.autostop_timer_container.show()
            elif self.status == self.STATUS_STARTED:
                self.server_button.setStyleSheet(self.common.css['server_status_button_started'])
                self.server_button.setEnabled(True)
                if self.mode == ServerStatus.MODE_SHARE:
                    self.server_button.setText(strings._('gui_share_stop_server'))
                else:
                    self.server_button.setText(strings._('gui_receive_stop_server'))
                if self.common.settings.get('autostart_timer'):
                    self.autostart_timer_container.hide()
                if self.common.settings.get('autostop_timer'):
                    self.autostop_timer_container.hide()
                    self.server_button.setToolTip(strings._('gui_stop_server_autostop_timer_tooltip').format(self.autostop_timer_widget.dateTime().toString("H:mmAP, MMM dd, yy")))
            elif self.status == self.STATUS_WORKING:
                self.server_button.setStyleSheet(self.common.css['server_status_button_working'])
                self.server_button.setEnabled(True)
                if self.autostart_timer_datetime:
                    self.autostart_timer_container.hide()
                    self.server_button.setToolTip(strings._('gui_start_server_autostart_timer_tooltip').format(self.autostart_timer_widget.dateTime().toString("H:mmAP, MMM dd, yy")))
                else:
                    self.server_button.setText(strings._('gui_please_wait'))
                if self.common.settings.get('autostop_timer'):
                    self.autostop_timer_container.hide()
            else:
                self.server_button.setStyleSheet(self.common.css['server_status_button_working'])
                self.server_button.setEnabled(False)
                self.server_button.setText(strings._('gui_please_wait'))
                if self.common.settings.get('autostart_timer'):
                    self.autostart_timer_container.hide()
                    self.server_button.setToolTip(strings._('gui_start_server_autostart_timer_tooltip').format(self.autostart_timer_widget.dateTime().toString("H:mmAP, MMM dd, yy")))
                if self.common.settings.get('autostop_timer'):
                    self.autostop_timer_container.hide()

    def server_button_clicked(self):
        """
        Toggle starting or stopping the server.
        """
        if self.status == self.STATUS_STOPPED:
            can_start = True
            if self.common.settings.get('autostart_timer'):
                if self.local_only:
                    self.autostart_timer_datetime = self.autostart_timer_widget.dateTime().toPyDateTime()
                else:
                    self.autostart_timer_datetime = self.autostart_timer_widget.dateTime().toPyDateTime().replace(second=0, microsecond=0)
                # If the timer has actually passed already before the user hit Start, refuse to start the server.
                if QtCore.QDateTime.currentDateTime().toPyDateTime() > self.autostart_timer_datetime:
                    can_start = False
                    Alert(self.common, strings._('gui_server_autostart_timer_expired'), QtWidgets.QMessageBox.Warning)
            if self.common.settings.get('autostop_timer'):
                if self.local_only:
                    self.autostop_timer_datetime = self.autostop_timer_widget.dateTime().toPyDateTime()
                else:
                    # Get the timer chosen, stripped of its seconds. This prevents confusion if the share stops at (say) 37 seconds past the minute chosen
                    self.autostop_timer_datetime = self.autostop_timer_widget.dateTime().toPyDateTime().replace(second=0, microsecond=0)
                # If the timer has actually passed already before the user hit Start, refuse to start the server.
                if QtCore.QDateTime.currentDateTime().toPyDateTime() > self.autostop_timer_datetime:
                    can_start = False
                    Alert(self.common, strings._('gui_server_autostop_timer_expired'), QtWidgets.QMessageBox.Warning)
                if self.common.settings.get('autostart_timer'):
                    if self.autostop_timer_datetime <= self.autostart_timer_datetime:
                        Alert(self.common, strings._('gui_autostop_timer_cant_be_earlier_than_autostart_timer'), QtWidgets.QMessageBox.Warning)
                        can_start = False
            if can_start:
                self.start_server()
        elif self.status == self.STATUS_STARTED:
            self.stop_server()
        elif self.status == self.STATUS_WORKING:
            self.cancel_server()
        self.button_clicked.emit()

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
        self.server_started_finished.emit()

    def stop_server(self):
        """
        Stop the server.
        """
        self.status = self.STATUS_WORKING
        self.autostart_timer_reset()
        self.autostop_timer_reset()
        self.update()
        self.server_stopped.emit()

    def cancel_server(self):
        """
        Cancel the server.
        """
        self.common.log('ServerStatus', 'cancel_server', 'Canceling the server mid-startup')
        self.status = self.STATUS_WORKING
        self.autostart_timer_reset()
        self.autostop_timer_reset()
        self.update()
        self.server_canceled.emit()

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
        clipboard = self.qtapp.clipboard()
        clipboard.setText(self.get_url())

        self.url_copied.emit()

    def copy_hidservauth(self):
        """
        Copy the HidServAuth line to the clipboard.
        """
        clipboard = self.qtapp.clipboard()
        clipboard.setText(self.app.auth_string)

        self.hidservauth_copied.emit()

    def get_url(self):
        """
        Returns the OnionShare URL.
        """
        if self.common.settings.get('public_mode'):
            url = 'http://{0:s}'.format(self.app.onion_host)
        else:
            url = 'http://{0:s}/{1:s}'.format(self.app.onion_host, self.web.slug)
        return url
