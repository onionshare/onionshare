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
from PyQt5 import QtCore, QtWidgets, QtGui

from onionshare import strings


class Upload(object):
    def __init__(self, common, upload_id, total_bytes):
        self.common = common

        self.upload_id = upload_id
        self.started = time.time()
        self.total_bytes = total_bytes
        self.uploaded_bytes = 0

        # Uploads have two modes, in progress and finished. In progess, they display
        # the progress bar. When finished, they display info about the files that
        # were uploaded.

        # Progress bar
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.progress_bar.setAlignment(QtCore.Qt.AlignHCenter)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(total_bytes)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet(self.common.css['downloads_uploads_progress_bar'])
        self.progress_bar.total_bytes = total_bytes

        # Finished
        self.finished = QtWidgets.QGroupBox()
        self.finished.hide()

        # Start at 0
        self.update(0)

    def update(self, uploaded_bytes):
        self.uploaded_bytes = uploaded_bytes

        self.progress_bar.setValue(uploaded_bytes)
        if uploaded_bytes == self.progress_bar.uploaded_bytes:
            # Upload is finished, hide the progress bar and show the finished widget
            self.progress_bar.hide()

            # TODO: add file information to the finished widget
            ended = time.time()
            elapsed = ended - self.started
            self.finished.show()

        else:
            elapsed = time.time() - self.started
            if elapsed < 10:
                pb_fmt = strings._('gui_download_upload_progress_starting').format(
                    self.common.human_readable_filesize(downloaded_bytes))
            else:
                pb_fmt = strings._('gui_download_upload_progress_eta').format(
                    self.common.human_readable_filesize(downloaded_bytes),
                    self.estimated_time_remaining)

        self.progress_bar.setFormat(pb_fmt)

    def cancel(self):
        self.progress_bar.setFormat(strings._('gui_canceled'))

    @property
    def estimated_time_remaining(self):
        return self.common.estimated_time_remaining(self.uploaded_bytes,
                                                self.total_bytes,
                                                self.started)


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

    def add(self, upload_id, total_bytes):
        """
        Add a new upload progress bar.
        """
        # Hide the no_uploads_label
        self.no_uploads_label.hide()

        # Add it to the list
        uploads = Upload(self.common, upload_id, total_bytes)
        self.uploads[upload_id] = download
        self.uploads_layout.addWidget(upload.progress_bar)

        # Scroll to the bottom
        self.vbar.setValue(self.vbar.maximum())

    def update(self, upload_id, uploaded_bytes):
        """
        Update the progress of an upload progress bar.
        """
        self.uploads[upload_id].update(uploaded_bytes)

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
            self.uploads_layout.removeWidget(upload.progress_bar)
            upload.progress_bar.close()
        self.uploads = {}

        self.no_uploads_label.show()
        self.resize(self.sizeHint())
