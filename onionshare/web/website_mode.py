import os
import sys
import tempfile
import mimetypes
from flask import Response, request, render_template, make_response, send_from_directory

from .base_mode import BaseModeWeb
from .. import strings


class WebsiteModeWeb(BaseModeWeb):
    """
    All of the web logic for website mode
    """
    def init(self):
        self.common.log('WebsiteModeWeb', '__init__')
        self.define_routes()


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
                        return self.directory_listing(path, filenames, filesystem_path)

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
                        return self.directory_listing(path, filenames)

                else:
                    # If the path isn't found, throw a 404
                    return self.web.error404()

    def build_directory_listing(self, filenames):
        for filename in filenames:
            if filesystem_path:
                this_filesystem_path = os.path.join(filesystem_path, filename)
            else:
                this_filesystem_path = self.files[filename]

            is_dir = os.path.isdir(this_filesystem_path)

            if is_dir:
                dirs.append({
                    'basename': filename
                })
            else:
                size = os.path.getsize(this_filesystem_path)
                size_human = self.common.human_readable_filesize(size)
                files.append({
                    'basename': filename,
                    'size_human': size_human
                })
        return files, dirs


    def build_file_list(self, filenames):
        """
        Build a data structure that describes the list of files that make up
        the static website.
        """
        self.common.log("WebsiteModeWeb", "build_file_list")

        # Loop through the files
        for filename in filenames:
            basename = os.path.basename(filename.rstrip('/'))

            # If it's a filename, add it
            if os.path.isfile(filename):
                self.files[basename] = filename
                self.root_files[basename] = filename

            # If it's a directory, add it recursively
            elif os.path.isdir(filename):
                self.root_files[basename + '/'] = filename

                for root, _, nested_filenames in os.walk(filename):
                    # Normalize the root path. So if the directory name is "/home/user/Documents/some_folder",
                    # and it has a nested folder foobar, the root is "/home/user/Documents/some_folder/foobar".
                    # The normalized_root should be "some_folder/foobar"
                    normalized_root = os.path.join(basename, root[len(filename):].lstrip('/')).rstrip('/')

                    # Add the dir itself
                    self.files[normalized_root + '/'] = root

                    # Add the files in this dir
                    for nested_filename in nested_filenames:
                        self.files[os.path.join(normalized_root, nested_filename)] = os.path.join(root, nested_filename)

        return True
