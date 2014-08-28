from PyQt4 import QtCore, QtGui

import common
from onionshare import strings, helpers

class Options(QtGui.QHBoxLayout):
    def __init__(self, stay_open=False):
        super(Options, self).__init__()
        self.addSpacing(10)
        
        # close automatically
        self.close_automatically = QtGui.QCheckBox()
        if stay_open:
            self.close_automatically.setCheckState(QtCore.Qt.Unchecked)
        else:
            self.close_automatically.setCheckState(QtCore.Qt.Checked)
        self.close_automatically.setText(strings._("close_on_finish"))

        # add the widgets
        self.addWidget(self.close_automatically)

