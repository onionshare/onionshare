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
from PyQt5 import QtCore, QtWidgets, QtGui

from onionshare import strings, common

class ServerStatus(QtWidgets.QVBoxLayout):
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

    def __init__(self, qtapp, app, web, file_selection):
        super(ServerStatus, self).__init__()
        self.status = self.STATUS_STOPPED

        self.qtapp = qtapp
        self.app = app
        self.web = web
        self.file_selection = file_selection

        # server layout
        self.status_image_stopped = QtGui.QImage(common.get_resource_path('images/server_stopped.png'))
        self.status_image_working = QtGui.QImage(common.get_resource_path('images/server_working.png'))
        self.status_image_started = QtGui.QImage(common.get_resource_path('images/server_started.png'))
        self.status_image_label = QtWidgets.QLabel()
        self.status_image_label.setFixedWidth(30)
        self.server_button = QtWidgets.QPushButton()
        self.server_button.clicked.connect(self.server_button_clicked)
        server_layout = QtWidgets.QHBoxLayout()
        server_layout.addWidget(self.status_image_label)
        server_layout.addWidget(self.server_button)

        # url layout
        self.reveal_url_button = QtWidgets.QPushButton(strings._('gui_reveal_url', True))
        self.reveal_url_button.setCheckable(True)
        self.reveal_url_button.toggled.connect(self.reveal_url_toggled)
        self.copy_url_button = QtWidgets.QPushButton(strings._('gui_copy_url', True))
        self.copy_url_button.clicked.connect(self.copy_url)
        self.copy_hidservauth_button = QtWidgets.QPushButton(strings._('gui_copy_hidservauth', True))
        self.copy_hidservauth_button.clicked.connect(self.copy_hidservauth)
        url_layout = QtWidgets.QHBoxLayout()
        url_layout.addWidget(self.reveal_url_button)
        url_layout.addWidget(self.copy_url_button)
        url_layout.addWidget(self.copy_hidservauth_button)

        # add the widgets
        self.addLayout(server_layout)
        self.addLayout(url_layout)

        self.update()

    def update(self):
        """
        Update the GUI elements based on the current state.
        """
        # set the status image
        if self.status == self.STATUS_STOPPED:
            self.status_image_label.setPixmap(QtGui.QPixmap.fromImage(self.status_image_stopped))
        elif self.status == self.STATUS_WORKING:
            self.status_image_label.setPixmap(QtGui.QPixmap.fromImage(self.status_image_working))
        elif self.status == self.STATUS_STARTED:
            self.status_image_label.setPixmap(QtGui.QPixmap.fromImage(self.status_image_started))

        # set the URL fields
        if self.status == self.STATUS_STARTED:
            self.reveal_url_button.show()
            self.copy_url_button.show()

            if self.app.stealth:
                self.copy_hidservauth_button.show()
            else:
                self.copy_hidservauth_button.hide()

            # resize parent widget
            p = self.parentWidget()
            p.resize(p.sizeHint())
        else:
            self.reveal_url_button.hide()
            self.copy_url_button.hide()
            self.copy_hidservauth_button.hide()

        # button
        if self.file_selection.get_num_files() == 0:
            self.server_button.setEnabled(False)
            self.server_button.setText(strings._('gui_start_server', True))
        else:
            if self.status == self.STATUS_STOPPED:
                self.server_button.setEnabled(True)
                self.server_button.setText(strings._('gui_start_server', True))
            elif self.status == self.STATUS_STARTED:
                self.server_button.setEnabled(True)
                self.server_button.setText(strings._('gui_stop_server', True))
            else:
                self.server_button.setEnabled(False)
                self.server_button.setText(strings._('gui_please_wait'))

    def server_button_clicked(self):
        """
        Toggle starting or stopping the server.
        """
        if self.status == self.STATUS_STOPPED:
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
        self.update()
        self.server_stopped.emit()

    def stop_server_finished(self):
        """
        The server has finished stopping.
        """
        self.status = self.STATUS_STOPPED
        self.update()

    def reveal_url_toggled(self, checked):
        """
        Toggle the 'Reveal URL' button to either
        show the Onion URL or hide it
        """
        common.log('OnionShareGui', 'reveal_url_toggled', 'URL reveal button was clicked')
        if checked:
            self.reveal_url_button.setText('http://{0:s}/{1:s}'.format(self.app.onion_host, self.web.slug))
        else:
            self.reveal_url_button.setText(strings._('gui_reveal_url', True))

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
