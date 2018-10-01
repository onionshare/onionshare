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

import json
import os
import platform
import locale

from . import strings


class Settings(object):
    """
    This class stores all of the settings for OnionShare, specifically for how
    to connect to Tor. If it can't find the settings file, it uses the default,
    which is to attempt to connect automatically using default Tor Browser
    settings.
    """
    def __init__(self, common, config=False):
        self.common = common

        self.common.log('Settings', '__init__')

        # Default config
        self.filename = self.build_filename()

        # If a readable config file was provided, use that instead
        if config:
            if os.path.isfile(config):
                self.filename = config
            else:
                self.common.log('Settings', '__init__', 'Supplied config does not exist or is unreadable. Falling back to default location')

        # Dictionary of available languages in this version of OnionShare,
        # mapped to the language name, in that language
        self.available_locales = {
            'cs': 'Hrvatski',   # Croatian
            'da': 'Dansk',      # Danish
            'de': 'Deutsch',    # German
            'en': 'English',    # English
            'eo': 'Esperanto',  # Esperanto
            'es': 'Español',    # Spanish
            'fi': 'Suomi',      # Finnish
            'fr': 'Français',   # French
            'it': 'Italiano',   # Italian
            'nl': 'Nederlands', # Dutch
            'no': 'Norsk',      # Norweigan
            'pt': 'Português',  # Portuguese
            'ru': 'Русский',    # Russian
            'tr': 'Türkçe'      # Turkish
        }

        # These are the default settings. They will get overwritten when loading from disk
        self.default_settings = {
            'version': self.common.version,
            'connection_type': 'bundled',
            'control_port_address': '127.0.0.1',
            'control_port_port': 9051,
            'socks_address': '127.0.0.1',
            'socks_port': 9050,
            'socket_file_path': '/var/run/tor/control',
            'auth_type': 'no_auth',
            'auth_password': '',
            'close_after_first_download': True,
            'shutdown_timeout': False,
            'use_stealth': False,
            'use_autoupdate': True,
            'autoupdate_timestamp': None,
            'no_bridges': True,
            'tor_bridges_use_obfs4': False,
            'tor_bridges_use_meek_lite_azure': False,
            'tor_bridges_use_custom_bridges': '',
            'use_legacy_v2_onions': False,
            'save_private_key': False,
            'private_key': '',
            'public_mode': False,
            'slug': '',
            'hidservauth_string': '',
            'downloads_dir': self.build_default_downloads_dir(),
            'receive_allow_receiver_shutdown': True,
            'locale': None # this gets defined in fill_in_defaults()
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

        # Choose the default locale based on the OS preference, and fall-back to English
        if self._settings['locale'] is None:
            default_locale = locale.getdefaultlocale()[0][:2]
            if default_locale not in self.available_locales:
                default_locale = 'en'
            self._settings['locale'] = default_locale

    def build_filename(self):
        """
        Returns the path of the settings file.
        """
        p = platform.system()
        if p == 'Windows':
            try:
                appdata = os.environ['APPDATA']
                return '{}\\OnionShare\\onionshare.json'.format(appdata)
            except:
                # If for some reason we don't have the 'APPDATA' environment variable
                # (like running tests in Linux while pretending to be in Windows)
                return os.path.expanduser('~/.config/onionshare/onionshare.json')
        elif p == 'Darwin':
            return os.path.expanduser('~/Library/Application Support/OnionShare/onionshare.json')
        else:
            return os.path.expanduser('~/.config/onionshare/onionshare.json')

    def build_default_downloads_dir(self):
        """
        Returns the path of the default Downloads directory for receive mode.
        """
        # TODO: Test in Windows, though it looks like it should work
        # https://docs.python.org/3/library/os.path.html#os.path.expanduser
        return os.path.expanduser('~/OnionShare')

    def load(self):
        """
        Load the settings from file.
        """
        self.common.log('Settings', 'load')

        # If the settings file exists, load it
        if os.path.exists(self.filename):
            try:
                self.common.log('Settings', 'load', 'Trying to load {}'.format(self.filename))
                with open(self.filename, 'r') as f:
                    self._settings = json.load(f)
                    self.fill_in_defaults()
            except:
                pass

    def save(self):
        """
        Save settings to file.
        """
        self.common.log('Settings', 'save')

        try:
            os.makedirs(os.path.dirname(self.filename))
        except:
            pass
        open(self.filename, 'w').write(json.dumps(self._settings))
        self.common.log('Settings', 'save', 'Settings saved in {}'.format(self.filename))

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
