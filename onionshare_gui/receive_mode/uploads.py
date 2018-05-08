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


class File(QtWidgets.QWidget):
    def __init__(self, common, filename):
        super(File, self).__init__()
        self.common = common
        self.filename = filename

        self.started = datetime.now()

        # Filename label
        self.label = QtWidgets.QLabel(self.filename)

        # Progress bar
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.progress_bar.setAlignment(QtCore.Qt.AlignHCenter)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet(self.common.css['downloads_uploads_progress_bar'])

        # Folder button
        self.folder_button = QtWidgets.QPushButton("open folder")
        self.folder_button.hide()

        # Layouts
        info_layout = QtWidgets.QVBoxLayout()
        info_layout.addWidget(self.label)
        info_layout.addWidget(self.progress_bar)

        # The horizontal layout has info to the left, folder button to the right
        layout = QtWidgets.QHBoxLayout()
        layout.addLayout(info_layout)
        layout.addWidget(self.folder_button)
        self.setLayout(layout)

    def update(self, total_bytes, uploaded_bytes):
        print('total_bytes: {}, uploaded_bytes: {}'.format(total_bytes, uploaded_bytes))
        if total_bytes == uploaded_bytes:
            # Hide the progress bar, show the folder button
            self.progress_bar.hide()
            self.folder_button.show()

        else:
            # Update the progress bar
            self.progress_bar.setMaximum(total_bytes)
            self.progress_bar.setValue(uploaded_bytes)

            elapsed = datetime.now() - self.started
            if elapsed.seconds < 10:
                pb_fmt = strings._('gui_download_upload_progress_starting').format(
                    self.common.human_readable_filesize(uploaded_bytes))
            else:
                estimated_time_remaining = self.common.estimated_time_remaining(
                    uploaded_bytes,
                    total_bytes,
                    started.timestamp())
                pb_fmt = strings._('gui_download_upload_progress_eta').format(
                    self.common.human_readable_filesize(uploaded_bytes),
                    estimated_time_remaining)


class Upload(QtWidgets.QGroupBox):
    def __init__(self, common, upload_id):
        super(Upload, self).__init__()
        self.common = common

        self.upload_id = upload_id
        self.started = datetime.now()
        self.uploaded_bytes = 0

        # Set the title of the title of the group box based on the start time
        self.setTitle(strings._('gui_upload_in_progress', True).format(self.started.strftime("%b %m, %I:%M%p")))

        # The layout contains file widgets
        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)

        # We're also making a dictionary of file widgets, to make them easier to access
        self.files = {}

    def update(self, progress):
        """
        Using the progress from Web, make sure all the file progress bars exist,
        and update their progress
        """
        for filename in progress:
            # Add a new file if needed
            if filename not in self.files:
                self.files[filename] = File(self.common, filename)
                self.layout.addWidget(self.files[filename])

            # Update the file
            self.files[filename].update(progress[filename]['total_bytes'], progress[filename]['uploaded_bytes'])


class Uploads(QtWidgets.QScrollArea):
    """
    The uploads chunk of the GUI. This lists all of the active upload
    progress bars, as well as information about each upload.
    """
    def __init__(self, common):
        super(Uploads, self).__init__()
        self.common = common
        self.common.log('Uploads', '__init__')

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
        self.common.log('Uploads', 'add', 'upload_id: {}'.format(upload_id))
        # Hide the no_uploads_label
        self.no_uploads_label.hide()

        # Add it to the list
        upload = Upload(self.common, upload_id)
        self.uploads[upload_id] = upload
        self.uploads_layout.addWidget(upload)

        # Scroll to the bottom
        self.vbar.setValue(self.vbar.maximum())

    def update(self, upload_id, progress):
        """
        Update the progress of an upload progress bar.
        """
        self.uploads[upload_id].update(progress)
        self.adjustSize()

    def cancel(self, upload_id):
        """
        Update an upload progress bar to show that it has been canceled.
        """
        self.common.log('Uploads', 'cancel', 'upload_id: {}'.format(upload_id))
        self.uploads[upload_id].cancel()

    def reset(self):
        """
        Reset the uploads back to zero
        """
        self.common.log('Uploads', 'reset')
        for upload in self.uploads.values():
            self.uploads_layout.removeWidget(upload)
        self.uploads = {}

        self.no_uploads_label.show()
        self.resize(self.sizeHint())
