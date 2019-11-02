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


class ModeSettings:
    """
    This stores the settings for a single instance of an OnionShare mode. In CLI there
    is only one TabSettings, and in the GUI there is a separate TabSettings for each tab
    """

    def __init__(self, common):
        self.common = common

        self.settings = {
            "persistent": {
                "enabled": False,
                "private_key": None,
                "hidservauth": None,
                "password": None,
            },
            "general": {
                "public": False,
                "autostart_timer": False,
                "autostop_timer": False,
                "legacy": False,
                "client_auth": False,
            },
            "share": {"autostop_sharing": True},
            "receive": {"data_dir": self.common.settings.build_default_data_dir()},
            "website": {"disable_csp": False},
        }

    def get(self, group, key):
        return self.settings[group][key]

    def set(self, group, key, val):
        self.settings[group][key] = val
