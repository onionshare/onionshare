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

import os
import sys
import tempfile
import mimetypes
from flask import Response, request, render_template, make_response

from .send_base_mode import SendBaseModeWeb


class WebsiteModeWeb(SendBaseModeWeb):
    """
    All of the web logic for website mode
    """

    def init(self):
        pass

    def define_routes(self):
        """
        The web app routes for sharing a website
        """

        @self.web.app.route("/", defaults={"path": ""})
        @self.web.app.route("/<path:path>")
        def path_public(path):
            return path_logic(path)

        def path_logic(path=""):
            """
            Render the onionshare website.
            """
            return self.render_logic(path)

    def directory_listing_template(
        self, path, files, dirs, breadcrumbs, breadcrumbs_leaf
    ):
        return make_response(
            render_template(
                "listing.html",
                path=path,
                files=files,
                dirs=dirs,
                breadcrumbs=breadcrumbs,
                breadcrumbs_leaf=breadcrumbs_leaf,
                static_url_path=self.web.static_url_path,
            )
        )

    def set_file_info_custom(self, filenames, processed_size_callback):
        self.common.log("WebsiteModeWeb", "set_file_info_custom")
        self.web.cancel_compression = True

    def render_logic(self, path=""):
        # Strip trailing slash
        path = path.rstrip("/")

        if path in self.files:
            filesystem_path = self.files[path]

            # If it's a directory
            if os.path.isdir(filesystem_path):
                # Is there an index.html?
                index_path = os.path.join(path, "index.html")
                if index_path in self.files:
                    # Render it
                    return self.stream_individual_file(self.files[index_path])

                else:
                    # Otherwise, render directory listing
                    filenames = []
                    for filename in os.listdir(filesystem_path):
                        filenames.append(filename)
                    filenames.sort()
                    return self.directory_listing(filenames, path, filesystem_path)

            # If it's a file
            elif os.path.isfile(filesystem_path):
                return self.stream_individual_file(filesystem_path)

            # If it's not a directory or file, throw a 404
            else:
                history_id = self.cur_history_id
                self.cur_history_id += 1
                return self.web.error404(history_id)
        else:
            # Special case loading /

            if path == "":
                index_path = "index.html"
                if index_path in self.files:
                    # Render it
                    return self.stream_individual_file(self.files[index_path])
                else:
                    # Root directory listing
                    filenames = list(self.root_files)
                    filenames.sort()
                    return self.directory_listing(filenames, path)

            else:
                # If the path isn't found, throw a 404
                history_id = self.cur_history_id
                self.cur_history_id += 1
                return self.web.error404(history_id)
