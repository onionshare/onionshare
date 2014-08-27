from onionshare import helpers
from nose import with_setup

import test_helpers

def test_get_platform_on_tails():
    "get_platform() returns 'Tails' when hostname is 'amnesia'"
    helpers.platform.uname = lambda: ('Linux', 'amnesia', '3.14-1-amd64', '#1 SMP Debian 3.14.4-1 (2014-05-13)', 'x86_64', '')
    assert helpers.get_platform() == 'Tails'

def test_get_platform_returns_platform_system():
    "get_platform() returns platform.system() when ONIONSHARE_PLATFORM is not defined"
    helpers.platform.system = lambda: 'Sega Saturn'
    assert helpers.get_platform() == 'Sega Saturn'

def test_filehash_returns_correct_hash():
    "file_crunching() returns correct hash"

    text = """
           If you want a picture of the future, imagine a boot stamping on an
           encrypted, redundant, distributed filesystem -- forever.
           """
    tempfile = test_helpers.write_tempfile(text)
    filehash, _ = helpers.file_crunching(tempfile)

    assert filehash == 'bc004fe72e6530a545570b4c6ce76bcb78ea526b'

def test_filehash_returns_correct_size():
    "file_crunching() returns correct size"

    text = "AUSCANNZUKUS has always been at war with Eastasia."
    tempfile = test_helpers.write_tempfile(text)
    _, filesize = helpers.file_crunching(tempfile)

    assert filesize == 50
