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

import types

import pytest

from onionshare import strings
from onionshare.settings import Settings

# # Stub get_resource_path so it finds the correct path while running tests
# def get_resource_path(filename):
#     resources_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'share')
#     path = os.path.join(resources_dir, filename)
#     return path
# common.get_resource_path = get_resource_path

def test_underscore_is_function():
    assert callable(strings._) and isinstance(strings._, types.FunctionType)


class TestLoadStrings:
    def test_load_strings_defaults_to_english(
            self, common_obj, locale_en, sys_onionshare_dev_mode):
        """ load_strings() loads English by default """
        common_obj.settings = Settings(common_obj)
        strings.load_strings(common_obj)
        assert strings._('preparing_files') == "Compressing files."


    def test_load_strings_loads_other_languages(
            self, common_obj, locale_fr, sys_onionshare_dev_mode):
        """ load_strings() loads other languages in different locales """
        common_obj.settings = Settings(common_obj)
        common_obj.settings.set('locale', 'fr')
        strings.load_strings(common_obj)
        assert strings._('preparing_files') == "Compression des fichiers."

    def test_load_invalid_locale(
            self, common_obj, locale_invalid, sys_onionshare_dev_mode):
        """ load_strings() raises a KeyError for an invalid locale """
        with pytest.raises(KeyError):
            common_obj.settings = Settings(common_obj)
            common_obj.settings.set('locale', 'XX')
            strings.load_strings(common_obj)
