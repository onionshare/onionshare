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
from onionshare import helpers
from nose import with_setup

import test_helpers

def test_get_platform_returns_platform_system():
    """get_platform() returns platform.system() when ONIONSHARE_PLATFORM is not defined"""
    helpers.platform.system = lambda: 'Sega Saturn'
    assert helpers.get_platform() == 'Sega Saturn'
