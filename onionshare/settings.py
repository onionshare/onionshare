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

from . import strings, common

class Settings(object):
    """
    This class stores all of the settings for OnionShare, specifically for how
    to connect to Tor. If it can't find the settings file, it uses the default,
    which is to attempt to connect automatically using default Tor Browser
    settings.
    """
    def __init__(self):
        common.log('Settings', '__init__')

        self.filename = self.build_filename()

        # These are the default settings. They will get overwritten when loading from disk
        self.default_settings = {
            'version': common.get_version(),
            'connection_type': 'bundled',
            'control_port_address': '127.0.0.1',
            'control_port_port': 9051,
            'socks_address': '127.0.0.1',
            'socks_port': 9050,
            'socket_file_path': '/var/run/tor/control',
            'auth_type': 'no_auth',
            'auth_password': '',
            'close_after_first_download': True,
            'systray_notifications': True,
            'use_stealth': False,
            'use_autoupdate': True,
            'autoupdate_timestamp': None
        }
        self._settings = {}
        self.fill_in_defaults()

    def fill_in_defaults(self):
        """
        If there are any missing settings from self._settings, replace them with
        their default values.
        """
        for key in self.default_settings:
            if key not in self._settings:
                self._settings[key] = self.default_settings[key]

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
        common.log('Settings', 'load')

        # If the settings file exists, load it
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f:
                    self._settings = json.loads(f.read())
                    self.fill_in_defaults()
            except:
                pass

    def save(self):
        """
        Save settings to file.
        """
        common.log('Settings', 'save')

        try:
            os.makedirs(os.path.dirname(self.filename))
        except:
            pass
        open(self.filename, 'w').write(json.dumps(self._settings))
        print(strings._('settings_saved').format(self.filename))

    def get(self, key):
        return self._settings[key]

    def set(self, key, val):
        # If typecasting int values fails, fallback to default values
        if key == 'control_port_port' or key == 'socks_port':
            try:
                val = int(val)
            except:
                if key == 'control_port_port':
                    val = self.default_settings['control_port_port']
                elif key == 'socks_port':
                    val = self.default_settings['socks_port']

        self._settings[key] = val
