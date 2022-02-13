# -*- coding: utf-8 -*-
"""
OnionShare | https://onionshare.org/

Copyright (C) 2014-2022 Micah Lee, et al. <micah@micahflee.com>

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
from PySide2 import QtCore, QtWidgets

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


class TorConnectionWidget(QtWidgets.QWidget):
    """
    Connecting to Tor widget, with a progress bar
    """

    open_tor_settings = QtCore.Signal()
    success = QtCore.Signal()
    fail = QtCore.Signal(str)
    update_progress = QtCore.Signal(int)

    def __init__(self, common, status_bar):
        super(TorConnectionWidget, self).__init__(None)
        self.common = common
        self.common.log("TorConnectionWidget", "__init__")

        self.status_bar = status_bar
        self.label = QtWidgets.QLabel(strings._("connecting_to_tor"))
        self.label.setAlignment(QtCore.Qt.AlignHCenter)

        self.progress = QtWidgets.QProgressBar()
        self.progress.setRange(0, 100)
        self.cancel_button = QtWidgets.QPushButton(
            strings._("gui_settings_button_cancel")
        )
        self.cancel_button.clicked.connect(self.cancel_clicked)

        progress_layout = QtWidgets.QHBoxLayout()
        progress_layout.addWidget(self.progress)
        progress_layout.addWidget(self.cancel_button)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.label)
        layout.addLayout(progress_layout)

        self.setLayout(layout)

        # Start displaying the status at 0
        self._tor_status_update(0, "")

    def start(self, custom_settings=False, testing_settings=False, onion=None):
        self.common.log("TorConnectionWidget", "start")
        self.was_canceled = False

        self.testing_settings = testing_settings

        if custom_settings:
            self.settings = custom_settings
        else:
            self.settings = self.common.settings

        if self.testing_settings:
            self.onion = onion
        else:
            self.onion = self.common.gui.onion

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

    def cancel_clicked(self):
        self.was_canceled = True
        self.fail.emit("")
        self._reset()

    def wasCanceled(self):
        return self.was_canceled

    def _tor_status_update(self, progress, summary):
        self.progress.setValue(int(progress))
        self.update_progress.emit(int(progress))
        self.label.setText(
            f"<strong>{strings._('connecting_to_tor')}</strong><br>{summary}"
        )

    def _connected_to_tor(self):
        self.common.log("TorConnectionWidget", "_connected_to_tor")
        self.active = False
        self.status_bar.clearMessage()

        # Close the dialog after connecting
        self.progress.setValue(self.progress.maximum())
        self.update_progress.emit(int(self.progress.maximum()))

        self.success.emit()
        self._reset()

    def _canceled_connecting_to_tor(self):
        self.common.log("TorConnectionWidget", "_canceled_connecting_to_tor")
        self.active = False
        self.onion.cleanup()

        # Cancel connecting to Tor
        QtCore.QTimer.singleShot(1, self.cancel_clicked)
        self._reset()

    def _error_connecting_to_tor(self, msg):
        self.common.log("TorConnectionWidget", "_error_connecting_to_tor")
        self.active = False
        self.fail.emit(msg)
        self._reset()

    def _reset(self):
        self.label.setText("")
        self.progress.setValue(0)
        self.update_progress.emit(0)


class TorConnectionThread(QtCore.QThread):
    tor_status_update = QtCore.Signal(str, str)
    connected_to_tor = QtCore.Signal()
    canceled_connecting_to_tor = QtCore.Signal()
    error_connecting_to_tor = QtCore.Signal(str)

    def __init__(self, common, settings, parent):
        super(TorConnectionThread, self).__init__()
        self.common = common
        self.common.log("TorConnectionThread", "__init__")
        self.settings = settings
        self.parent = parent

    def run(self):
        self.common.log("TorConnectionThread", "run")

        # Connect to the Onion
        try:
            self.parent.onion.connect(self.settings, False, self._tor_status_update)
            if self.parent.onion.connected_to_tor:
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
        return not self.parent.wasCanceled()
