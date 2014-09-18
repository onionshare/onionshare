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
from PyQt4 import QtCore, QtGui

import common
from onionshare import strings, helpers

class Options(QtGui.QHBoxLayout):
    def __init__(self, web):
        super(Options, self).__init__()

        self.web = web
        
        # close automatically
        self.close_automatically = QtGui.QCheckBox()
        if self.web.stay_open:
            self.close_automatically.setCheckState(QtCore.Qt.Unchecked)
        else:
            self.close_automatically.setCheckState(QtCore.Qt.Checked)
        self.close_automatically.setText(strings._("close_on_finish", True))
        self.connect(self.close_automatically, QtCore.SIGNAL('stateChanged(int)'), self.stay_open_changed)

        # add the widgets
        self.addWidget(self.close_automatically)

    def stay_open_changed(self, state):
        if state > 0:
            self.web.set_stay_open(False)
        else:
            self.web.set_stay_open(True)

