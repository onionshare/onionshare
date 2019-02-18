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

try:
    # We only need pwd module in macOS, and it's not available in Windows
    import pwd
except:
    pass

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
            'bn': 'বাংলা',       # Bengali
            'ca': 'Català',     # Catalan
            'da': 'Dansk',      # Danish
            'en': 'English',    # English
            'fr': 'Français',   # French
            'el': 'Ελληνικά',   # Greek
            'it': 'Italiano',   # Italian
            'ja': '日本語',      # Japanese
            'fa': 'فارسی',      # Persian
            'pt_BR': 'Português (Brasil)',  # Portuguese Brazil
            'ru': 'Русский',    # Russian
            'es': 'Español',    # Spanish
            'sv': 'Svenska'     # Swedish
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
            'data_dir': self.build_default_data_dir(),
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
            language_code, encoding = locale.getdefaultlocale()

            # Default to English
            if not language_code:
                language_code = 'en_US'

            if language_code == 'pt_PT' and language_code == 'pt_BR':
                # Portuguese locales include country code
                default_locale = language_code
            else:
                # All other locales cut off the country code
                default_locale = language_code[:2]

            if default_locale not in self.available_locales:
                default_locale = 'en'
            self._settings['locale'] = default_locale

    def build_filename(self):
        """
        Returns the path of the settings file.
        """
        return os.path.join(self.common.build_data_dir(), 'onionshare.json')

    def build_default_data_dir(self):
        """
        Returns the path of the default Downloads directory for receive mode.
        """

        if self.common.platform == "Darwin":
            # We can't use os.path.expanduser() in macOS because in the sandbox it
            # returns the path to the sandboxed homedir
            real_homedir = pwd.getpwuid(os.getuid()).pw_dir
            return os.path.join(real_homedir, 'OnionShare')
        elif self.common.platform == "Windows":
            # On Windows, os.path.expanduser() needs to use backslash, or else it
            # retains the forward slash, which breaks opening the folder in explorer.
            return os.path.expanduser('~\OnionShare')
        else:
            # All other OSes
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

        # Make sure data_dir exists
        try:
            os.makedirs(self.get('data_dir'), exist_ok=True)
        except:
            pass

    def save(self):
        """
        Save settings to file.
        """
        self.common.log('Settings', 'save')
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
