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

import os, shutil

from . import common, strings
from .common import ShutdownTimer

class OnionShare(object):
    """
    OnionShare is the main application class. Pass in options and run
    start_onion_service and it will do the magic.
    """
    def __init__(self, common, onion, local_only=False, stay_open=False, shutdown_timeout=0):
        self.common = common

        self.common.log('OnionShare', '__init__')

        # The Onion object
        self.onion = onion

        self.hidserv_dir = None
        self.onion_host = None
        self.port = None
        self.stealth = None

        # files and dirs to delete on shutdown
        self.cleanup_filenames = []

        # do not use tor -- for development
        self.local_only = local_only

        # automatically close when download is finished
        self.stay_open = stay_open

        # optionally shut down after N hours
        self.shutdown_timeout = shutdown_timeout
        # init timing thread
        self.shutdown_timer = None

    def set_stealth(self, stealth):
        self.common.log('OnionShare', 'set_stealth', 'stealth={}'.format(stealth))

        self.stealth = stealth
        self.onion.stealth = stealth
    
    def choose_port(self):
        """
        Choose a random port.
        """
        try:
            self.port = self.common.get_available_port(17600, 17650)
        except:
            raise OSError(strings._('no_available_port'))

    def start_onion_service(self):
        """
        Start the onionshare onion service.
        """
        self.common.log('OnionShare', 'start_onion_service')

        if not self.port:
            self.choose_port()

        if self.local_only:
            self.onion_host = '127.0.0.1:{0:d}'.format(self.port)
            return

        if self.shutdown_timeout > 0:
            self.shutdown_timer = ShutdownTimer(self.common, self.shutdown_timeout)

        self.onion_host = self.onion.start_onion_service(self.port)

        if self.stealth:
            self.auth_string = self.onion.auth_string

    def cleanup(self):
        """
        Shut everything down and clean up temporary files, etc.
        """
        self.common.log('OnionShare', 'cleanup')

        # cleanup files
        for filename in self.cleanup_filenames:
            if os.path.isfile(filename):
                os.remove(filename)
            elif os.path.isdir(filename):
                shutil.rmtree(filename)
        self.cleanup_filenames = []
