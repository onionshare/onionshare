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
In order to avoid a Mac gnupg dependency, I manually verify the signature
and hard-code the sha256 hash.
"""

import inspect, os, sys, hashlib, zipfile, io, shutil, subprocess
import urllib.request

def main():
    dmg_url = 'https://www.torproject.org/dist/torbrowser/6.5.1/TorBrowser-6.5.1-osx64_en-US.dmg'
    dmg_filename = 'TorBrowser-6.5.1-osx64_en-US.dmg'
    expected_dmg_sha256 = '4155633dd51db9c805e8a81a9fd180e7235077f15023b5f002648f1c2a8bef92'

    # Build paths
    root_path = os.path.dirname(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))))
    working_path = os.path.join(root_path, 'build', 'tor')
    dmg_tor_path = os.path.join('/Volumes', 'Tor Browser', 'TorBrowser.app', 'Contents')
    dmg_path = os.path.join(working_path, dmg_filename)
    dist_path = os.path.join(root_path, 'dist', 'OnionShare.app', 'Contents')

    # Make sure the working folder exists
    if not os.path.exists(working_path):
        os.makedirs(working_path)

    # Make sure the zip is downloaded
    if not os.path.exists(dmg_path):
        print("Downloading {}".format(dmg_url))
        response = urllib.request.urlopen(dmg_url)
        dmg_data = response.read()
        open(dmg_path, 'wb').write(dmg_data)
        dmg_sha256 = hashlib.sha256(dmg_data).hexdigest()
    else:
        dmg_data = open(dmg_path, 'rb').read()
        dmg_sha256 = hashlib.sha256(dmg_data).hexdigest()

    # Compare the hash
    if dmg_sha256 != expected_dmg_sha256:
        print("ERROR! The sha256 doesn't match:")
        print("expected: {}".format(expected_dmg_sha256))
        print("  actual: {}".format(dmg_sha256))
        sys.exit(-1)

    # Mount the dmg, copy data to the working path
    subprocess.call(['hdiutil', 'attach', dmg_path])

    # Make sure Resources/tor exists before copying files
    if os.path.exists(os.path.join(dist_path, 'Resources', 'tor')):
        shutil.rmtree(os.path.join(dist_path, 'Resources', 'tor'))
    os.makedirs(os.path.join(dist_path, 'Resources', 'tor'))

    # Copy into dist
    shutil.copyfile(os.path.join(dmg_tor_path, 'Resources', 'TorBrowser', 'Tor', 'geoip'), os.path.join(dist_path, 'Resources', 'tor', 'geoip'))
    shutil.copyfile(os.path.join(dmg_tor_path, 'Resources', 'TorBrowser', 'Tor', 'geoip6'), os.path.join(dist_path, 'Resources', 'tor', 'geoip6'))
    shutil.copyfile(os.path.join(dmg_tor_path, 'MacOS', 'Tor', 'tor.real'), os.path.join(dist_path, 'MacOS', 'tor'))
    os.chmod(os.path.join(dist_path, 'MacOS', 'tor'), 0o755)

    # Unmount dmg
    subprocess.call(['diskutil', 'unmount', '/Volumes/Tor Browser'])

if __name__ == '__main__':
    main()
