import os
import sys
import tempfile
import mimetypes
from flask import Response, request, render_template, make_response, send_from_directory

from .send_base_mode import SendBaseModeWeb
from .. import strings


class WebsiteModeWeb(SendBaseModeWeb):
    """
    All of the web logic for website mode
    """
    def define_routes(self):
        """
        The web app routes for sharing a website
        """
        @self.web.app.route('/', defaults={'path': ''})
        @self.web.app.route('/<path:path>')
        def path_public(path):
            return path_logic(path)

        def path_logic(path=''):
            """
            Render the onionshare website.
            """

            # Each download has a unique id
            visit_id = self.visit_count
            self.visit_count += 1

            # Tell GUI the page has been visited
            self.web.add_request(self.web.REQUEST_STARTED, path, {
                'id': visit_id,
                'action': 'visit'
            })

            return self.render_logic(path)

    def directory_listing_template(self, path, files, dirs):
        return make_response(render_template('listing.html',
            path=path,
            files=files,
            dirs=dirs,
            static_url_path=self.web.static_url_path))

    def set_file_info_custom(self, filenames, processed_size_callback):
        self.common.log("WebsiteModeWeb", "set_file_info_custom")
        self.web.cancel_compression = True

    def render_logic(self, path=''):
        if path in self.files:
            filesystem_path = self.files[path]

            # If it's a directory
            if os.path.isdir(filesystem_path):
                # Is there an index.html?
                index_path = os.path.join(path, 'index.html')
                if index_path in self.files:
                    # Render it
                    dirname = os.path.dirname(self.files[index_path])
                    basename = os.path.basename(self.files[index_path])

                    return send_from_directory(dirname, basename)

                else:
                    # Otherwise, render directory listing
                    filenames = []
                    for filename in os.listdir(filesystem_path):
                        if os.path.isdir(os.path.join(filesystem_path, filename)):
                            filenames.append(filename + '/')
                        else:
                            filenames.append(filename)
                    filenames.sort()
                    return self.directory_listing(filenames, path, filesystem_path)

            # If it's a file
            elif os.path.isfile(filesystem_path):
                dirname = os.path.dirname(filesystem_path)
                basename = os.path.basename(filesystem_path)
                return send_from_directory(dirname, basename)

            # If it's not a directory or file, throw a 404
            else:
                return self.web.error404()
        else:
            # Special case loading /

            if path == '':
                index_path = 'index.html'
                if index_path in self.files:
                    # Render it
                    dirname = os.path.dirname(self.files[index_path])
                    basename = os.path.basename(self.files[index_path])
                    return send_from_directory(dirname, basename)
                else:
                    # Root directory listing
                    filenames = list(self.root_files)
                    filenames.sort()
                    return self.directory_listing(filenames, path)

            else:
                # If the path isn't found, throw a 404
                return self.web.error404()
