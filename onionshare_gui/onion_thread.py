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

class OnionThread(QtCore.QThread):
    """
    A QThread for starting our Onion Service.
    By using QThread rather than threading.Thread, we are able
    to call quit() or terminate() on the startup if the user
    decided to cancel (in which case do not proceed with obtaining
    the Onion address and starting the web server).
    """
    def __init__(self, common, function, kwargs=None):
        super(OnionThread, self).__init__()

        self.common = common

        self.common.log('OnionThread', '__init__')
        self.function = function
        if not kwargs:
            self.kwargs = {}
        else:
            self.kwargs = kwargs

    def run(self):
        self.common.log('OnionThread', 'run')

        self.function(**self.kwargs)
