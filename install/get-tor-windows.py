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

import inspect, os, sys, hashlib, zipfile, io, shutil
import urllib.request

def main():
    zip_url = 'https://archive.torproject.org/tor-package-archive/torbrowser/7.0.11/tor-win32-0.3.1.9.zip'
    zip_filename = 'tor-win32-0.3.1.9.zip'
    expected_zip_sha256 = 'faf28efb606455842bda66ca369287a116b6d6e5ad3720ebed9337da0717f1b4'

    # Build paths
    root_path = os.path.dirname(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))))
    working_path = os.path.join(os.path.join(root_path, 'build'), 'tor')
    zip_path = os.path.join(working_path, zip_filename)
    dist_path = os.path.join(os.path.join(os.path.join(root_path, 'dist'), 'onionshare'), 'tor')

    # Make sure the working folder exists
    if not os.path.exists(working_path):
        os.makedirs(working_path)

    # Make sure the zip is downloaded
    if not os.path.exists(zip_path):
        print("Downloading {}".format(zip_url))
        response = urllib.request.urlopen(zip_url)
        zip_data = response.read()
        open(zip_path, 'wb').write(zip_data)
        zip_sha256 = hashlib.sha256(zip_data).hexdigest()
    else:
        zip_data = open(zip_path, 'rb').read()
        zip_sha256 = hashlib.sha256(zip_data).hexdigest()

    # Compare the hash
    if zip_sha256 != expected_zip_sha256:
        print("ERROR! The sha256 doesn't match:")
        print("expected: {}".format(expected_zip_sha256))
        print("  actual: {}".format(zip_sha256))
        sys.exit(-1)

    # Extract the zip
    z = zipfile.ZipFile(io.BytesIO(zip_data))
    z.extractall(working_path)

    # Delete un-used files
    os.remove(os.path.join(os.path.join(working_path, 'Tor'), 'tor-gencert.exe'))

    # Copy into dist
    if os.path.exists(dist_path):
        shutil.rmtree(dist_path)
    os.makedirs(dist_path)
    shutil.copytree( os.path.join(working_path, 'Tor'), os.path.join(dist_path, 'Tor') )
    shutil.copytree( os.path.join(working_path, 'Data'), os.path.join(dist_path, 'Data') )

if __name__ == '__main__':
    main()
