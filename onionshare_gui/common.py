# -*- coding: utf-8 -*-
"""
OnionShare | https://onionshare.org/

Copyright (C) 2014 Micah Lee <micah@micahflee.com>

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
import os, inspect, platform

def get_onionshare_gui_dir():
    if platform.system() == 'Darwin':
        onionshare_gui_dir = os.path.dirname(__file__)
    else:
        onionshare_gui_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    return onionshare_gui_dir

onionshare_gui_dir = get_onionshare_gui_dir()
