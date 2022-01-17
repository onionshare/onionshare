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
In order to avoid a Windows gnupg dependency, I manually verify the signature
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
    exe_url = "https://dist.torproject.org/torbrowser/11.0.4/torbrowser-install-11.0.4_en-US.exe"
    exe_filename = "torbrowser-install-11.0.4_en-US.exe"
    expected_exe_sha256 = (
        "c7073f58f49a225bcf7668a5630e94f5f5e96fb7bed095feebf3bf8417bd3d07"
    )
    # Build paths
    root_path = os.path.dirname(
        os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    )
    working_path = os.path.join(root_path, "build", "tor")
    exe_path = os.path.join(working_path, exe_filename)
    dist_path = os.path.join(root_path, "onionshare", "resources", "tor")

    # Make sure the working folder exists
    if not os.path.exists(working_path):
        os.makedirs(working_path)

    # Make sure Tor Browser is downloaded
    if not os.path.exists(exe_path):
        print("Downloading {}".format(exe_url))
        r = requests.get(exe_url)
        open(exe_path, "wb").write(r.content)
        exe_sha256 = hashlib.sha256(r.content).hexdigest()
    else:
        exe_data = open(exe_path, "rb").read()
        exe_sha256 = hashlib.sha256(exe_data).hexdigest()

    # Compare the hash
    if exe_sha256 != expected_exe_sha256:
        print("ERROR! The sha256 doesn't match:")
        print("expected: {}".format(expected_exe_sha256))
        print("  actual: {}".format(exe_sha256))
        sys.exit(-1)

    # Extract the bits we need from the exe
    subprocess.Popen(
        [
            "7z",
            "e",
            "-y",
            exe_path,
            "Browser\\TorBrowser\\Tor",
            "-o%s" % os.path.join(working_path, "Tor"),
        ]
    ).wait()
    subprocess.Popen(
        [
            "7z",
            "e",
            "-y",
            exe_path,
            "Browser\\TorBrowser\\Data\\Tor\\geoip*",
            "-o%s" % os.path.join(working_path, "Data"),
        ]
    ).wait()

    # Copy into the onionshare resources
    if os.path.exists(dist_path):
        shutil.rmtree(dist_path)
    os.makedirs(dist_path)
    shutil.copytree(os.path.join(working_path, "Tor"), os.path.join(dist_path, "Tor"))
    shutil.copytree(
        os.path.join(working_path, "Data"), os.path.join(dist_path, "Data", "Tor")
    )

    # Fetch the built-in bridges
    UpdateTorBridges(root_path)


if __name__ == "__main__":
    main()
