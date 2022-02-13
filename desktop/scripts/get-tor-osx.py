#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OnionShare | https://onionshare.org/

Copyright (C) 2014-2022 Micah Lee, et al. <micah@micahflee.com>

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

"""
This script downloads a pre-built tor binary to bundle with OnionShare.
In order to avoid a Mac gnupg dependency, I manually verify the signature
and hard-code the sha256 hash.
"""
import inspect
import os
import sys
import hashlib
import shutil
import subprocess
import requests

from bridges import UpdateTorBridges


def main():
    dmg_url = "https://dist.torproject.org/torbrowser/11.0.4/TorBrowser-11.0.4-osx64_en-US.dmg"
    dmg_filename = "TorBrowser-11.0.4-osx64_en-US.dmg"
    expected_dmg_sha256 = (
        "309a67c8a82ae266756d7cf5ea00e94d9242e59d55eaff97dcd6201da3c8449c"
    )

    # Build paths
    root_path = os.path.dirname(
        os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    )
    working_path = os.path.join(root_path, "build", "tor")
    dmg_tor_path = os.path.join(
        "/Volumes", "Tor Browser", "Tor Browser.app", "Contents"
    )
    dmg_path = os.path.join(working_path, dmg_filename)
    dist_path = os.path.join(root_path, "onionshare", "resources", "tor")
    if not os.path.exists(dist_path):
        os.makedirs(dist_path, exist_ok=True)

    # Make sure the working folder exists
    if not os.path.exists(working_path):
        os.makedirs(working_path)

    # Make sure the zip is downloaded
    if not os.path.exists(dmg_path):
        print("Downloading {}".format(dmg_url))
        r = requests.get(dmg_url)
        open(dmg_path, "wb").write(r.content)
        dmg_sha256 = hashlib.sha256(r.content).hexdigest()
    else:
        dmg_data = open(dmg_path, "rb").read()
        dmg_sha256 = hashlib.sha256(dmg_data).hexdigest()

    # Compare the hash
    if dmg_sha256 != expected_dmg_sha256:
        print("ERROR! The sha256 doesn't match:")
        print("expected: {}".format(expected_dmg_sha256))
        print("  actual: {}".format(dmg_sha256))
        sys.exit(-1)

    # Mount the dmg, copy data to the working path
    subprocess.call(["hdiutil", "attach", dmg_path])

    # Copy into dist
    shutil.copyfile(
        os.path.join(dmg_tor_path, "Resources", "TorBrowser", "Tor", "geoip"),
        os.path.join(dist_path, "geoip"),
    )
    shutil.copyfile(
        os.path.join(dmg_tor_path, "Resources", "TorBrowser", "Tor", "geoip6"),
        os.path.join(dist_path, "geoip6"),
    )
    shutil.copyfile(
        os.path.join(dmg_tor_path, "MacOS", "Tor", "tor.real"),
        os.path.join(dist_path, "tor"),
    )
    os.chmod(os.path.join(dist_path, "tor"), 0o755)
    shutil.copyfile(
        os.path.join(dmg_tor_path, "MacOS", "Tor", "libevent-2.1.7.dylib"),
        os.path.join(dist_path, "libevent-2.1.7.dylib"),
    )
    # obfs4proxy binary
    shutil.copyfile(
        os.path.join(dmg_tor_path, "MacOS", "Tor", "PluggableTransports", "obfs4proxy"),
        os.path.join(dist_path, "obfs4proxy"),
    )
    os.chmod(os.path.join(dist_path, "obfs4proxy"), 0o755)
    # snowflake-client binary
    shutil.copyfile(
        os.path.join(
            dmg_tor_path, "MacOS", "Tor", "PluggableTransports", "snowflake-client"
        ),
        os.path.join(dist_path, "snowflake-client"),
    )
    os.chmod(os.path.join(dist_path, "snowflake-client"), 0o755)

    # Eject dmg
    subprocess.call(["diskutil", "eject", "/Volumes/Tor Browser"])

    # Fetch the built-in bridges
    UpdateTorBridges(root_path)


if __name__ == "__main__":
    main()
