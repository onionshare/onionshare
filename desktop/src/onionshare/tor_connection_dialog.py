# -*- coding: utf-8 -*-
"""
OnionShare | https://onionshare.org/

Copyright (C) 2014-2021 Micah Lee, et al. <micah@micahflee.com>

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
from PySide2 import QtCore, QtWidgets, QtGui

from onionshare_cli.onion import (
    BundledTorCanceled,
    TorErrorInvalidSetting,
    TorErrorAutomatic,
    TorErrorSocketPort,
    TorErrorSocketFile,
    TorErrorMissingPassword,
    TorErrorUnreadableCookieFile,
    TorErrorAuthError,
    TorErrorProtocolError,
    BundledTorTimeout,
    BundledTorBroken,
    TorTooOldEphemeral,
    TorTooOldStealth,
    PortNotAvailable,
)

from . import strings
from .gui_common import GuiCommon
from .widgets import Alert


class TorConnectionDialog(QtWidgets.QProgressDialog):
    """
    Connecting to Tor dialog.
    """

    open_settings = QtCore.Signal()

    def __init__(self, common, custom_settings=False):
        super(TorConnectionDialog, self).__init__(None)

        self.common = common

        if custom_settings:
            self.settings = custom_settings
        else:
            self.settings = self.common.settings

        self.common.log("TorConnectionDialog", "__init__")

        self.setWindowTitle("OnionShare")
        self.setWindowIcon(QtGui.QIcon(GuiCommon.get_resource_path("images/logo.png")))
        self.setModal(True)
        self.setFixedSize(400, 150)

        # Label
        self.setLabelText(strings._("connecting_to_tor"))

        # Progress bar ticks from 0 to 100
        self.setRange(0, 100)
        # Don't show if connection takes less than 100ms (for non-bundled tor)
        self.setMinimumDuration(100)

        # Start displaying the status at 0
        self._tor_status_update(0, "")

    def start(self):
        self.common.log("TorConnectionDialog", "start")

        t = TorConnectionThread(self.common, self.settings, self)
        t.tor_status_update.connect(self._tor_status_update)
        t.connected_to_tor.connect(self._connected_to_tor)
        t.canceled_connecting_to_tor.connect(self._canceled_connecting_to_tor)
        t.error_connecting_to_tor.connect(self._error_connecting_to_tor)
        t.start()

        # The main thread needs to remain active, and checking for Qt events,
        # until the thread is finished. Otherwise it won't be able to handle
        # accepting signals.
        self.active = True
        while self.active:
            time.sleep(0.1)
            self.common.gui.qtapp.processEvents()

    def _tor_status_update(self, progress, summary):
        self.setValue(int(progress))
        self.setLabelText(
            f"<strong>{strings._('connecting_to_tor')}</strong><br>{summary}"
        )

    def _connected_to_tor(self):
        self.common.log("TorConnectionDialog", "_connected_to_tor")
        self.active = False

        # Close the dialog after connecting
        self.setValue(self.maximum())

    def _canceled_connecting_to_tor(self):
        self.common.log("TorConnectionDialog", "_canceled_connecting_to_tor")
        self.active = False
        self.common.gui.onion.cleanup()

        # Cancel connecting to Tor
        QtCore.QTimer.singleShot(1, self.cancel)

    def _error_connecting_to_tor(self, msg):
        self.common.log("TorConnectionDialog", "_error_connecting_to_tor")
        self.active = False

        def alert_and_open_settings():
            # Display the exception in an alert box
            Alert(
                self.common,
                f"{msg}\n\n{strings._('gui_tor_connection_error_settings')}",
                QtWidgets.QMessageBox.Warning,
            )

            # Open settings
            self.open_settings.emit()

        QtCore.QTimer.singleShot(1, alert_and_open_settings)

        # Cancel connecting to Tor
        QtCore.QTimer.singleShot(1, self.cancel)


class TorConnectionThread(QtCore.QThread):
    tor_status_update = QtCore.Signal(str, str)
    connected_to_tor = QtCore.Signal()
    canceled_connecting_to_tor = QtCore.Signal()
    error_connecting_to_tor = QtCore.Signal(str)

    def __init__(self, common, settings, dialog):
        super(TorConnectionThread, self).__init__()

        self.common = common

        self.common.log("TorConnectionThread", "__init__")

        self.settings = settings

        self.dialog = dialog

    def run(self):
        self.common.log("TorConnectionThread", "run")

        # Connect to the Onion
        try:
            self.common.gui.onion.connect(self.settings, False, self._tor_status_update)
            if self.common.gui.onion.connected_to_tor:
                self.connected_to_tor.emit()
            else:
                self.canceled_connecting_to_tor.emit()

        except BundledTorCanceled:
            self.common.log(
                "TorConnectionThread", "run", "caught exception: BundledTorCanceled"
            )
            self.canceled_connecting_to_tor.emit()

        except (
            TorErrorInvalidSetting,
            TorErrorAutomatic,
            TorErrorSocketPort,
            TorErrorSocketFile,
            TorErrorMissingPassword,
            TorErrorUnreadableCookieFile,
            TorErrorAuthError,
            TorErrorProtocolError,
            BundledTorTimeout,
            BundledTorBroken,
            TorTooOldEphemeral,
            TorTooOldStealth,
            PortNotAvailable,
        ) as e:
            message = self.common.gui.get_translated_tor_error(e)
            self.common.log(
                "TorConnectionThread", "run", f"caught exception: {message}"
            )
            self.error_connecting_to_tor.emit(message)

    def _tor_status_update(self, progress, summary):
        self.tor_status_update.emit(progress, summary)

        # Return False if the dialog was canceled
        return not self.dialog.wasCanceled()
