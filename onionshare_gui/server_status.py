# -*- coding: utf-8 -*-
"""
OnionShare | https://onionshare.org/

Copyright (C) 2014 Micah Lee <micah@micahflee.com>

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
from PyQt4 import QtCore, QtGui

import common
from onionshare import strings, helpers

class ServerStatus(QtGui.QVBoxLayout):
    server_started = QtCore.pyqtSignal()
    server_stopped = QtCore.pyqtSignal()
    url_copied = QtCore.pyqtSignal()

    STATUS_STOPPED = 0
    STATUS_WORKING = 1
    STATUS_STARTED = 2

    def __init__(self, qtapp, app, web, file_selection):
        super(ServerStatus, self).__init__()
        self.status = self.STATUS_STOPPED
        self.addSpacing(10)

        self.qtapp = qtapp
        self.app = app
        self.web = web
        self.file_selection = file_selection

        # server layout
        self.status_image_stopped = QtGui.QImage('{0}/server_stopped.png'.format(common.onionshare_gui_dir))
        self.status_image_working = QtGui.QImage('{0}/server_working.png'.format(common.onionshare_gui_dir))
        self.status_image_started = QtGui.QImage('{0}/server_started.png'.format(common.onionshare_gui_dir))
        self.status_image_label = QtGui.QLabel()
        self.status_image_label.setFixedWidth(30)
        self.start_server_button = QtGui.QPushButton(strings._('gui_start_server'))
        self.start_server_button.clicked.connect(self.start_server)
        self.stop_server_button = QtGui.QPushButton(strings._('gui_stop_server'))
        self.stop_server_button.clicked.connect(self.stop_server)
        server_layout = QtGui.QHBoxLayout()
        server_layout.addWidget(self.status_image_label)
        server_layout.addWidget(self.start_server_button)
        server_layout.addWidget(self.stop_server_button)

        # url layout
        url_font = QtGui.QFont()
        url_font.setPointSize(8)
        self.url_label = QtGui.QLabel()
        self.url_label.setFont(url_font)
        self.url_label.setWordWrap(True)
        self.url_label.setAlignment(QtCore.Qt.AlignCenter)
        self.copy_url_button = QtGui.QPushButton(strings._('gui_copy_url'))
        self.copy_url_button.clicked.connect(self.copy_url)
        url_layout = QtGui.QHBoxLayout()
        url_layout.addWidget(self.url_label)
        url_layout.addWidget(self.copy_url_button)

        # add the widgets
        self.addLayout(server_layout)
        self.addLayout(url_layout)

        self.update()

    def update(self):
        # set the status image
        if self.status == self.STATUS_STOPPED:
            self.status_image_label.setPixmap(QtGui.QPixmap.fromImage(self.status_image_stopped))
        elif self.status == self.STATUS_WORKING:
            self.status_image_label.setPixmap(QtGui.QPixmap.fromImage(self.status_image_working))
        elif self.status == self.STATUS_STARTED:
            self.status_image_label.setPixmap(QtGui.QPixmap.fromImage(self.status_image_started))

        # set the URL fields
        if self.status == self.STATUS_STARTED:
            self.url_label.setText('http://{0}/ {1}'.format(self.app.onion_host, self.web.slug))
            self.url_label.show()
            self.copy_url_button.show()
        else:
            self.url_label.hide()
            self.copy_url_button.hide()

        # buttons enabled
        if self.file_selection.get_num_files() == 0:
            self.start_server_button.setEnabled(False)
            self.stop_server_button.setEnabled(False)
        else:
            if self.status == self.STATUS_STOPPED:
                self.start_server_button.setEnabled(True)
                self.stop_server_button.setEnabled(False)
            elif self.status == self.STATUS_STARTED:
                self.start_server_button.setEnabled(False)
                self.stop_server_button.setEnabled(True)
            else:
                self.start_server_button.setEnabled(False)
                self.stop_server_button.setEnabled(False)

    def start_server(self):
        self.status = self.STATUS_WORKING
        self.update()
        self.server_started.emit()

    def start_server_finished(self):
        self.status = self.STATUS_STARTED
        self.copy_url()
        self.update()

    def stop_server(self):
        self.status = self.STATUS_WORKING
        self.update()
        self.server_stopped.emit()

    def stop_server_finished(self):
        self.status = self.STATUS_STOPPED
        self.update()

    def copy_url(self):
        url = 'http://{0}/{1}'.format(self.app.onion_host, self.web.slug)

        if platform.system() == 'Windows':
            # Qt's QClipboard isn't working in Windows
            # https://github.com/micahflee/onionshare/issues/46
            import ctypes
            GMEM_DDESHARE = 0x2000
            ctypes.windll.user32.OpenClipboard(None)
            ctypes.windll.user32.EmptyClipboard()
            hcd = ctypes.windll.kernel32.GlobalAlloc(GMEM_DDESHARE, len(bytes(url))+1)
            pch_data = ctypes.windll.kernel32.GlobalLock(hcd)
            ctypes.cdll.msvcrt.strcpy(ctypes.c_char_p(pch_data), bytes(url))
            ctypes.windll.kernel32.GlobalUnlock(hcd)
            ctypes.windll.user32.SetClipboardData(1, hcd)
            ctypes.windll.user32.CloseClipboard()
        else:
            clipboard = self.qtapp.clipboard()
            clipboard.setText(url)

        self.url_copied.emit()

