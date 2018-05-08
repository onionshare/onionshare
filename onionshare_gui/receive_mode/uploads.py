# -*- coding: utf-8 -*-
"""
OnionShare | https://onionshare.org/

Copyright (C) 2014-2018 Micah Lee <micah@micahflee.com>

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
from datetime import datetime
from PyQt5 import QtCore, QtWidgets, QtGui

from onionshare import strings


class Upload(QtWidgets.QGroupBox):
    def __init__(self, common, upload_id):
        super(Upload, self).__init__()
        self.common = common

        self.upload_id = upload_id
        self.started = datetime.now()
        self.uploaded_bytes = 0

        # Set the title of the title of the group box based on the start time
        self.setTitle(strings._('gui_upload_in_progress', True).format(self.started.strftime("%b %m, %I:%M%p")))

        # Start at 0
        self.update({})

    def update(self, progress):
        """
        Using the progress from Web, make sure all the file progress bars exist,
        and update their progress
        """
        pass


class Uploads(QtWidgets.QScrollArea):
    """
    The uploads chunk of the GUI. This lists all of the active upload
    progress bars, as well as information about each upload.
    """
    def __init__(self, common):
        super(Uploads, self).__init__()
        self.common = common

        self.uploads = {}

        self.setWindowTitle(strings._('gui_uploads', True))
        self.setWidgetResizable(True)
        self.setMaximumHeight(600)
        self.setMinimumHeight(150)
        self.setMinimumWidth(350)
        self.setWindowIcon(QtGui.QIcon(common.get_resource_path('images/logo.png')))
        self.setWindowFlags(QtCore.Qt.Sheet | QtCore.Qt.WindowTitleHint | QtCore.Qt.WindowSystemMenuHint | QtCore.Qt.CustomizeWindowHint)
        self.vbar = self.verticalScrollBar()

        uploads_label = QtWidgets.QLabel(strings._('gui_uploads', True))
        uploads_label.setStyleSheet(self.common.css['downloads_uploads_label'])
        self.no_uploads_label = QtWidgets.QLabel(strings._('gui_no_uploads', True))

        self.uploads_layout = QtWidgets.QVBoxLayout()

        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(uploads_label)
        layout.addWidget(self.no_uploads_label)
        layout.addLayout(self.uploads_layout)
        layout.addStretch()
        widget.setLayout(layout)
        self.setWidget(widget)

    def add(self, upload_id):
        """
        Add a new upload.
        """
        # Hide the no_uploads_label
        self.no_uploads_label.hide()

        # Add it to the list
        upload = Upload(self.common, upload_id)
        self.uploads[upload_id] = upload
        self.uploads_layout.addWidget(upload)

        # Scroll to the bottom
        self.vbar.setValue(self.vbar.maximum())

    def update(self, upload_id, uploaded_bytes):
        """
        Update the progress of an upload progress bar.
        """
        pass
        #self.uploads[upload_id].update(uploaded_bytes)

    def cancel(self, upload_id):
        """
        Update an upload progress bar to show that it has been canceled.
        """
        self.uploads[upload_id].cancel()

    def reset(self):
        """
        Reset the uploads back to zero
        """
        for upload in self.uploads.values():
            self.uploads_layout.removeWidget(upload)
        self.uploads = {}

        self.no_uploads_label.show()
        self.resize(self.sizeHint())
