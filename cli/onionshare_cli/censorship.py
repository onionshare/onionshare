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
import requests


class CensorshipCircumventionError(Exception):
    """
    There was a problem connecting to the Tor CensorshipCircumvention API.
    """


class CensorshipCircumvention(object):
    """
    Connect to the Tor Moat APIs to retrieve censorship
    circumvention recommendations or the latest bridges.

    We support reaching this API over Tor, or Meek
    (domain fronting) if Tor is not connected.
    """

    def __init__(self, common, meek=None, onion=None):
        """
        Set up the CensorshipCircumvention object to hold
        common and meek objects.
        """
        self.common = common
        self.common.log("CensorshipCircumvention", "__init__")
        self.api_proxies = {}
        if meek:
            self.meek = meek
            self.common.log(
                "CensorshipCircumvention",
                "__init__",
                "Using Meek with CensorshipCircumvention API",
            )
            self.api_proxies = self.meek.meek_proxies
        if onion:
            self.onion = onion
            if not self.onion.is_authenticated:
                return False
            else:
                self.common.log(
                    "CensorshipCircumvention",
                    "__init__",
                    "Using Tor with CensorshipCircumvention API",
                )
                (socks_address, socks_port) = self.onion.get_tor_socks_port()
                self.api_proxies = {
                    "http": f"socks5h://{socks_address}:{socks_port}",
                    "https": f"socks5h://{socks_address}:{socks_port}",
                }

    def request_map(self, country=False):
        """
        Retrieves the Circumvention map from Tor Project and store it
        locally for further look-ups if required.

        Optionally pass a country code in order to get recommended settings
        just for that country.

        Note that this API endpoint doesn't return actual bridges,
        it just returns the recommended bridge type countries.
        """
        if not self.api_proxies:
            return False
        endpoint = "https://bridges.torproject.org/moat/circumvention/map"
        data = {}
        if country:
            data = {"country": country}

        try:
            r = requests.post(
                endpoint,
                json=data,
                headers={"Content-Type": "application/vnd.api+json"},
                proxies=self.api_proxies,
            )
            if r.status_code != 200:
                self.common.log(
                    "CensorshipCircumvention",
                    "censorship_obtain_map",
                    f"status_code={r.status_code}",
                )
                return False

            result = r.json()

            if "errors" in result:
                self.common.log(
                    "CensorshipCircumvention",
                    "censorship_obtain_map",
                    f"errors={result['errors']}",
                )
                return False

            return result
        except requests.exceptions.RequestException as e:
            raise CensorshipCircumventionError(e)

    def request_settings(self, country=False, transports=False):
        """
        Retrieves the Circumvention Settings from Tor Project, which
        will return recommended settings based on the country code of
        the requesting IP.

        Optionally, a country code can be specified in order to override
        the IP detection.

        Optionally, a list of transports can be specified in order to
        return recommended settings for just that transport type.
        """
        if not self.api_proxies:
            return False
        endpoint = "https://bridges.torproject.org/moat/circumvention/settings"
        data = {}
        if country:
            self.common.log(
                "CensorshipCircumvention",
                "censorship_obtain_settings",
                f"Trying to obtain bridges for country={country}",
            )
            data = {"country": country}
        if transports:
            data.append({"transports": transports})
        try:
            r = requests.post(
                endpoint,
                json=data,
                headers={"Content-Type": "application/vnd.api+json"},
                proxies=self.api_proxies,
            )
            if r.status_code != 200:
                self.common.log(
                    "CensorshipCircumvention",
                    "censorship_obtain_settings",
                    f"status_code={r.status_code}",
                )
                return False

            result = r.json()

            if "errors" in result:
                self.common.log(
                    "CensorshipCircumvention",
                    "censorship_obtain_settings",
                    f"errors={result['errors']}",
                )
                return False

            # There are no settings - perhaps this country doesn't require censorship circumvention?
            # This is not really an error, so we can just check if False and assume direct Tor
            # connection will work.
            if not "settings" in result:
                self.common.log(
                    "CensorshipCircumvention",
                    "censorship_obtain_settings",
                    "No settings found for this country",
                )
                return False

            return result
        except requests.exceptions.RequestException as e:
            raise CensorshipCircumventionError(e)

    def request_builtin_bridges(self):
        """
        Retrieves the list of built-in bridges from the Tor Project.
        """
        if not self.api_proxies:
            return False
        endpoint = "https://bridges.torproject.org/moat/circumvention/builtin"
        try:
            r = requests.post(
                endpoint,
                headers={"Content-Type": "application/vnd.api+json"},
                proxies=self.api_proxies,
            )
            if r.status_code != 200:
                self.common.log(
                    "CensorshipCircumvention",
                    "censorship_obtain_builtin_bridges",
                    f"status_code={r.status_code}",
                )
                return False

            result = r.json()

            if "errors" in result:
                self.common.log(
                    "CensorshipCircumvention",
                    "censorship_obtain_builtin_bridges",
                    f"errors={result['errors']}",
                )
                return False

            return result
        except requests.exceptions.RequestException as e:
            raise CensorshipCircumventionError(e)

    def save_settings(self, settings, bridge_settings):
        """
        Checks the bridges and saves them in settings.
        """
        bridges_ok = False
        self.settings = settings

        # @TODO there might be several bridge types recommended.
        # Should we attempt to iterate over each type if one of them fails to connect?
        # But if so, how to stop it starting 3 separate Tor connection threads?
        # for bridges in request_bridges["settings"]:
        bridges = bridge_settings["settings"][0]["bridges"]
        self.common.log(
            "CensorshipCircumvention",
            "save_settings",
            f"Obtained bridges: {bridges}",
        )
        bridge_strings = bridges["bridge_strings"]
        bridge_type = bridges["type"]
        bridge_source = bridges["source"]

        # If the recommended bridge source is to use the built-in
        # bridges, set that in our settings, as if the user had
        # selected the built-in bridges for a specific PT themselves.
        #
        if bridge_source == "builtin":
            self.common.log(
                "CensorshipCircumvention",
                "save_settings",
                "Will be using built-in bridges",
            )
            self.settings.set("bridges_type", "built-in")
            if bridge_type == "obfs4":
                self.settings.set("bridges_builtin_pt", "obfs4")
            if bridge_type == "snowflake":
                self.settings.set("bridges_builtin_pt", "snowflake")
            if bridge_type == "meek":
                self.settings.set("bridges_builtin_pt", "meek-azure")
            bridges_ok = True
        else:
            self.common.log(
                "CensorshipCircumvention",
                "save_settings",
                "Will be using custom bridges",
            )
            # Any other type of bridge we can treat as custom.
            self.settings.set("bridges_type", "custom")

            # Sanity check the bridges provided from the Tor API before saving
            bridges_checked = self.common.check_bridges_valid(bridge_strings)

            if bridges_checked:
                self.settings.set("bridges_custom", "\n".join(bridges_checked))
                bridges_ok = True

        # If we got any good bridges, save them to settings and return.
        if bridges_ok:
            self.common.log(
                "CensorshipCircumvention",
                "save_settings",
                "Saving settings with automatically-obtained bridges",
            )
            self.settings.set("bridges_enabled", True)
            self.settings.save()
            return True
        else:
            self.common.log(
                "CensorshipCircumvention",
                "save_settings",
                "Could not use any of the obtained bridges.",
            )
            return False
