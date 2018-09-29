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
import time
from PyQt5 import QtCore, QtWidgets, QtGui

from onionshare import strings


class Download(QtWidgets.QWidget):
    def __init__(self, common, download_id, total_bytes):
        super(Download, self).__init__()
        self.common = common

        self.download_id = download_id
        self.started = time.time()
        self.total_bytes = total_bytes
        self.downloaded_bytes = 0

        self.setStyleSheet('QWidget { border: 1px solid red; }')

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

        # Layout
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.progress_bar)
        self.setLayout(layout)

        # Start at 0
        self.update(0)

    def update(self, downloaded_bytes):
        self.downloaded_bytes = downloaded_bytes

        self.progress_bar.setValue(downloaded_bytes)
        if downloaded_bytes == self.progress_bar.total_bytes:
            pb_fmt = strings._('gui_download_upload_progress_complete').format(
                self.common.format_seconds(time.time() - self.started))
        else:
            elapsed = time.time() - self.started
            if elapsed < 10:
                # Wait a couple of seconds for the download rate to stabilize.
                # This prevents a "Windows copy dialog"-esque experience at
                # the beginning of the download.
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
        return self.common.estimated_time_remaining(self.downloaded_bytes,
                                                self.total_bytes,
                                                self.started)


class DownloadList(QtWidgets.QScrollArea):
    """
    List of download progress bars.
    """
    def __init__(self, common):
        super(DownloadList, self).__init__()
        self.common = common

        self.downloads = {}

        self.downloads_layout = QtWidgets.QVBoxLayout()
        self.downloads_layout.setSizeConstraint(QtWidgets.QLayout.SetMinAndMaxSize)
        widget = QtWidgets.QWidget()
        widget.setLayout(self.downloads_layout)
        self.setWidget(widget)

        self.setBackgroundRole(QtGui.QPalette.Light)
        self.verticalScrollBar().rangeChanged.connect(self.resizeScroll)

    def resizeScroll(self, minimum, maximum):
        """
        Scroll to the bottom of the window when the range changes.
        """
        self.verticalScrollBar().setValue(maximum)

    def add(self, download_id, content_length):
        """
        Add a new download progress bar.
        """
        download = Download(self.common, download_id, content_length)
        self.downloads[download_id] = download
        self.downloads_layout.addWidget(download)

    def update(self, download_id, downloaded_bytes):
        """
        Update the progress of a download progress bar.
        """
        self.downloads[download_id].update(downloaded_bytes)

    def cancel(self, download_id):
        """
        Update a download progress bar to show that it has been canceled.
        """
        self.downloads[download_id].cancel()

    def reset(self):
        """
        Reset the downloads back to zero
        """
        for download in self.downloads.values():
            self.downloads_layout.removeWidget(download.progress_bar)
            download.progress_bar.close()
        self.downloads = {}


class Downloads(QtWidgets.QWidget):
    """
    The downloads chunk of the GUI. This lists all of the active download
    progress bars.
    """
    def __init__(self, common):
        super(Downloads, self).__init__()
        self.common = common

        self.setMinimumWidth(350)

        # When there are no downloads
        empty_image = QtWidgets.QLabel()
        empty_image.setAlignment(QtCore.Qt.AlignCenter)
        empty_image.setPixmap(QtGui.QPixmap.fromImage(QtGui.QImage(self.common.get_resource_path('images/downloads_transparent.png'))))
        empty_text = QtWidgets.QLabel(strings._('gui_no_downloads', True))
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

        # When there are downloads
        self.download_list = DownloadList(self.common)

        # Download header
        downloads_label = QtWidgets.QLabel(strings._('gui_downloads', True))
        downloads_label.setStyleSheet(self.common.css['downloads_uploads_label'])
        clear_button = QtWidgets.QPushButton(strings._('gui_clear_history', True))
        clear_button.setStyleSheet(self.common.css['downloads_uploads_clear'])
        clear_button.setFlat(True)
        clear_button.clicked.connect(self.reset)
        download_header = QtWidgets.QHBoxLayout()
        download_header.addWidget(downloads_label)
        download_header.addStretch()
        download_header.addWidget(clear_button)

        # Download layout
        not_empty_layout = QtWidgets.QVBoxLayout()
        not_empty_layout.addLayout(download_header)
        not_empty_layout.addWidget(self.download_list)
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

    def add(self, download_id, content_length):
        """
        Add a new download progress bar.
        """
        self.common.log('Downloads', 'add', 'download_id: {}, content_length: {}'.format(download_id, content_length))

        # Hide empty, show not empty
        self.empty.hide()
        self.not_empty.show()

        # Add it to the list
        self.download_list.add(download_id, content_length)

    def update(self, download_id, downloaded_bytes):
        """
        Update the progress of a download progress bar.
        """
        self.download_list.update(download_id, downloaded_bytes)

    def cancel(self, download_id):
        """
        Update a download progress bar to show that it has been canceled.
        """
        self.download_list.cancel(download_id)

    def reset(self):
        """
        Reset the downloads back to zero
        """
        self.download_list.reset()

        # Hide not empty, show empty
        self.not_empty.hide()
        self.empty.show()
