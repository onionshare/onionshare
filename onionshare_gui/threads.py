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

from onionshare.onion import *


class OnionThread(QtCore.QThread):
    """
    Starts the onion service, and waits for it to finish
    """

    success = QtCore.pyqtSignal()
    success_early = QtCore.pyqtSignal()
    error = QtCore.pyqtSignal(str)

    def __init__(self, mode):
        super(OnionThread, self).__init__()
        self.mode = mode
        self.mode.common.log("OnionThread", "__init__")

        # allow this thread to be terminated
        self.setTerminationEnabled()

    def run(self):
        self.mode.common.log("OnionThread", "run")

        # Make a new static URL path for each new share
        self.mode.web.generate_static_url_path()

        # Choose port and password early, because we need them to exist in advance for scheduled shares
        self.mode.app.stay_open = not self.mode.common.settings.get(
            "close_after_first_download"
        )
        if not self.mode.app.port:
            self.mode.app.choose_port()
        if not self.mode.common.settings.get("public_mode"):
            if not self.mode.web.password:
                self.mode.web.generate_password(
                    self.mode.common.settings.get("password")
                )

        try:
            if self.mode.obtain_onion_early:
                self.mode.app.start_onion_service(
                    await_publication=False, save_scheduled_key=True
                )
                # wait for modules in thread to load, preventing a thread-related cx_Freeze crash
                time.sleep(0.2)
                self.success_early.emit()
                # Unregister the onion so we can use it in the next OnionThread
                self.mode.app.onion.cleanup(False)
            else:
                self.mode.app.start_onion_service(await_publication=True)
                # wait for modules in thread to load, preventing a thread-related cx_Freeze crash
                time.sleep(0.2)
                # start onionshare http service in new thread
                self.mode.web_thread = WebThread(self.mode)
                self.mode.web_thread.start()
                self.success.emit()

        except (
            TorTooOld,
            TorErrorInvalidSetting,
            TorErrorAutomatic,
            TorErrorSocketPort,
            TorErrorSocketFile,
            TorErrorMissingPassword,
            TorErrorUnreadableCookieFile,
            TorErrorAuthError,
            TorErrorProtocolError,
            BundledTorTimeout,
            OSError,
        ) as e:
            self.error.emit(e.args[0])
            return


class WebThread(QtCore.QThread):
    """
    Starts the web service
    """

    success = QtCore.pyqtSignal()
    error = QtCore.pyqtSignal(str)

    def __init__(self, mode):
        super(WebThread, self).__init__()
        self.mode = mode
        self.mode.common.log("WebThread", "__init__")

    def run(self):
        self.mode.common.log("WebThread", "run")
        self.mode.web.start(
            self.mode.app.port,
            self.mode.app.stay_open,
            self.mode.common.settings.get("public_mode"),
            self.mode.web.password,
        )
        self.success.emit()


class AutoStartTimer(QtCore.QThread):
    """
    Waits for a prescribed time before allowing a share to start
    """

    success = QtCore.pyqtSignal()
    error = QtCore.pyqtSignal(str)

    def __init__(self, mode, canceled=False):
        super(AutoStartTimer, self).__init__()
        self.mode = mode
        self.canceled = canceled
        self.mode.common.log("AutoStartTimer", "__init__")

        # allow this thread to be terminated
        self.setTerminationEnabled()

    def run(self):
        now = QtCore.QDateTime.currentDateTime()
        autostart_timer_datetime_delta = now.secsTo(
            self.mode.server_status.autostart_timer_datetime
        )
        try:
            # Sleep until scheduled time
            while autostart_timer_datetime_delta > 0 and self.canceled == False:
                time.sleep(0.1)
                now = QtCore.QDateTime.currentDateTime()
                autostart_timer_datetime_delta = now.secsTo(
                    self.mode.server_status.autostart_timer_datetime
                )
            # Timer has now finished
            if self.canceled == False:
                self.mode.server_status.server_button.setText(
                    strings._("gui_please_wait")
                )
                self.mode.server_status_label.setText(
                    strings._("gui_status_indicator_share_working")
                )
                self.success.emit()
        except ValueError as e:
            self.error.emit(e.args[0])
            return
