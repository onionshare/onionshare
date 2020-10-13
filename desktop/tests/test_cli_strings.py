# -*- coding: utf-8 -*-
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
        self, common_obj, locale_en, sys_onionshare_dev_mode
    ):
        """ load_strings() loads English by default """
        common_obj.settings = Settings(common_obj)
        strings.load_strings(common_obj)
        assert strings._("not_a_readable_file") == "{0:s} is not a readable file."

    def test_load_strings_loads_other_languages(
        self, common_obj, locale_fr, sys_onionshare_dev_mode
    ):
        """ load_strings() loads other languages in different locales """
        common_obj.settings = Settings(common_obj)
        common_obj.settings.set("locale", "fr")
        strings.load_strings(common_obj)
        assert strings._("not_a_readable_file") == "{0:s} n’est pas un fichier lisible."

    def test_load_invalid_locale(
        self, common_obj, locale_invalid, sys_onionshare_dev_mode
    ):
        """ load_strings() raises a KeyError for an invalid locale """
        with pytest.raises(KeyError):
            common_obj.settings = Settings(common_obj)
            common_obj.settings.set("locale", "XX")
            strings.load_strings(common_obj)
