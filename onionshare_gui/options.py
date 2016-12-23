# -*- coding: utf-8 -*-
"""
OnionShare | https://onionshare.org/

Copyright (C) 2016 Micah Lee <micah@micahflee.com>

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
from PyQt5 import QtCore, QtWidgets

from onionshare import strings, helpers

class Options(QtWidgets.QVBoxLayout):
    """
    The extra onionshare options in the GUI.
    """
    def __init__(self, web, app):
        super(Options, self).__init__()

        self.web = web
        self.app = app

        # close automatically
        self.close_automatically = QtWidgets.QCheckBox()
        if self.web.stay_open:
            self.close_automatically.setCheckState(QtCore.Qt.Unchecked)
        else:
            self.close_automatically.setCheckState(QtCore.Qt.Checked)
        self.close_automatically.setText(strings._("close_on_finish", True))
        self.close_automatically.stateChanged.connect(self.stay_open_changed)

        # stealth
        self.stealth = QtWidgets.QCheckBox()
        self.stealth.setCheckState(QtCore.Qt.Unchecked)
        self.stealth.setText(strings._("create_stealth", True))
        self.stealth.stateChanged.connect(self.stealth_changed)

        # add the widgets
        self.addWidget(self.close_automatically)
        self.addWidget(self.stealth)

    def stay_open_changed(self, state):
        """
        When the 'close automatically' checkbox is toggled, let the web app know.
        """
        if state > 0:
            self.web.set_stay_open(False)
            self.app.stay_open = False
        else:
            self.web.set_stay_open(True)
            self.app.stay_open = True

    def stealth_changed(self, state):
        """
        When the 'stealth' checkbox is toggled, let the onionshare app know.
        """
        if state == 2:
            self.app.stealth = True
        else:
            self.app.stealth = False

    def set_stealth_enabled(self, enabled):
        """
        You cannot toggle stealth after an onion service has started. This method
        disables and re-enabled the stealth checkbox.
        """
        self.stealth.setEnabled(enabled)
