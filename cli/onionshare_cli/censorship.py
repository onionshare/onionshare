# -*- coding: utf-8 -*-
"""
OnionShare | https://onionshare.org/

Copyright (C) 2014-2021 Micah Lee, et al. <micah@micahflee.com>

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
import subprocess


class CensorshipCircumvention:
    """
    The CensorShipCircumvention object contains methods to detect
    and offer solutions to censorship when connecting to Tor.
    """

    def __init__(self, common):

        self.common = common
        self.common.log("CensorshipCircumvention", "__init__")

        get_tor_paths = self.common.get_tor_paths
        (
            self.tor_path,
            self.tor_geo_ip_file_path,
            self.tor_geo_ipv6_file_path,
            self.obfs4proxy_file_path,
            self.meek_client_file_path,
        ) = get_tor_paths()

        meek_url = "https://moat.torproject.org.global.prod.fastly.net/"
        meek_front = "cdn.sstatic.net"
        meek_env = {
            "TOR_PT_MANAGED_TRANSPORT_VER": "1",
            "TOR_PT_CLIENT_TRANSPORTS": "meek",
        }

        # @TODO detect the port from the subprocess output
        meek_address = "127.0.0.1"
        meek_port = "43533"  # hardcoded for testing
        self.meek_proxies = {
            "http": f"socks5h://{meek_address}:{meek_port}",
            "https": f"socks5h://{meek_address}:{meek_port}",
        }

        # Start the Meek Client as a subprocess.
        # This will be used to do domain fronting to the Tor
        # Moat API endpoints for censorship circumvention as
        # well as BridgeDB lookups.

        if self.common.platform == "Windows":
            # In Windows, hide console window when opening tor.exe subprocess
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            self.meek_proc = subprocess.Popen(
                [self.meek_client_file_path, "--url", meek_url, "--front", meek_front],
                stdout=subprocess.PIPE,
                startupinfo=startupinfo,
                bufsize=1,
                env=meek_env,
                text=True,
            )
        else:
            self.meek_proc = subprocess.Popen(
                [self.meek_client_file_path, "--url", meek_url, "--front", meek_front],
                stdout=subprocess.PIPE,
                bufsize=1,
                env=meek_env,
                text=True,
            )

            # if "CMETHOD meek socks5" in line:
            #    self.meek_host = (line.split(" ")[3].split(":")[0])
            #    self.meek_port = (line.split(" ")[3].split(":")[1])
            #    self.common.log("CensorshipCircumvention", "__init__", f"Meek host is {self.meek_host}")
            #    self.common.log("CensorshipCircumvention", "__init__", f"Meek port is {self.meek_port}")

    def censorship_obtain_map(self, country=False):
        """
        Retrieves the Circumvention map from Tor Project and store it
        locally for further look-ups if required.

        Optionally pass a country code in order to get recommended settings
        just for that country.

        Note that this API endpoint doesn't return actual bridges,
        it just returns the recommended bridge type countries.
        """
        endpoint = "https://bridges.torproject.org/moat/circumvention/map"
        data = {}
        if country:
            data = {"country": country}

        r = requests.post(
            endpoint,
            json=data,
            headers={"Content-Type": "application/vnd.api+json"},
            proxies=self.meek_proxies,
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

    def censorship_obtain_settings(self, country=False, transports=False):
        """
        Retrieves the Circumvention Settings from Tor Project, which
        will return recommended settings based on the country code of
        the requesting IP.

        Optionally, a country code can be specified in order to override
        the IP detection.

        Optionally, a list of transports can be specified in order to
        return recommended settings for just that transport type.
        """
        endpoint = "https://bridges.torproject.org/moat/circumvention/settings"
        data = {}
        if country:
            data = {"country": country}
        if transports:
            data.append({"transports": transports})
        r = requests.post(
            endpoint,
            json=data,
            headers={"Content-Type": "application/vnd.api+json"},
            proxies=self.meek_proxies,
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

    def censorship_obtain_builtin_bridges(self):
        """
        Retrieves the list of built-in bridges from the Tor Project.
        """
        endpoint = "https://bridges.torproject.org/moat/circumvention/builtin"
        r = requests.post(
            endpoint,
            headers={"Content-Type": "application/vnd.api+json"},
            proxies=self.meek_proxies,
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
