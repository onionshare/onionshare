import json, locale
import helpers

strings = {}

def load_strings(default="en"):
    global strings
    translated = json.loads(open('{0}/strings.json'.format(helpers.get_onionshare_dir())).read())
    strings = translated[default]
    lc, enc = locale.getdefaultlocale()
    if lc:
        lang = lc[:2]
        if lang in translated:
            # if a string doesn't exist, fallback to English
            for key in translated[default]:
                if key in translated[lang]:
                    strings[key] = translated[lang][key]

def translated(k):
    return strings[k].encode("utf-8")

_ = translated
