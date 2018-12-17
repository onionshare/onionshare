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
import locale
import os

strings = {}
translations = {}


def load_strings(common):
    """
    Loads translated strings and fallback to English
    if the translation does not exist.
    """
    global strings, translations

    # Load all translations
    translations = {}
    for locale in common.settings.available_locales:
        locale_dir = common.get_resource_path('locale')
        filename = os.path.join(locale_dir, "{}.json".format(locale))
        with open(filename, encoding='utf-8') as f:
            translations[locale] = json.load(f)

    # Build strings
    default_locale = 'en'
    current_locale = common.settings.get('locale')
    strings = {}
    for s in translations[default_locale]:
        if s in translations[current_locale] and translations[current_locale][s] != "":
            strings[s] = translations[current_locale][s]
        else:
            strings[s] = translations[default_locale][s]


def translated(k):
    """
    Returns a translated string.
    """
    return strings[k]

_ = translated
