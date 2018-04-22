# -*- coding: utf-8 -*-
"""
OnionShare | https://onionshare.org/

Copyright (C) 2017 Micah Lee <micah@micahflee.com>

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

from onionshare import strings, common

class Download(object):

    def __init__(self, download_id, total_bytes):
        self.download_id = download_id
        self.started = time.time()
        self.total_bytes = total_bytes
        self.downloaded_bytes = 0

        # make a new progress bar
        cssStyleData ="""
        QProgressBar {
            border: 1px solid #4e064f;
            background-color: #ffffff !important;
            text-align: center;
            color: #9b9b9b;
            font-size: 12px;
        }

        QProgressBar::chunk {
            background-color: #4e064f;
            width: 10px;
        }"""
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.progress_bar.setAlignment(QtCore.Qt.AlignHCenter)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(total_bytes)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet(cssStyleData)
        self.progress_bar.total_bytes = total_bytes

        # start at 0
        self.update(0)

    def update(self, downloaded_bytes):
        self.downloaded_bytes = downloaded_bytes

        self.progress_bar.setValue(downloaded_bytes)
        if downloaded_bytes == self.progress_bar.total_bytes:
            pb_fmt = strings._('gui_download_progress_complete').format(
                common.format_seconds(time.time() - self.started))
        else:
            elapsed = time.time() - self.started
            if elapsed < 10:
                # Wait a couple of seconds for the download rate to stabilize.
                # This prevents a "Windows copy dialog"-esque experience at
                # the beginning of the download.
                pb_fmt = strings._('gui_download_progress_starting').format(
                    common.human_readable_filesize(downloaded_bytes))
            else:
                pb_fmt = strings._('gui_download_progress_eta').format(
                    common.human_readable_filesize(downloaded_bytes),
                    self.estimated_time_remaining)

        self.progress_bar.setFormat(pb_fmt)

    def cancel(self):
        self.progress_bar.setFormat(strings._('gui_canceled'))

    @property
    def estimated_time_remaining(self):
        return common.estimated_time_remaining(self.downloaded_bytes,
                                                self.total_bytes,
                                                self.started)


class Downloads(QtWidgets.QWidget):
    """
    The downloads chunk of the GUI. This lists all of the active download
    progress bars.
    """
    def __init__(self):
        super(Downloads, self).__init__()
        self.downloads = {}

        self.downloads_container = QtWidgets.QScrollArea()
        self.downloads_container.setWidget(self)
        self.downloads_container.setWindowTitle(strings._('gui_downloads', True))
        self.downloads_container.setWidgetResizable(True)
        self.downloads_container.setMaximumHeight(600)
        self.downloads_container.setMinimumHeight(150)
        self.downloads_container.setMinimumWidth(350)
        self.downloads_container.setWindowIcon(QtGui.QIcon(common.get_resource_path('images/logo.png')))
        self.downloads_container.setWindowFlags(QtCore.Qt.Sheet | QtCore.Qt.WindowTitleHint | QtCore.Qt.WindowSystemMenuHint | QtCore.Qt.CustomizeWindowHint)
        self.downloads_container.vbar = self.downloads_container.verticalScrollBar()

        self.downloads_label = QtWidgets.QLabel(strings._('gui_downloads', True))
        self.downloads_label.setStyleSheet('QLabel { font-weight: bold; font-size 14px; text-align: center; }')
        self.no_downloads_label = QtWidgets.QLabel(strings._('gui_no_downloads', True))

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.downloads_label)
        self.layout.addWidget(self.no_downloads_label)
        self.setLayout(self.layout)

    def add_download(self, download_id, total_bytes):
        """
        Add a new download progress bar.
        """
        # add it to the list
        download = Download(download_id, total_bytes)
        self.downloads[download_id] = download
        self.layout.addWidget(download.progress_bar)

    def update_download(self, download_id, downloaded_bytes):
        """
        Update the progress of a download progress bar.
        """
        self.downloads[download_id].update(downloaded_bytes)

    def cancel_download(self, download_id):
        """
        Update a download progress bar to show that it has been canceled.
        """
        self.downloads[download_id].cancel()

    def reset_downloads(self):
        """
        Reset the downloads back to zero
        """
        for download in self.downloads.values():
            self.layout.removeWidget(download.progress_bar)
            download.progress_bar.close()
        self.downloads = {}
