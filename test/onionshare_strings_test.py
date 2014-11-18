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
import locale
from onionshare import strings
from nose import with_setup


def test_starts_with_empty_strings():
    """creates an empty strings dict by default"""
    assert strings.strings == {}


def test_load_strings_defaults_to_english():
    """load_strings() loads English by default"""
    locale.getdefaultlocale = lambda: ('en_US', 'UTF-8')
    strings.load_strings()
    assert strings._('wait_for_hs') == "Waiting for HS to be ready:"


def test_load_strings_loads_other_languages():
    """load_strings() loads other languages in different locales"""
    locale.getdefaultlocale = lambda: ('fr_FR', 'UTF-8')
    strings.load_strings("fr")
    assert strings._('wait_for_hs') == "En attente du HS:"

