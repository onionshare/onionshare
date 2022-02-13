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

import os
import requests


class UpdateTorBridges:
    """
    Update the built-in Tor Bridges in OnionShare's torrc templates.
    """

    def __init__(self, root_path):
        self.root_path = root_path
        torrc_template_dir = os.path.join(
            self.root_path, os.pardir, "cli/onionshare_cli/resources"
        )
        endpoint = "https://bridges.torproject.org/moat/circumvention/builtin"
        r = requests.post(
            endpoint,
            headers={"Content-Type": "application/vnd.api+json"},
        )
        if r.status_code != 200:
            print(
                f"There was a problem fetching the latest built-in bridges: status_code={r.status_code}"
            )
            return False

        result = r.json()

        if "errors" in result:
            print(
                f"There was a problem fetching the latest built-in bridges: errors={result['errors']}"
            )
            return False

        for bridge_type in ["meek", "obfs4", "snowflake"]:
            if result[bridge_type]:
                if bridge_type == "meek":
                    torrc_template_extension = "meek_lite_azure"
                else:
                    torrc_template_extension = bridge_type
                torrc_template = os.path.join(
                    self.root_path,
                    torrc_template_dir,
                    f"torrc_template-{torrc_template_extension}",
                )

                with open(torrc_template, "w") as f:
                    f.write(f"# Enable built-in {bridge_type} bridge\n")
                    bridges = result[bridge_type]
                    # Sorts the bridges numerically by IP, since they come back in
                    # random order from the API each time, and create noisy git diff.
                    bridges.sort(key=lambda s: s.split()[1])
                    for item in bridges:
                        if bridge_type == "meek":
                            # obfs4proxy expects the bridge type to be meek_lite, and the url/front params
                            # are missing in the Tor API response, so we have to add them in ourselves.
                            bridge = item.replace("meek", "meek_lite")
                            f.write(
                                f"Bridge {bridge} url=https://meek.azureedge.net/ front=ajax.aspnetcdn.com\n"
                            )
                        else:
                            f.write(f"Bridge {item}\n")
