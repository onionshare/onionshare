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

