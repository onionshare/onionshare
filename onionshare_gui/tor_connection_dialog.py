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

    def start(self):
        common.log('TorConnectionDialog', 'start')

        # If bundled tor, prepare to display Tor connection status
        if self.settings.get('connection_type') == 'bundled':
            tor_status_update = self.tor_status_update
        else:
            tor_status_update = None

        # Connect to the Onion
        self.setValue(0)
        try:
            self.onion.connect(self.settings, tor_status_update)

            # Close the dialog after connecting
            self.setValue(self.maximum())

        except BundledTorCanceled as e:
            self.cancel()

        except Exception as e:
            # Cancel connecting to Tor
            self.cancel()

            # Display the exception in an alert box
            Alert("{}\n\n{}".format(e.args[0], strings._('gui_tor_connection_error_settings', True)), QtWidgets.QMessageBox.Warning)

            # Open settings
            self.open_settings.emit()

    def tor_status_update(self, progress, summary):
        self.setValue(int(progress))
        self.setLabelText("<strong>{}</strong><br>{}".format(strings._('connecting_to_tor', True), summary))

        # Return False if the dialog was canceled
        return not self.wasCanceled()
