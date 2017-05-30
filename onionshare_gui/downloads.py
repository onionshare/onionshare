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

from PyQt5 import QtCore, QtWidgets

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
            border: 2px solid grey;
            border-radius: 5px;
            text-align: center;
        }

        QProgressBar::chunk {
            background: qlineargradient(x1: 0.5, y1: 0, x2: 0.5, y2: 1, stop: 0 #b366ff, stop: 1 #d9b3ff);
            width: 10px;
        }"""
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setTextVisible(True)
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
        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)

    def add_download(self, download_id, total_bytes):
        """
        Add a new download progress bar.
        """
        self.parent().show()

        # add it to the list
        download = Download(download_id, total_bytes)
        self.downloads[download_id] = download
        self.layout.insertWidget(-1, download.progress_bar)

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
