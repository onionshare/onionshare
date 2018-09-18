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
import time
from PyQt5 import QtCore


class OnionThread(QtCore.QThread):
    """
    Starts the onion service, and waits for it to finish
    """
    success = QtCore.pyqtSignal()
    error = QtCore.pyqtSignal(str)

    def __init__(self, mode):
        super(OnionThread, self).__init__()
        self.mode = mode
        self.mode.common.log('OnionThread', '__init__')

        # allow this thread to be terminated
        self.setTerminationEnabled()

    def run(self):
        self.mode.common.log('OnionThread', 'run')

        try:
            self.mode.app.start_onion_service()
            self.success.emit()

        except (TorTooOld, TorErrorInvalidSetting, TorErrorAutomatic, TorErrorSocketPort, TorErrorSocketFile, TorErrorMissingPassword, TorErrorUnreadableCookieFile, TorErrorAuthError, TorErrorProtocolError, BundledTorTimeout, OSError) as e:
            self.error.emit(e.args[0])
            return

        self.mode.app.stay_open = not self.mode.common.settings.get('close_after_first_download')

        # start onionshare http service in new thread
        self.mode.web_thread = WebThread(self.mode)
        self.mode.web_thread.start()

        # wait for modules in thread to load, preventing a thread-related cx_Freeze crash
        time.sleep(0.2)


class WebThread(QtCore.QThread):
    """
    Starts the web service
    """
    success = QtCore.pyqtSignal()
    error = QtCore.pyqtSignal(str)

    def __init__(self, mode):
        super(WebThread, self).__init__()
        self.mode = mode
        self.mode.common.log('WebThread', '__init__')

    def run(self):
        self.mode.common.log('WebThread', 'run')
        self.mode.web.start(self.mode.app.port, self.mode.app.stay_open, self.mode.common.settings.get('slug'))
