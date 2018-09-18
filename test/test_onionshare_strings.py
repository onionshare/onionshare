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


# # Stub get_resource_path so it finds the correct path while running tests
# def get_resource_path(filename):
#     resources_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'share')
#     path = os.path.join(resources_dir, filename)
#     return path
# common.get_resource_path = get_resource_path


def test_starts_with_empty_strings():
    """ Creates an empty strings dict by default """
    assert strings.strings == {}


def test_underscore_is_function():
    assert callable(strings._) and isinstance(strings._, types.FunctionType)


class TestLoadStrings:
    def test_load_strings_defaults_to_english(
            self, common_obj, locale_en, sys_onionshare_dev_mode):
        """ load_strings() loads English by default """
        strings.load_strings(common_obj)
        assert strings._('wait_for_hs') == "Waiting for HS to be ready:"


    def test_load_strings_loads_other_languages(
            self, common_obj, locale_fr, sys_onionshare_dev_mode):
        """ load_strings() loads other languages in different locales """
        strings.load_strings(common_obj, "fr")
        assert strings._('wait_for_hs') == "En attente du HS:"

    def test_load_partial_strings(
            self, common_obj, locale_ru, sys_onionshare_dev_mode):
        strings.load_strings(common_obj)
        assert strings._("give_this_url") == (
            "Отправьте эту ссылку тому человеку, "
            "которому вы хотите передать файл:")
        assert strings._('wait_for_hs') == "Waiting for HS to be ready:"

    def test_load_invalid_locale(
            self, common_obj, locale_invalid, sys_onionshare_dev_mode):
        """ load_strings() raises a KeyError for an invalid locale """
        with pytest.raises(KeyError):
            strings.load_strings(common_obj, 'XX')
