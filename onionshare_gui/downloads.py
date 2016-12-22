# -*- coding: utf-8 -*-
"""
OnionShare | https://onionshare.org/

Copyright (C) 2016 Micah Lee <micah@micahflee.com>

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

from onionshare import strings, helpers

class Download(object):

    def __init__(self, download_id, total_bytes):
        self.download_id = download_id
        self.started = time.time()
        self.total_bytes = total_bytes
        self.downloaded_bytes = 0

        # make a new progress bar
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setAlignment(QtCore.Qt.AlignHCenter)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(total_bytes)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet(
            "QProgressBar::chunk { background-color: #05B8CC; }")
        self.progress_bar.total_bytes = total_bytes

        # start at 0
        self.update(0)

    def update(self, downloaded_bytes):
        self.downloaded_bytes = downloaded_bytes

        self.progress_bar.setValue(downloaded_bytes)
        if downloaded_bytes == self.progress_bar.total_bytes:
            pb_fmt = strings._('gui_download_progress_complete').format(
                helpers.format_seconds(time.time() - self.started))
        else:
            elapsed = time.time() - self.started
            if elapsed < 10:
                # Wait a couple of seconds for the download rate to stabilize.
                # This prevents a "Windows copy dialog"-esque experience at
                # the beginning of the download.
                pb_fmt = strings._('gui_download_progress_starting').format(
                    helpers.human_readable_filesize(downloaded_bytes))
            else:
                pb_fmt = strings._('gui_download_progress_eta').format(
                    helpers.human_readable_filesize(downloaded_bytes),
                    self.estimated_time_remaining)

        self.progress_bar.setFormat(pb_fmt)

    def cancel(self):
        self.progress_bar.setFormat(strings._('gui_canceled'))

    @property
    def estimated_time_remaining(self):
        return helpers.estimated_time_remaining(self.downloaded_bytes,
                                                self.total_bytes,
                                                self.started)


class Downloads(QtWidgets.QVBoxLayout):
    """
    The downloads chunk of the GUI. This lists all of the active download
    progress bars.
    """
    def __init__(self):
        super(Downloads, self).__init__()

        self.downloads = {}

        # downloads label
        self.downloads_label = QtWidgets.QLabel(strings._('gui_downloads', True))
        self.downloads_label.hide()

        # add the widgets
        self.addWidget(self.downloads_label)

    def add_download(self, download_id, total_bytes):
        """
        Add a new download progress bar.
        """
        self.downloads_label.show()

        # add it to the list
        download = Download(download_id, total_bytes)
        self.downloads[download_id] = download
        self.insertWidget(-1, download.progress_bar)

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
