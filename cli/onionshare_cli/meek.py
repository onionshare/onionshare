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
import subprocess
from queue import Queue, Empty
from threading import Thread


class Meek(object):
    """
    The Meek object starts the meek-client as a subprocess.
    This process is used to do domain-fronting to connect to
    the Tor APIs for censorship circumvention and retrieving
    bridges, before connecting to Tor.
    """

    def __init__(self, common):
        """
        Set up the Meek object
        """

        self.common = common
        self.common.log("Meek", "__init__")

        get_tor_paths = self.common.get_tor_paths
        (
            self.tor_path,
            self.tor_geo_ip_file_path,
            self.tor_geo_ipv6_file_path,
            self.obfs4proxy_file_path,
            self.snowflake_file_path,
            self.meek_client_file_path,
        ) = get_tor_paths()

        self.meek_proxies = {}
        self.meek_url = "https://moat.torproject.org.global.prod.fastly.net/"
        self.meek_front = "cdn.sstatic.net"
        self.meek_env = {
            "TOR_PT_MANAGED_TRANSPORT_VER": "1",
            "TOR_PT_CLIENT_TRANSPORTS": "meek",
        }
        self.meek_host = "127.0.0.1"
        self.meek_port = None

    def start(self):
        """
        Start the Meek Client and populate the SOCKS proxies dict
        for use with requests to the Tor Moat API.
        """
        # Small method to read stdout from the subprocess.
        # We use this to obtain the random port that Meek
        # started on
        def enqueue_output(out, queue):
            for line in iter(out.readline, b""):
                queue.put(line)
            out.close()

        # Start the Meek Client as a subprocess.

        if self.common.platform == "Windows":
            # In Windows, hide console window when opening meek-client.exe subprocess
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            self.meek_proc = subprocess.Popen(
                [
                    self.meek_client_file_path,
                    "--url",
                    self.meek_url,
                    "--front",
                    self.meek_front,
                ],
                stdout=subprocess.PIPE,
                startupinfo=startupinfo,
                bufsize=1,
                env=self.meek_env,
                text=True,
            )
        else:
            self.meek_proc = subprocess.Popen(
                [
                    self.meek_client_file_path,
                    "--url",
                    self.meek_url,
                    "--front",
                    self.meek_front,
                ],
                stdout=subprocess.PIPE,
                bufsize=1,
                env=self.meek_env,
                text=True,
            )

        # Queue up the stdout from the subprocess for polling later
        q = Queue()
        t = Thread(target=enqueue_output, args=(self.meek_proc.stdout, q))
        t.daemon = True  # thread dies with the program
        t.start()

        while True:
            # read stdout without blocking
            try:
                line = q.get_nowait()
            except Empty:
                # no stdout yet?
                pass
            else:  # we got stdout
                if "CMETHOD meek socks5" in line:
                    self.meek_host = line.split(" ")[3].split(":")[0]
                    self.meek_port = line.split(" ")[3].split(":")[1]
                    self.common.log("Meek", "start", f"Meek host is {self.meek_host}")
                    self.common.log("Meek", "start", f"Meek port is {self.meek_port}")
                    break

        if self.meek_port:
            self.meek_proxies = {
                "http": f"socks5h://{self.meek_host}:{self.meek_port}",
                "https": f"socks5h://{self.meek_host}:{self.meek_port}",
            }
        else:
            self.common.log("Meek", "start", "Could not obtain the meek port")
            raise MeekNotRunning()


class MeekNotRunning(Exception):
    """
    We were unable to start Meek or obtain the port
    number it started on, in order to do domain fronting.
    """
