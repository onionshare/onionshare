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
import os
import subprocess
import textwrap
from datetime import datetime
from PyQt5 import QtCore, QtWidgets, QtGui

from onionshare import strings
from ...widgets import Alert


class File(QtWidgets.QWidget):
    def __init__(self, common, filename):
        super(File, self).__init__()
        self.common = common

        self.common.log('File', '__init__', 'filename: {}'.format(filename))

        self.filename = filename
        self.started = datetime.now()

        # Filename label
        self.filename_label = QtWidgets.QLabel(self.filename)
        self.filename_label_width = self.filename_label.width()

        # File size label
        self.filesize_label = QtWidgets.QLabel()
        self.filesize_label.setStyleSheet(self.common.css['receive_file_size'])
        self.filesize_label.hide()

        # Folder button
        folder_pixmap = QtGui.QPixmap.fromImage(QtGui.QImage(self.common.get_resource_path('images/open_folder.png')))
        folder_icon = QtGui.QIcon(folder_pixmap)
        self.folder_button = QtWidgets.QPushButton()
        self.folder_button.clicked.connect(self.open_folder)
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

    def rename(self, new_filename):
        self.filename = new_filename
        self.filename_label.setText(self.filename)

    def open_folder(self):
        """
        Open the downloads folder, with the file selected, in a cross-platform manner
        """
        self.common.log('File', 'open_folder')

        abs_filename = os.path.join(self.common.settings.get('downloads_dir'), self.filename)

        # Linux
        if self.common.platform == 'Linux' or self.common.platform == 'BSD':
            try:
                # If nautilus is available, open it
                subprocess.Popen(['nautilus', abs_filename])
            except:
                Alert(self.common, strings._('gui_open_folder_error_nautilus').format(abs_filename))

        # macOS
        elif self.common.platform == 'Darwin':
            # TODO: Implement opening folder with file selected in macOS
            # This seems helpful: https://stackoverflow.com/questions/3520493/python-show-in-finder
            self.common.log('File', 'open_folder', 'not implemented for Darwin yet')

        # Windows
        elif self.common.platform == 'Windows':
            # TODO: Implement opening folder with file selected in Windows
            # This seems helpful: https://stackoverflow.com/questions/6631299/python-opening-a-folder-in-explorer-nautilus-mac-thingie
            self.common.log('File', 'open_folder', 'not implemented for Windows yet')


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

    def rename(self, old_filename, new_filename):
        self.files[old_filename].rename(new_filename)
        self.files[new_filename] = self.files.pop(old_filename)

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


class UploadList(QtWidgets.QScrollArea):
    """
    List of upload progess bars.
    """
    def __init__(self, common):
        super(UploadList, self).__init__()
        self.common = common

        self.uploads = {}

        # The layout that holds all of the uploads
        self.uploads_layout = QtWidgets.QVBoxLayout()
        self.uploads_layout.setContentsMargins(0, 0, 0, 0)
        self.uploads_layout.setSizeConstraint(QtWidgets.QLayout.SetMinAndMaxSize)

        # Wrapper layout that also contains a stretch
        wrapper_layout = QtWidgets.QVBoxLayout()
        wrapper_layout.setSizeConstraint(QtWidgets.QLayout.SetMinAndMaxSize)
        wrapper_layout.addLayout(self.uploads_layout)
        wrapper_layout.addStretch()

        # The internal widget of the scroll area
        widget = QtWidgets.QWidget()
        widget.setLayout(wrapper_layout)
        self.setWidget(widget)
        self.setWidgetResizable(True)

        # Other scroll area settings
        self.setBackgroundRole(QtGui.QPalette.Light)
        self.verticalScrollBar().rangeChanged.connect(self.resizeScroll)

    def resizeScroll(self, minimum, maximum):
        """
        Scroll to the bottom of the window when the range changes.
        """
        self.verticalScrollBar().setValue(maximum)

    def add(self, upload_id, content_length):
        """
        Add a new upload progress bar.
        """
        upload = Upload(self.common, upload_id, content_length)
        self.uploads[upload_id] = upload
        self.uploads_layout.addWidget(upload)

    def update(self, upload_id, progress):
        """
        Update the progress of an upload.
        """
        self.uploads[upload_id].update(progress)

    def rename(self, upload_id, old_filename, new_filename):
        """
        Rename a file, which happens if the filename already exists in downloads_dir.
        """
        self.uploads[upload_id].rename(old_filename, new_filename)

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
        for upload in self.uploads.values():
            self.uploads_layout.removeWidget(upload)
            upload.progress_bar.close()
        self.uploads = {}


class Uploads(QtWidgets.QWidget):
    """
    The uploads chunk of the GUI. This lists all of the active upload
    progress bars, as well as information about each upload.
    """
    def __init__(self, common):
        super(Uploads, self).__init__()
        self.common = common
        self.common.log('Uploads', '__init__')

        self.setMinimumWidth(350)

        # When there are no uploads
        empty_image = QtWidgets.QLabel()
        empty_image.setAlignment(QtCore.Qt.AlignCenter)
        empty_image.setPixmap(QtGui.QPixmap.fromImage(QtGui.QImage(self.common.get_resource_path('images/uploads_transparent.png'))))
        empty_text = QtWidgets.QLabel(strings._('gui_no_uploads', True))
        empty_text.setAlignment(QtCore.Qt.AlignCenter)
        empty_text.setStyleSheet(self.common.css['downloads_uploads_empty_text'])
        empty_layout = QtWidgets.QVBoxLayout()
        empty_layout.addStretch()
        empty_layout.addWidget(empty_image)
        empty_layout.addWidget(empty_text)
        empty_layout.addStretch()
        self.empty = QtWidgets.QWidget()
        self.empty.setStyleSheet(self.common.css['downloads_uploads_empty'])
        self.empty.setLayout(empty_layout)

        # When there are uploads
        self.upload_list = UploadList(self.common)

        # Upload header
        uploads_label = QtWidgets.QLabel(strings._('gui_uploads', True))
        uploads_label.setStyleSheet(self.common.css['downloads_uploads_label'])
        clear_button = QtWidgets.QPushButton(strings._('gui_clear_history', True))
        clear_button.setStyleSheet(self.common.css['downloads_uploads_clear'])
        clear_button.setFlat(True)
        clear_button.clicked.connect(self.reset)
        upload_header = QtWidgets.QHBoxLayout()
        upload_header.addWidget(uploads_label)
        upload_header.addStretch()
        upload_header.addWidget(clear_button)

        # Upload layout
        not_empty_layout = QtWidgets.QVBoxLayout()
        not_empty_layout.addLayout(upload_header)
        not_empty_layout.addWidget(self.upload_list)
        self.not_empty = QtWidgets.QWidget()
        self.not_empty.setLayout(not_empty_layout)

        # Layout
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.empty)
        layout.addWidget(self.not_empty)
        self.setLayout(layout)

        # Reset once at the beginning
        self.reset()

    def add(self, upload_id, content_length):
        """
        Add a new upload.
        """
        self.common.log('Uploads', 'add', 'upload_id: {}, content_length: {}'.format(upload_id, content_length))

        # Hide empty, show not empty
        self.empty.hide()
        self.not_empty.show()

        # Add it to the list
        self.upload_list.add(upload_id, content_length)

    def update(self, upload_id, progress):
        """
        Update the progress of an upload.
        """
        self.upload_list.update(upload_id, progress)

    def rename(self, upload_id, old_filename, new_filename):
        """
        Rename a file, which happens if the filename already exists in downloads_dir.
        """
        self.upload_list.rename(upload_id, old_filename, new_filename)

    def finished(self, upload_id):
        """
        An upload has finished.
        """
        self.upload_list.finished(upload_id)

    def cancel(self, upload_id):
        """
        Update an upload progress bar to show that it has been canceled.
        """
        self.common.log('Uploads', 'cancel', 'upload_id: {}'.format(upload_id))
        self.upload_list.cancel(upload_id)

    def reset(self):
        """
        Reset the uploads back to zero
        """
        self.upload_list.reset()

        # Hide not empty, show empty
        self.not_empty.hide()
        self.empty.show()
