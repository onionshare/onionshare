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

import platform, os, json

from . import strings, helpers

class Settings(object):
    """
    This class stores all of the settings for OnionShare, specifically for how
    to connect to Tor. If it can't find the settings file, it uses the default,
    which is to attempt to connect automatically using default Tor Browser
    settings.
    """
    def __init__(self):
        self.filename = self.build_filename()

        # These are the default settings. They will get overwritten when loading from disk
        self._settings = {
            'version': helpers.get_version(),
            'connection_type': 'automatic',
            'control_port_address': '127.0.0.1',
            'control_port_port': 9051,
            'socket_file_path': '/var/run/tor/control',
            'auth_type': 'no_auth',
            'auth_password': ''
        }

    def build_filename(self):
        """
        Returns the path of the settings file.
        """
        p = platform.system()
        if p == 'Windows':
            appdata = os.environ['APPDATA']
            return '{}\\OnionShare\\onionshare.json'.format(appdata)
        elif p == 'Darwin':
            return os.path.expanduser('~/Library/Application Support/OnionShare/onionshare.json')
        else:
            return os.path.expanduser('~/.config/onionshare/onionshare.json')

    def load(self):
        """
        Load the settings from file.
        """
        # If the settings file exists, load it
        if os.path.exists(self.filename):
            try:
                self._settings = json.loads(open(self.filename, 'r').read())
            except:
                pass

    def save(self):
        """
        Save settings to file.
        """
        try:
            os.makedirs(os.path.dirname(self.filename))
        except:
            pass
        open(self.filename, 'w').write(json.dumps(self._settings))
        print(strings._('settings_saved').format(self.filename))

    def get(self, key):
        return self._settings[key]

    def set(self, key, val):
        self._settings[key] = val
