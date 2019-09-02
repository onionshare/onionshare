import os
import sys
import tempfile
import mimetypes
from flask import Response, request, render_template, make_response

from .. import strings


class SendBaseModeWeb:
    """
    All of the web logic shared between share and website mode (modes where the user sends files)
    """
    def __init__(self, common, web):
        super(SendBaseModeWeb, self).__init__()
        self.common = common
        self.web = web

        # Information about the file to be shared
        self.file_info = []
        self.is_zipped = False
        self.download_filename = None
        self.download_filesize = None
        self.gzip_filename = None
        self.gzip_filesize = None
        self.zip_writer = None

        # Dictionary mapping file paths to filenames on disk
        self.files = {}
        # This is only the root files and dirs, as opposed to all of them
        self.root_files = {}

        self.cleanup_filenames = []
        self.file_info = {'files': [], 'dirs': []}

        self.visit_count = 0
        self.download_count = 0

        # If "Stop After First Download" is checked (stay_open == False), only allow
        # one download at a time.
        self.download_in_progress = False

        self.define_routes()

    def init(self):
        self.common.log('SendBaseModeWeb', '__init__')
        self.define_routes()

    def define_routes(self):
        """
        Inherited class will implement this
        """
        pass

    def directory_listing_template(self):
        """
        Inherited class will implement this. It should call render_template and return
        the response.
        """
        pass

    def directory_listing(self, filenames, path='', filesystem_path=None):
        # If filesystem_path is None, this is the root directory listing
        files, dirs = self.build_directory_listing(filenames, filesystem_path)
        r = self.directory_listing_template(path, files, dirs)
        return self.web.add_security_headers(r)

    def build_directory_listing(self, filenames, filesystem_path):
        files = []
        dirs = []

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

    def set_file_info_custom(self, filenames, processed_size_callback):
        """
        Inherited class will implement this.
        """
        pass

    def set_file_info(self, filenames, processed_size_callback=None):
        """
        Build a data structure that describes the list of files
        """

        # If there's just one folder, replace filenames with a list of files inside that folder
        if len(filenames) == 1 and os.path.isdir(filenames[0]):
            filenames = [os.path.join(filenames[0], x) for x in os.listdir(filenames[0])]

        self.build_file_list(filenames)
        self.set_file_info_custom(filenames, processed_size_callback)

    def build_file_list(self, filenames):
        """
        Build a data structure that describes the list of files that make up
        the static website.
        """
        self.common.log("BaseModeWeb", "build_file_list")

        # Clear the list of files
        self.files = {}
        self.root_files = {}

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

    def render_logic(self, path=''):
        """
        Inherited class will implement this.
        """
        pass
