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


import fileinput, argparse, re, os, codecs, json, sys


def arg_parser():
    desc = __doc__.strip().splitlines()[0]
    p = argparse.ArgumentParser(description=desc)
    p.add_argument('-d', default='.', help='onionshare directory',
                   metavar='ONIONSHARE_DIR', dest='onionshare_dir')
    p.add_argument('--show-all-keys', action='store_true',
                   help='show translation key in source and exit'),
    p.add_argument('-l', default='all', help='language code (default: all)',
                   metavar='LANG_CODE', dest='lang_code')
    return p


def files_in(*dirs):
    dir = os.path.join(*dirs)
    files = os.listdir(dir)
    return [os.path.join(dir, f) for f in files]


def main():
    parser = arg_parser()
    args = parser.parse_args()

    dir = args.onionshare_dir

    src = files_in(dir, 'onionshare') + \
          files_in(dir, 'onionshare_gui') + \
          files_in(dir, 'onionshare_gui/share_mode') + \
          files_in(dir, 'onionshare_gui/receive_mode') + \
          files_in(dir, 'install/scripts') + \
          files_in(dir, 'tests')
    pysrc = [p for p in src if p.endswith('.py')]

    lang_code = args.lang_code

    translate_keys = set()
    # load translate key from python source
    for line in fileinput.input(pysrc, openhook=fileinput.hook_encoded('utf-8')):
        # search `strings._('translate_key')`
        #        `strings._('translate_key', True)`
        m = re.findall(r'strings\._\((.*?)\)', line)
        if m:
            for match in m:
                key = match.split(',')[0].strip('''"' ''')
                translate_keys.add(key)

    if args.show_all_keys:
        for k in sorted(translate_keys):
            print(k)
        sys.exit()

    if lang_code == 'all':
        locale_files = [f for f in files_in(dir, 'share/locale') if f.endswith('.json')]
    else:
        locale_files = [f for f in files_in(dir, 'share/locale') if f.endswith('%s.json' % lang_code)]
    for locale_file in locale_files:
        with codecs.open(locale_file, 'r', encoding='utf-8') as f:
            trans = json.load(f)
        # trans -> {"key1": "translate-text1", "key2": "translate-text2", ...}
        locale_keys = set(trans.keys())

        disused = locale_keys - translate_keys
        lacked = translate_keys - locale_keys

        locale, ext = os.path.splitext(os.path.basename(locale_file))
        for k in sorted(disused):
            print(locale, 'disused', k)

        for k in sorted(lacked):
            print(locale, 'lacked', k)


if __name__ == '__main__':
    main()
