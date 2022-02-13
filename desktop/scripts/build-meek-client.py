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
import shutil
import os
import subprocess
import inspect
import platform


def main():
    if shutil.which("go") is None:
        print("Install go: https://golang.org/doc/install")
        return

    subprocess.run(
        [
            "go",
            "install",
            "git.torproject.org/pluggable-transports/meek.git/meek-client@v0.37.0",
        ]
    )

    root_path = os.path.dirname(
        os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    )
    if platform.system() == "Windows":
        dist_path = os.path.join(root_path, "onionshare", "resources", "tor", "Tor")
        bin_filename = "meek-client.exe"
    else:
        dist_path = os.path.join(root_path, "onionshare", "resources", "tor")
        bin_filename = "meek-client"

    bin_path = os.path.join(os.path.expanduser("~"), "go", "bin", bin_filename)
    shutil.copyfile(
        os.path.join(bin_path),
        os.path.join(dist_path, bin_filename),
    )
    os.chmod(os.path.join(dist_path, bin_filename), 0o755)

    print(f"Installed {bin_filename} in {dist_path}")


if __name__ == "__main__":
    main()
