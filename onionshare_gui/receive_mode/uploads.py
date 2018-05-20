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
        self.filename_label = QtWidgets.QLabel(self.filename)

        # File size label
        self.filesize_label = QtWidgets.QLabel()
        self.filesize_label.setStyleSheet(self.common.css['receive_file_size'])
        self.filesize_label.hide()

        # Folder button
        folder_pixmap = QtGui.QPixmap.fromImage(QtGui.QImage(self.common.get_resource_path('images/open_folder.png')))
        folder_icon = QtGui.QIcon(folder_pixmap)
        self.folder_button = QtWidgets.QPushButton()
        self.folder_button.setIcon(folder_icon)
        self.folder_button.setIconSize(folder_pixmap.rect().size())
        self.folder_button.setFlat(True)
        self.folder_button.hide()

        # Layouts
        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.filename_label)
        layout.addWidget(self.filesize_label)
        layout.addStretch()
        layout.addWidget(self.folder_button)
        self.setLayout(layout)

    def update(self, uploaded_bytes, complete):
        self.filesize_label.setText(self.common.human_readable_filesize(uploaded_bytes))
        self.filesize_label.show()

        if complete:
            self.folder_button.show()


class Upload(QtWidgets.QWidget):
    def __init__(self, common, upload_id, content_length):
        super(Upload, self).__init__()
        self.common = common
        self.upload_id = upload_id
        self.content_length = content_length
        self.started = datetime.now()

        # Label
        self.label = QtWidgets.QLabel(strings._('gui_upload_in_progress', True).format(self.started.strftime("%b %d, %I:%M%p")))

        # Progress bar
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.progress_bar.setAlignment(QtCore.Qt.AlignHCenter)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet(self.common.css['downloads_uploads_progress_bar'])

        # This layout contains file widgets
        self.files_layout = QtWidgets.QVBoxLayout()
        self.files_layout.setContentsMargins(0, 0, 0, 0)
        files_widget = QtWidgets.QWidget()
        files_widget.setStyleSheet(self.common.css['receive_file'])
        files_widget.setLayout(self.files_layout)

        # Layout
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(files_widget)
        layout.addStretch()
        self.setLayout(layout)

        # We're also making a dictionary of file widgets, to make them easier to access
        self.files = {}

    def update(self, progress):
        """
        Using the progress from Web, update the progress bar and file size labels
        for each file
        """
        total_uploaded_bytes = 0
        for filename in progress:
            total_uploaded_bytes += progress[filename]['uploaded_bytes']

        # Update the progress bar
        self.progress_bar.setMaximum(self.content_length)
        self.progress_bar.setValue(total_uploaded_bytes)

        elapsed = datetime.now() - self.started
        if elapsed.seconds < 10:
            pb_fmt = strings._('gui_download_upload_progress_starting').format(
                self.common.human_readable_filesize(total_uploaded_bytes))
        else:
            estimated_time_remaining = self.common.estimated_time_remaining(
                total_uploaded_bytes,
                self.content_length,
                self.started.timestamp())
            pb_fmt = strings._('gui_download_upload_progress_eta').format(
                self.common.human_readable_filesize(total_uploaded_bytes),
                estimated_time_remaining)

        # Using list(progress) to avoid "RuntimeError: dictionary changed size during iteration"
        for filename in list(progress):
            # Add a new file if needed
            if filename not in self.files:
                self.files[filename] = File(self.common, filename)
                self.files_layout.addWidget(self.files[filename])

            # Update the file
            self.files[filename].update(progress[filename]['uploaded_bytes'], progress[filename]['complete'])

    def finished(self):
        # Hide the progress bar
        self.progress_bar.hide()

        # Change the label
        self.ended = self.started = datetime.now()
        if self.started.year == self.ended.year and self.started.month == self.ended.month and self.started.day == self.ended.day:
            if self.started.hour == self.ended.hour and self.started.minute == self.ended.minute:
                text = strings._('gui_upload_finished', True).format(
                    self.started.strftime("%b %d, %I:%M%p")
                )
            else:
                text = strings._('gui_upload_finished_range', True).format(
                    self.started.strftime("%b %d, %I:%M%p"),
                    self.ended.strftime("%I:%M%p")
                )
        else:
            text = strings._('gui_upload_finished_range', True).format(
                self.started.strftime("%b %d, %I:%M%p"),
                self.ended.strftime("%b %d, %I:%M%p")
            )
        self.label.setText(text)


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

    def add(self, upload_id, content_length):
        """
        Add a new upload.
        """
        self.common.log('Uploads', 'add', 'upload_id: {}, content_length: {}'.format(upload_id, content_length))
        # Hide the no_uploads_label
        self.no_uploads_label.hide()

        # Add it to the list
        upload = Upload(self.common, upload_id, content_length)
        self.uploads[upload_id] = upload
        self.uploads_layout.addWidget(upload)

        # Scroll to the bottom
        self.vbar.setValue(self.vbar.maximum())

    def update(self, upload_id, progress):
        """
        Update the progress of an upload.
        """
        self.uploads[upload_id].update(progress)
        #self.adjustSize()

    def finished(self, upload_id):
        """
        An upload has finished.
        """
        self.uploads[upload_id].finished()

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
