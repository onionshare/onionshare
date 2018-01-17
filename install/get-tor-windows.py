# -*- coding: utf-8 -*-
"""
OnionShare | https://onionshare.org/

Copyright (C) 2017 Micah Lee <micah@micahflee.com>

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

import inspect, os, sys, hashlib, shutil, subprocess
import urllib.request

def main():
    exe_url = 'https://archive.torproject.org/tor-package-archive/torbrowser/7.0.11/torbrowser-install-7.0.11_en-US.exe'
    exe_filename = 'torbrowser-install-7.0.11_en-US.exe'
    expected_exe_sha256 = 'a033eb9b9ed2ad389169b36a90946a8af8f05bd0c7bbd3e37678041331096624'
    # Build paths
    root_path = os.path.dirname(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))))
    working_path = os.path.join(os.path.join(root_path, 'build'), 'tor')
    exe_path = os.path.join(working_path, exe_filename)
    dist_path = os.path.join(os.path.join(os.path.join(root_path, 'dist'), 'onionshare'), 'tor')

    # Make sure the working folder exists
    if not os.path.exists(working_path):
        os.makedirs(working_path)

    # Make sure the zip is downloaded
    if not os.path.exists(exe_path):
        print("Downloading {}".format(exe_url))
        response = urllib.request.urlopen(exe_url)
        exe_data = response.read()
        open(exe_path, 'wb').write(exe_data)
        exe_sha256 = hashlib.sha256(exe_data).hexdigest()
    else:
        exe_data = open(exe_path, 'rb').read()
        exe_sha256 = hashlib.sha256(exe_data).hexdigest()

    # Compare the hash
    if exe_sha256 != expected_exe_sha256:
        print("ERROR! The sha256 doesn't match:")
        print("expected: {}".format(expected_exe_sha256))
        print("  actual: {}".format(exe_sha256))
        sys.exit(-1)

    # Extract the bits we need from the exe
    cmd = ['7z', 'e', exe_path, 'Browser\TorBrowser\Tor', '-o%s' % os.path.join(working_path, 'Tor')]
    cmd2 = ['7z', 'e', exe_path, 'Browser\TorBrowser\Data\Tor\geoip*', '-o%s' % os.path.join(working_path, 'Data')]
    subprocess.Popen(cmd).wait()
    subprocess.Popen(cmd2).wait()

    # Copy into dist
    if os.path.exists(dist_path):
        shutil.rmtree(dist_path)
    os.makedirs(dist_path)
    shutil.copytree( os.path.join(working_path, 'Tor'), os.path.join(dist_path, 'Tor') )
    shutil.copytree( os.path.join(working_path, 'Data'), os.path.join(dist_path, 'Data', 'Tor') )

if __name__ == '__main__':
    main()
