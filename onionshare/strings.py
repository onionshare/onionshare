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
import json, locale, sys, platform, os
import helpers

strings = {}

def load_strings(default="en"):
    global strings

    # find locale dir
    if platform.system() == 'Linux':
        locale_dir = os.path.join(sys.prefix, 'share/onionshare/locale')
    else:
        locale_dir = os.path.join(os.path.dirname(helpers.get_onionshare_dir()), 'locale')

    # load all translations
    translated = {}
    for filename in os.listdir(locale_dir):
        abs_filename = os.path.join(locale_dir, filename)
        lang, ext = os.path.splitext(filename)
        if abs_filename.endswith('.json'):
            translated[lang] = json.loads(open(abs_filename).read())

    strings = translated[default]
    lc, enc = locale.getdefaultlocale()
    if lc:
        lang = lc[:2]
        if lang in translated:
            # if a string doesn't exist, fallback to English
            for key in translated[default]:
                if key in translated[lang]:
                    strings[key] = translated[lang][key]

def translated(k, gui=False):
    if gui:
        return strings[k].encode("utf-8").decode('utf-8', 'replace')
    else:
        return strings[k].encode("utf-8")

_ = translated
