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

from PySide2 import QtCore
import datetime
import re
import socks
from distutils.version import LooseVersion as Version

from onionshare_cli.settings import Settings


class UpdateCheckerCheckError(Exception):
    """
    Error checking for updates because of some Tor connection issue, or because
    the OnionShare website is down.
    """

    pass


class UpdateCheckerInvalidLatestVersion(Exception):
    """
    Successfully downloaded the latest version, but it doesn't appear to be a
    valid version string.
    """

    def __init__(self, latest_version):
        self.latest_version = latest_version


class UpdateChecker(QtCore.QObject):
    """
    Load http://elx57ue5uyfplgva.onion/latest-version.txt to see what the latest
    version of OnionShare is. If the latest version is newer than the
    installed version, alert the user.

    Only check at most once per day, unless force is True.
    """

    update_available = QtCore.Signal(str, str, str)
    update_not_available = QtCore.Signal()
    update_error = QtCore.Signal()
    update_invalid_version = QtCore.Signal(str)

    def __init__(self, common, onion):
        super(UpdateChecker, self).__init__()

        self.common = common

        self.common.log("UpdateChecker", "__init__")
        self.onion = onion

    def check(self, force=False):
        self.common.log("UpdateChecker", "check", f"force={force}")
        # Load the settings
        settings = Settings(self.common)
        settings.load()

        # If force=True, then definitely check
        if force:
            check_for_updates = True
        else:
            check_for_updates = False

            # See if it's been 1 day since the last check
            autoupdate_timestamp = settings.get("autoupdate_timestamp")
            if autoupdate_timestamp:
                last_checked = datetime.datetime.fromtimestamp(autoupdate_timestamp)
                now = datetime.datetime.now()

                one_day = datetime.timedelta(days=1)
                if now - last_checked > one_day:
                    check_for_updates = True
            else:
                check_for_updates = True

        # Check for updates
        if check_for_updates:
            self.common.log("UpdateChecker", "check", "checking for updates")
            # Download the latest-version file over Tor
            try:
                # User agent string includes OnionShare version and platform
                user_agent = f"OnionShare {self.common.version}, {self.common.platform}"

                # If the update is forced, add '?force=1' to the URL, to more
                # accurately measure daily users
                path = "/latest-version.txt"
                if force:
                    path += "?force=1"

                if Version(self.onion.tor_version) >= Version("0.3.2.9"):
                    onion_domain = (
                        "lldan5gahapx5k7iafb3s4ikijc4ni7gx5iywdflkba5y2ezyg6sjgyd.onion"
                    )
                else:
                    onion_domain = "elx57ue5uyfplgva.onion"

                self.common.log(
                    "UpdateChecker", "check", f"loading http://{onion_domain}{path}"
                )

                (socks_address, socks_port) = self.onion.get_tor_socks_port()
                socks.set_default_proxy(socks.SOCKS5, socks_address, socks_port)

                s = socks.socksocket()
                s.settimeout(15)  # 15 second timeout
                s.connect((onion_domain, 80))

                http_request = f"GET {path} HTTP/1.0\r\n"
                http_request += f"Host: {onion_domain}\r\n"
                http_request += f"User-Agent: {user_agent}\r\n"
                http_request += "\r\n"
                s.sendall(http_request.encode("utf-8"))

                http_response = s.recv(1024)
                latest_version = (
                    http_response[http_response.find(b"\r\n\r\n") :]
                    .strip()
                    .decode("utf-8")
                )

                self.common.log(
                    "UpdateChecker",
                    "check",
                    f"latest OnionShare version: {latest_version}",
                )

            except Exception as e:
                self.common.log("UpdateChecker", "check", str(e))
                self.update_error.emit()
                raise UpdateCheckerCheckError

            # Validate that latest_version looks like a version string
            # This regex is: 1-3 dot-separated numeric components
            version_re = r"^(\d+\.)?(\d+\.)?(\d+)$"
            if not re.match(version_re, latest_version):
                self.update_invalid_version.emit(latest_version)
                raise UpdateCheckerInvalidLatestVersion(latest_version)

            # Update the last checked timestamp (dropping the seconds and milliseconds)
            timestamp = (
                datetime.datetime.now()
                .replace(microsecond=0)
                .replace(second=0)
                .timestamp()
            )
            # Re-load the settings first before saving, just in case they've changed since we started our thread
            settings.load()
            settings.set("autoupdate_timestamp", timestamp)
            settings.save()

            # Do we need to update?
            update_url = "https://onionshare.org"
            installed_version = self.common.version
            if installed_version < latest_version:
                self.update_available.emit(
                    update_url, installed_version, latest_version
                )
                return

            # No updates are available
            self.update_not_available.emit()


class UpdateThread(QtCore.QThread):
    update_available = QtCore.Signal(str, str, str)
    update_not_available = QtCore.Signal()
    update_error = QtCore.Signal()
    update_invalid_version = QtCore.Signal(str)

    def __init__(self, common, onion, force=False):
        super(UpdateThread, self).__init__()

        self.common = common

        self.common.log("UpdateThread", "__init__")
        self.onion = onion
        self.force = force

    def run(self):
        self.common.log("UpdateThread", "run")

        u = UpdateChecker(self.common, self.onion)
        u.update_available.connect(self._update_available)
        u.update_not_available.connect(self._update_not_available)
        u.update_error.connect(self._update_error)
        u.update_invalid_version.connect(self._update_invalid_version)

        try:
            u.check(force=self.force)
        except Exception as e:
            # If update check fails, silently ignore
            self.common.log("UpdateThread", "run", str(e))
            pass

    def _update_available(self, update_url, installed_version, latest_version):
        self.common.log("UpdateThread", "_update_available")
        self.active = False
        self.update_available.emit(update_url, installed_version, latest_version)

    def _update_not_available(self):
        self.common.log("UpdateThread", "_update_not_available")
        self.active = False
        self.update_not_available.emit()

    def _update_error(self):
        self.common.log("UpdateThread", "_update_error")
        self.active = False
        self.update_error.emit()

    def _update_invalid_version(self, latest_version):
        self.common.log("UpdateThread", "_update_invalid_version")
        self.active = False
        self.update_invalid_version.emit(latest_version)
