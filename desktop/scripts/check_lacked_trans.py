#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Check translation lacked or disused.

Example:
in OnionShare directory
$ check_lacked_trans.py
de disused choose_file
de disused gui_starting_server
de lacked gui_canceled
de lacked gui_starting_server1
de lacked gui_starting_server2
de lacked gui_starting_server3
en disused choose_file
es disused choose_file
es disused gui_starting_server
...


1. search `{{strings.translation_key}}` and `strings._('translation_key')`
   from .py or .html files.
2. load translation key from locale/*.json.
3. compare these.

"""


import argparse
import re
import os
import codecs
import json
import sys


def arg_parser():
    desc = __doc__.strip().splitlines()[0]
    p = argparse.ArgumentParser(description=desc)
    p.add_argument(
        "-d",
        default=".",
        help="onionshare directory",
        metavar="ONIONSHARE_DIR",
        dest="onionshare_dir",
    )
    p.add_argument(
        "--show-all-keys",
        action="store_true",
        help="show translation key in source and exit",
    ),
    p.add_argument(
        "-l",
        default="all",
        help="language code (default: all)",
        metavar="LANG_CODE",
        dest="lang_code",
    )
    return p


def files_in(*dirs):
    dir = os.path.join(*dirs)
    files = os.listdir(dir)
    return [os.path.join(dir, f) for f in files]


def main():
    parser = arg_parser()
    args = parser.parse_args()

    dir = args.onionshare_dir

    src = (
        files_in(dir, "onionshare_gui")
        + files_in(dir, "onionshare_gui/tab")
        + files_in(dir, "onionshare_gui/tab/mode")
        + files_in(dir, "onionshare_gui/tab/mode/chat_mode")
        + files_in(dir, "onionshare_gui/tab/mode/receive_mode")
        + files_in(dir, "onionshare_gui/tab/mode/share_mode")
        + files_in(dir, "onionshare_gui/tab/mode/website_mode")
        + files_in(dir, "install/scripts")
    )
    filenames = [p for p in src if p.endswith(".py")]

    lang_code = args.lang_code

    translate_keys = set()
    for filename in filenames:
        # load translate key from python source
        with open(filename) as f:
            src = f.read()

        # find all the starting strings
        start_substr = "strings._\("
        starting_indices = [m.start() for m in re.finditer(start_substr, src)]

        for starting_i in starting_indices:
            # are we dealing with single quotes or double quotes?
            quote = None
            inc = 0
            while True:
                quote_i = starting_i + len("strings._(") + inc
                if src[quote_i] == '"':
                    quote = '"'
                    break
                if src[quote_i] == "'":
                    quote = "'"
                    break
                inc += 1

            # find the starting quote
            starting_i = src.find(quote, starting_i)
            if starting_i:
                starting_i += 1
                # find the ending quote
                ending_i = src.find(quote, starting_i)
                if ending_i:
                    key = src[starting_i:ending_i]
                    translate_keys.add(key)

    if args.show_all_keys:
        for k in sorted(translate_keys):
            print(k)
        sys.exit()

    if lang_code == "all":
        locale_files = [f for f in files_in(dir, "share/locale") if f.endswith(".json")]
    else:
        locale_files = [
            f
            for f in files_in(dir, "share/locale")
            if f.endswith("%s.json" % lang_code)
        ]
    for locale_file in locale_files:
        with codecs.open(locale_file, "r", encoding="utf-8") as f:
            trans = json.load(f)
        # trans -> {"key1": "translate-text1", "key2": "translate-text2", ...}
        locale_keys = set(trans.keys())

        disused = locale_keys - translate_keys
        lacked = translate_keys - locale_keys

        locale, ext = os.path.splitext(os.path.basename(locale_file))
        for k in sorted(disused):
            print(locale, "disused", k)

        for k in sorted(lacked):
            print(locale, "lacked", k)


if __name__ == "__main__":
    main()
