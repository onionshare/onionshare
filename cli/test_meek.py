import sys
import onionshare_cli
from onionshare_cli import censorship

print("Using:", onionshare_cli.__file__)

orig = censorship.CensorshipCircumvention.request_builtin_bridges

def fake(self):
    # Fail only the over-Tor attempt; leave the Meek attempt alone
    if getattr(self, "onion", None):
        return False
    return orig(self)

censorship.CensorshipCircumvention.request_builtin_bridges = fake
sys.exit(onionshare_cli.main())
