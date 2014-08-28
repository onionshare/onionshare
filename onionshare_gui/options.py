from PyQt4 import QtCore, QtGui

import common
from onionshare import strings, helpers

class Options(QtGui.QHBoxLayout):
    def __init__(self, web):
        super(Options, self).__init__()
        self.addSpacing(10)

        self.web = web
        
        # close automatically
        self.close_automatically = QtGui.QCheckBox()
        if self.web.stay_open:
            self.close_automatically.setCheckState(QtCore.Qt.Unchecked)
        else:
            self.close_automatically.setCheckState(QtCore.Qt.Checked)
        self.close_automatically.setText(strings._("close_on_finish"))
        self.connect(self.close_automatically, QtCore.SIGNAL('stateChanged(int)'), self.stay_open_changed)

        # add the widgets
        self.addWidget(self.close_automatically)

    def stay_open_changed(self, state):
        if state > 0:
            self.web.set_stay_open(False)
        else:
            self.web.set_stay_open(True)

