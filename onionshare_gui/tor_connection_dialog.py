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

from onionshare import strings, common
from onionshare.onion import *

from .alert import Alert

class TorConnectionDialog(QtWidgets.QProgressDialog):
    """
    Connecting to Tor dialog.
    """
    open_settings = QtCore.pyqtSignal()

    def __init__(self, settings, onion):
        super(TorConnectionDialog, self).__init__(None)
        common.log('TorConnectionDialog', '__init__')

        self.settings = settings
        self.onion = onion

        self.setWindowTitle("OnionShare")
        self.setWindowIcon(QtGui.QIcon(common.get_resource_path('images/logo.png')))
        self.setModal(True)
        self.setFixedSize(400, 150)

        # Label
        self.setLabelText(strings._('connecting_to_tor', True))

        # Progress bar ticks from 0 to 100
        self.setRange(0, 100)
        # Don't show if connection takes less than 100ms (for non-bundled tor)
        self.setMinimumDuration(100)

        # Start displaying the status at 0
        self.tor_status_update(0, '')

    def start(self):
        common.log('TorConnectionDialog', 'start')

        t = TorConnectionThread(self, self.settings, self.onion)
        t.tor_status_update.connect(self.tor_status_update)
        t.connected_to_tor.connect(self.connected_to_tor)
        t.canceled_connecting_to_tor.connect(self.canceled_connecting_to_tor)
        t.error_connecting_to_tor.connect(self.error_connecting_to_tor)
        t.start()

        # Wait for the thread to start
        time.sleep(0.1)

    def tor_status_update(self, progress, summary):
        self.setValue(int(progress))
        self.setLabelText("<strong>{}</strong><br>{}".format(strings._('connecting_to_tor', True), summary))

    def connected_to_tor(self):
        common.log('TorConnectionDialog', 'connected_to_tor')

        # Close the dialog after connecting
        self.setValue(self.maximum())

    def canceled_connecting_to_tor(self):
        common.log('TorConnectionDialog', 'canceled_connecting_to_tor')

        # Cancel connecting to Tor
        self.cancel()

    def error_connecting_to_tor(self):
        common.log('TorConnectionDialog', 'error_connecting_to_tor')

        # Cancel connecting to Tor
        self.cancel()

        # Display the exception in an alert box
        Alert("{}\n\n{}".format(e.args[0], strings._('gui_tor_connection_error_settings', True)), QtWidgets.QMessageBox.Warning)

        # Open settings
        self.open_settings.emit()

class TorConnectionThread(QtCore.QThread):
    tor_status_update = QtCore.pyqtSignal(str, str)
    connected_to_tor = QtCore.pyqtSignal()
    canceled_connecting_to_tor = QtCore.pyqtSignal()
    error_connecting_to_tor = QtCore.pyqtSignal(str)

    def __init__(self, dialog, settings, onion):
        super(TorConnectionThread, self).__init__()
        common.log('TorConnectionThread', '__init__')

        self.dialog = dialog
        self.settings = settings
        self.onion = onion

    def run(self):
        common.log('TorConnectionThread', 'run')

        # Connect to the Onion
        try:
            common.log('TorConnectionThread', 'run', 'about to run onion.connect')
            self.onion.connect(self.settings, self._tor_status_update)
            common.log('TorConnectionThread', 'run', 'onion.connect succeeded')
            self.connected_to_tor.emit()

        except BundledTorCanceled as e:
            self.canceled_connecting_to_tor.emit()

        except Exception as e:
            self.error_connecting_to_tor.emit(e.args[0])

    def _tor_status_update(self, progress, summary):
        self.tor_status_update.emit(progress, summary)

        # Return False if the dialog was canceled
        return not self.dialog.wasCanceled()
