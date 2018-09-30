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
from PyQt5 import QtCore


class CompressThread(QtCore.QThread):
    """
    Compresses files to be shared
    """
    success = QtCore.pyqtSignal()
    error = QtCore.pyqtSignal(str)

    def __init__(self, mode):
        super(CompressThread, self).__init__()
        self.mode = mode
        self.mode.common.log('CompressThread', '__init__')

    # prepare files to share
    def set_processed_size(self, x):
        if self.mode._zip_progress_bar != None:
            self.mode._zip_progress_bar.update_processed_size_signal.emit(x)

    def run(self):
        self.mode.common.log('CompressThread', 'run')

        try:
            if self.mode.web.share_mode.set_file_info(self.mode.filenames, processed_size_callback=self.set_processed_size):
                self.success.emit()
            else:
                # Cancelled
                pass

            self.mode.app.cleanup_filenames += self.mode.web.share_mode.cleanup_filenames
        except OSError as e:
            self.error.emit(e.strerror)

    def cancel(self):
        self.mode.common.log('CompressThread', 'cancel')

        # Let the Web and ZipWriter objects know that we're canceling compression early
        self.mode.web.cancel_compression = True
        try:
            self.mode.web.zip_writer.cancel_compression = True
        except AttributeError:
            # we never made it as far as creating a ZipWriter object
            pass
