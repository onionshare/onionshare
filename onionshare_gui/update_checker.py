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
import datetime, time, socks, socket, re, platform

from . import strings, helpers
from onionshare.settings import Settings
from onionshare.onion import Onion
from .alert import Alert

class UpdateCheckerTorError(Exception):
    """
    Error checking for updates because of some Tor connection issue.
    """
    pass

class UpdateCheckerSOCKSHTTPError(Exception):
    """
    Error checking for updates because of some SOCKS proxy or HTTP request issue.
    """
    pass

class UpdateCheckerInvalidLatestVersion(Exception):
    """
    Successfully downloaded the latest version, but it doesn't appear to be a
    valid version string.
    """
    def __init__(self, latest_version):
        self.latest_version = latest_version

def check_for_updates(force=False, bundled_tor_func=None):
    """
    Load http://elx57ue5uyfplgva.onion/latest-version.txt to see what the latest
    version of OnionShare is. If the latest version is newer than the
    installed version, alert the user.

    Only check at most once per day, unless force is True.
    """
    # Load the settings
    settings = Settings()
    settings.load()

    # See if it's been 1 day since the last check, and if so set force to True
    if not force:
        autoupdate_timestamp = settings.get('autoupdate_timestamp')
        if autoupdate_timestamp:
            last_checked = datetime.datetime.fromtimestamp(autoupdate_timestamp)
            now = datetime.datetime.now()

            one_day = datetime.timedelta(days=1)
            if now - last_checked > one_day:
                force = True
        else:
            force = True

    # Check for updates
    if force:
        # Create an Onion object, for checking for updates over tor
        try:
            onion = Onion(settings=settings, bundled_tor_func=bundled_tor_func)
        except:
            raise UpdateCheckerTorError

        # Download the latest-version file over Tor
        try:
            (socks_address, socks_port) = onion.get_tor_socks_port()
            socks.set_default_proxy(socks.SOCKS5, socks_address, socks_port)

            s = socks.socksocket()
            s.connect(('elx57ue5uyfplgva.onion', 80))

            http_request = 'GET /latest-version.txt HTTP/1.0\r\n'
            http_request += 'Host: elx57ue5uyfplgva.onion\r\n'
            http_request += 'User-Agent: OnionShare {}, {}\r\n'.format(helpers.get_version(), platform.system())
            http_request += '\r\n'
            s.sendall(http_request.encode('utf-8'))

            http_response = s.recv(1024)
            latest_version = http_response[http_response.find(b'\r\n\r\n'):].strip().decode('utf-8')

            # Clean up from Onion
            onion.cleanup()
        except:
            raise UpdateCheckerSOCKSHTTPError

        # Validate that latest_version looks like a version string
        # This regex is: 1-3 dot-separated numeric components
        version_re = r"^(\d+\.)?(\d+\.)?(\d+)$"
        if not re.match(version_re, latest_version):
            raise UpdateCheckerInvalidLatestVersion(latest_version)

        # Update the last checked timestamp (dropping the seconds and milliseconds)
        timestamp = datetime.datetime.now().replace(microsecond=0).replace(second=0).timestamp()
        settings.set('autoupdate_timestamp', timestamp)
        settings.save()

        # Do we need to update?
        update_url = 'https://github.com/micahflee/onionshare/releases/tag/v{}'.format(latest_version)
        installed_version = helpers.get_version()
        if installed_version < latest_version:
            Alert(strings._("update_available", True).format(update_url, installed_version, latest_version))
            return True

        return False
