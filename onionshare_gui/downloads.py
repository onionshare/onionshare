from PyQt4 import QtCore, QtGui

import common
from onionshare import strings, helpers

class Downloads(QtGui.QVBoxLayout):
    def __init__(self):
        super(Downloads, self).__init__()
        self.addSpacing(10)

        # downloads label
        self.downloads_label = QtGui.QLabel(strings._('gui_downloads'))
        """progress_bar = QtGui.QProgressBar()
        progress_bar.setFormat("12.3 KiB, 17%")
        progress_bar.setTextVisible(True)
        progress_bar.setAlignment(QtCore.Qt.AlignHCenter)
        progress_bar.setMinimum(0)
        progress_bar.setMaximum(100)
        progress_bar.setValue(17)"""
        # hide downloads by default
        self.downloads_label.hide()

        # add the widgets
        self.addWidget(self.downloads_label)
        #self.addWidget(progress_bar)

