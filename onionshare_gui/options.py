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

class Options(QtWidgets.QHBoxLayout):
    """
    The extra onionshare options in the GUI.
    """
    def __init__(self, web, app):
        super(Options, self).__init__()

        self.web = web
        self.app = app

        # close automatically
        self.close_automatically = QtWidgets.QCheckBox()
        self.timer_field = QtWidgets.QLineEdit()
        self.timer_field.setPlaceholderText("leave blank for no limit (hours)")
        self.timer_field.setMaxLength(5)
        self.hours = 0

        if self.web.stay_open:
            self.close_automatically.setCheckState(QtCore.Qt.Unchecked)
            self.timer_field.setReadOnly(False)
        else:
            self.close_automatically.setCheckState(QtCore.Qt.Checked)
            self.timer_field.setReadOnly(True)
        self.close_automatically.setText(strings._("close_on_finish", True))
        self.close_automatically.stateChanged.connect(self.stay_open_changed)
        self.timer_field.textChanged.connect(self.on_text_changed)
        
        # add the widgets
        self.addWidget(self.close_automatically)
        self.addWidget(self.timer_field)
    def stay_open_changed(self, state):
        """
        When the 'close automatically' checkbox is toggled, let the web app know.
        """
        if state > 0:
            self.timer_field.setReadOnly(True)
            self.web.set_stay_open(0)
            self.app.stay_open = 0
        else:
            self.timer_field.setReadOnly(False)
            if self.timer_field.text() == "":
                self.hours = 999999
            print(self.hours)
            self.web.set_stay_open(self.hours)
            self.app.stay_open = self.hours
            self.app.t_cas = helpers.close_after_seconds(self.hours)

    def on_text_changed(self,state):
        """
        When the state of the QLineBox is altered, let the web app know.
        """
        text = self.timer_field.text()
        h = text if text != "" else 999999 # if field empty, no bound to timer.
        try:
            self.hours = int(h)
            self.web.set_stay_open(self.hours)
            self.app.stay_open = self.hours
            self.app.t_cas = helpers.close_after_seconds(self.hours)
        except Exception:
            # warn input here
            print('Input restricted to positive integer values')
            pass
