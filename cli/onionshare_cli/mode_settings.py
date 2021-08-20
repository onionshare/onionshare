# -*- coding: utf-8 -*-
"""
OnionShare | https://onionshare.org/

Copyright (C) 2014-2021 Micah Lee, et al. <micah@micahflee.com>

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
import os
import json
import platform

if platform.system() == "Darwin":
    import pwd


class ModeSettings:
    """
    This stores the settings for a single instance of an OnionShare mode. In CLI there
    is only one ModeSettings, and in the GUI there is a separate ModeSettings for each tab
    """

    def __init__(self, common, filename=None, id=None):
        self.common = common

        self.default_settings = {
            "onion": {
                "private_key": None,
                "hidservauth_string": None,
                "password": None,
            },
            "persistent": {"mode": None, "enabled": False},
            "general": {
                "title": None,
                "public": False,
                "autostart_timer": False,
                "autostop_timer": False,
                "legacy": False,
                "client_auth": False,
                "service_id": None,
            },
            "share": {"autostop_sharing": True, "filenames": []},
            "receive": {
                "data_dir": self.build_default_receive_data_dir(),
                "webhook_url": None,
                "disable_text": False,
                "disable_files": False,
            },
            "website": {"disable_csp": False, "filenames": []},
            "chat": {"room": "default"},
        }
        self._settings = {}

        self.just_created = False
        if id:
            self.id = id
        else:
            self.id = self.common.build_password(3)

        self.load(filename)

    def fill_in_defaults(self):
        """
        If there are any missing settings from self._settings, replace them with
        their default values.
        """
        for key in self.default_settings:
            if key in self._settings:
                for inner_key in self.default_settings[key]:
                    if inner_key not in self._settings[key]:
                        self._settings[key][inner_key] = self.default_settings[key][
                            inner_key
                        ]
            else:
                self._settings[key] = self.default_settings[key]

    def get(self, group, key):
        return self._settings[group][key]

    def set(self, group, key, val):
        self._settings[group][key] = val
        self.common.log(
            "ModeSettings", "set", f"updating {self.id}: {group}.{key} = {val}"
        )
        self.save()

    def build_default_receive_data_dir(self):
        """
        Returns the path of the default Downloads directory for receive mode.
        """

        if self.common.platform == "Darwin":
            # We can't use os.path.expanduser() in macOS because in the sandbox it
            # returns the path to the sandboxed homedir
            real_homedir = pwd.getpwuid(os.getuid()).pw_dir
            return os.path.join(real_homedir, "OnionShare")
        elif self.common.platform == "Windows":
            # On Windows, os.path.expanduser() needs to use backslash, or else it
            # retains the forward slash, which breaks opening the folder in explorer.
            return os.path.expanduser("~\\OnionShare")
        else:
            # All other OSes
            return os.path.expanduser("~/OnionShare")

    def load(self, filename=None):
        # Load persistent settings from disk. If the file doesn't exist, create it
        if filename:
            self.filename = filename
        else:
            self.filename = os.path.join(
                self.common.build_persistent_dir(), f"{self.id}.json"
            )

        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r") as f:
                    self._settings = json.load(f)
                    self.fill_in_defaults()
                    self.common.log("ModeSettings", "load", f"loaded {self.filename}")
                    return
            except Exception:
                pass

        # If loading settings didn't work, create the settings file
        self.common.log("ModeSettings", "load", f"creating {self.filename}")
        self.fill_in_defaults()
        self.just_created = True

    def save(self):
        # Save persistent setting to disk
        if not self.get("persistent", "enabled"):
            return

        if self.filename:
            with open(self.filename, "w") as file:
                file.write(json.dumps(self._settings, indent=2))

    def delete(self):
        # Delete the file from disk
        if os.path.exists(self.filename):
            os.remove(self.filename)
