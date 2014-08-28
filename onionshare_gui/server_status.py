from PyQt4 import QtCore, QtGui

import common
from onionshare import strings, helpers

class ServerStatus(QtGui.QVBoxLayout):
    server_started = QtCore.pyqtSignal()
    server_stopped = QtCore.pyqtSignal()

    STATUS_STOPPED = 0
    STATUS_WORKING = 1
    STATUS_STARTED = 2

    def __init__(self, file_selection):
        super(ServerStatus, self).__init__()
        self.status = self.STATUS_STOPPED
        self.addSpacing(10)

        self.file_selection = file_selection

        # server layout
        self.status_image_stopped = QtGui.QImage('{0}/server_stopped.png'.format(common.onionshare_gui_dir))
        self.status_image_working = QtGui.QImage('{0}/server_working.png'.format(common.onionshare_gui_dir))
        self.status_image_started = QtGui.QImage('{0}/server_started.png'.format(common.onionshare_gui_dir))
        self.status_image_label = QtGui.QLabel()
        self.status_image_label.setFixedWidth(30)
        self.start_server_button = QtGui.QPushButton(strings._('gui_start_server'))
        self.start_server_button.clicked.connect(self.start_server)
        self.stop_server_button = QtGui.QPushButton(strings._('gui_stop_server'))
        self.stop_server_button.clicked.connect(self.stop_server)
        server_layout = QtGui.QHBoxLayout()
        server_layout.addWidget(self.status_image_label)
        server_layout.addWidget(self.start_server_button)
        server_layout.addWidget(self.stop_server_button)

        # url layout
        url_font = QtGui.QFont()
        url_font.setPointSize(8)
        self.url_label = QtGui.QLabel()
        self.url_label.setFont(url_font)
        self.url_label.setWordWrap(True)
        self.url_label.setAlignment(QtCore.Qt.AlignCenter)
        self.url_label.setMargin(3)
        self.copy_url_button = QtGui.QPushButton(strings._('gui_copy_url'))
        self.copy_url_button.clicked.connect(self.copy_url)
        url_layout = QtGui.QHBoxLayout()
        url_layout.addWidget(self.url_label)
        url_layout.addWidget(self.copy_url_button)
        # url fields start hidden, until there's a URL
        self.url_label.hide()
        self.copy_url_button.hide()

        # add the widgets
        self.addLayout(server_layout)
        self.addLayout(url_layout)

        self.update()

    def update(self):
        # set the status image
        if self.status == self.STATUS_STOPPED:
            self.status_image_label.setPixmap(QtGui.QPixmap.fromImage(self.status_image_stopped))
        elif self.status == self.STATUS_WORKING:
            self.status_image_label.setPixmap(QtGui.QPixmap.fromImage(self.status_image_working))
        elif self.status == self.STATUS_STARTED:
            self.status_image_label.setPixmap(QtGui.QPixmap.fromImage(self.status_image_started))

        # buttons enabled
        if self.file_selection.get_num_files() == 0:
            self.start_server_button.setEnabled(False)
            self.stop_server_button.setEnabled(False)
        else:
            if self.status == self.STATUS_STOPPED:
                self.start_server_button.setEnabled(True)
                self.stop_server_button.setEnabled(False)
            else:
                self.start_server_button.setEnabled(False)
                self.stop_server_button.setEnabled(True)

    def start_server(self):
        self.status = self.STATUS_WORKING
        self.update()
        self.server_started.emit()

    def stop_server(self):
        self.status = self.STATUS_STOPPED
        self.update()
        self.server_stopped.emit()

    def copy_url(self):
        pass

