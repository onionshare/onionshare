import locale
from onionshare import strings
from nose import with_setup

def test_starts_with_empty_strings():
    "creates an empty strings dict by default"
    assert strings.strings == {}

def test_load_strings_defaults_to_english():
    "load_strings() loads English by default"
    locale.getdefaultlocale = lambda: ('en_US', 'UTF-8')
    strings.load_strings()
    assert strings._('calculating_sha1') == "Calculating SHA1 checksum."

def test_load_strings_loads_other_languages():
    "load_strings() loads other languages in different locales"
    locale.getdefaultlocale = lambda: ('fr_FR', 'UTF-8')
    strings.load_strings("fr")
    assert strings._('calculating_sha1') == "Calculer un hachage SHA-1."


