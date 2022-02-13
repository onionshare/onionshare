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
    tarball_url = "https://dist.torproject.org/torbrowser/11.0.4/tor-browser-linux64-11.0.4_en-US.tar.xz"
    tarball_filename = "tor-browser-linux64-11.0.4_en-US.tar.xz"
    expected_tarball_sha256 = (
        "05a5fd6d633ca84c33bbd3e2f8ffca2d2fa2105032a430b07d3c0cf062d9e15f"
    )

    # Build paths
    root_path = os.path.dirname(
        os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    )
    working_path = os.path.join(root_path, "build", "tor")
    tarball_path = os.path.join(working_path, tarball_filename)
    dist_path = os.path.join(root_path, "onionshare", "resources", "tor")

    # Make sure dirs exist
    if not os.path.exists(working_path):
        os.makedirs(working_path, exist_ok=True)

    if not os.path.exists(dist_path):
        os.makedirs(dist_path, exist_ok=True)

    # Make sure the tarball is downloaded
    if not os.path.exists(tarball_path):
        print("Downloading {}".format(tarball_url))
        r = requests.get(tarball_url)
        open(tarball_path, "wb").write(r.content)
        tarball_sha256 = hashlib.sha256(r.content).hexdigest()
    else:
        tarball_data = open(tarball_path, "rb").read()
        tarball_sha256 = hashlib.sha256(tarball_data).hexdigest()

    # Compare the hash
    if tarball_sha256 != expected_tarball_sha256:
        print("ERROR! The sha256 doesn't match:")
        print("expected: {}".format(expected_tarball_sha256))
        print("  actual: {}".format(tarball_sha256))
        sys.exit(-1)

    # Delete extracted tarball, if it's there
    shutil.rmtree(os.path.join(working_path, "tor-browser_en-US"), ignore_errors=True)

    # Extract the tarball
    subprocess.call(["tar", "-xvf", tarball_path], cwd=working_path)
    tarball_tor_path = os.path.join(
        working_path, "tor-browser_en-US", "Browser", "TorBrowser"
    )

    # Copy into dist
    shutil.copyfile(
        os.path.join(tarball_tor_path, "Data", "Tor", "geoip"),
        os.path.join(dist_path, "geoip"),
    )
    shutil.copyfile(
        os.path.join(tarball_tor_path, "Data", "Tor", "geoip6"),
        os.path.join(dist_path, "geoip6"),
    )
    shutil.copyfile(
        os.path.join(tarball_tor_path, "Tor", "tor"),
        os.path.join(dist_path, "tor"),
    )
    os.chmod(os.path.join(dist_path, "tor"), 0o755)
    shutil.copyfile(
        os.path.join(tarball_tor_path, "Tor", "libcrypto.so.1.1"),
        os.path.join(dist_path, "libcrypto.so.1.1"),
    )
    shutil.copyfile(
        os.path.join(tarball_tor_path, "Tor", "libevent-2.1.so.7"),
        os.path.join(dist_path, "libevent-2.1.so.7"),
    )
    shutil.copyfile(
        os.path.join(tarball_tor_path, "Tor", "libssl.so.1.1"),
        os.path.join(dist_path, "libssl.so.1.1"),
    )
    shutil.copyfile(
        os.path.join(tarball_tor_path, "Tor", "libstdc++", "libstdc++.so.6"),
        os.path.join(dist_path, "libstdc++.so.6"),
    )
    shutil.copyfile(
        os.path.join(tarball_tor_path, "Tor", "PluggableTransports", "obfs4proxy"),
        os.path.join(dist_path, "obfs4proxy"),
    )
    os.chmod(os.path.join(dist_path, "obfs4proxy"), 0o755)
    shutil.copyfile(
        os.path.join(
            tarball_tor_path, "Tor", "PluggableTransports", "snowflake-client"
        ),
        os.path.join(dist_path, "snowflake-client"),
    )
    os.chmod(os.path.join(dist_path, "snowflake-client"), 0o755)

    print(f"Tor binaries extracted to: {dist_path}")

    # Fetch the built-in bridges
    UpdateTorBridges(root_path)


if __name__ == "__main__":
    main()
