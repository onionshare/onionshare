# -*- coding: utf-8 -*-
"""
OnionShare | https://onionshare.org/

Copyright (C) 2015 Micah Lee <micah@micahflee.com>

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
from PyQt4 import QtCore, QtGui

import common
from onionshare import strings, helpers


class Downloads(QtGui.QVBoxLayout):
    """
    The downloads chunk of the GUI. This lists all of the active download
    progress bars.
    """
    def __init__(self):
        super(Downloads, self).__init__()

        self.progress_bars = {}

        # downloads label
        self.downloads_label = QtGui.QLabel(strings._('gui_downloads', True))
        self.downloads_label.hide()

        # add the widgets
        self.addWidget(self.downloads_label)

    def add_download(self, download_id, total_bytes):
        """
        Add a new download progress bar.
        """
        self.downloads_label.show()

        # make a new progress bar
        pb = QtGui.QProgressBar()
        pb.setTextVisible(True)
        pb.setAlignment(QtCore.Qt.AlignHCenter)
        pb.setMinimum(0)
        pb.setMaximum(total_bytes)
        pb.setValue(0)
        pb.setStyleSheet("QProgressBar::chunk { background-color: #05B8CC; }")
        pb.total_bytes = total_bytes

        # add it to the list
        self.progress_bars[download_id] = pb
        self.addWidget(pb)

        # start at 0
        self.update_download(download_id, total_bytes, 0)

    def update_download(self, download_id, total_bytes, downloaded_bytes):
        """
        Update the progress of a download progress bar.
        """
        if download_id not in self.progress_bars:
            self.add_download(download_id, total_bytes)

        pb = self.progress_bars[download_id]
        pb.setValue(downloaded_bytes)
        if downloaded_bytes == pb.total_bytes:
            pb.setFormat("%p%")
        else:
            pb.setFormat("{0:s}, %p%".format(helpers.human_readable_filesize(downloaded_bytes)))

    def cancel_download(self, download_id):
        """
        Update a download progress bar to show that it has been canceled.
        """
        pb = self.progress_bars[download_id]
        pb.setFormat(strings._('gui_canceled'))
