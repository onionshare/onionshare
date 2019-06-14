import os
import sys
import tempfile
import mimetypes
from flask import Response, request, render_template, make_response, send_from_directory

from .. import strings

class BaseModeWeb(object):
    """
    All of the web logic shared between share and website mode
    """
    def __init__(self, common, web):
        super(BaseModeWeb, self).__init__()
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
        """
        Add custom initialization here.
        """
        pass


    def directory_listing(self, filenames, path='', filesystem_path=None):
        # If filesystem_path is None, this is the root directory listing
        files = []
        dirs = []
        r = ''

        files, dirs = self.build_directory_listing(filenames, filesystem_path)

        if self.web.mode == 'website':
            r = make_response(render_template('listing.html',
                path=path,
                files=files,
                dirs=dirs,
                static_url_path=self.web.static_url_path))

        elif self.web.mode == 'share':
            r = make_response(render_template(
                'send.html',
                file_info=self.file_info,
                files=files,
                dirs=dirs,
                filename=os.path.basename(self.download_filename),
                filesize=self.filesize,
                filesize_human=self.common.human_readable_filesize(self.download_filesize),
                is_zipped=self.is_zipped,
                static_url_path=self.web.static_url_path))

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


    def set_file_info(self, filenames, processed_size_callback=None):
        """
        Build a data structure that describes the list of files
        """

        # If there's just one folder, replace filenames with a list of files inside that folder
        if len(filenames) == 1 and os.path.isdir(filenames[0]):
            filenames = [os.path.join(filenames[0], x) for x in os.listdir(filenames[0])]

        self.build_file_list(filenames)

        if self.web.mode == 'share':
            self.common.log("ShareModeWeb", "set_file_info")
            self.web.cancel_compression = False
            self.build_zipfile_list(filenames, processed_size_callback)

        elif self.web.mode == 'website':
            self.common.log("WebsiteModeWeb", "set_file_info")
            self.web.cancel_compression = True

        return True


    def build_file_list(self, filenames):
        """
        Build a data structure that describes the list of files that make up
        the static website.
        """
        self.common.log("BaseModeWeb", "build_file_list")

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
        if path in self.files:
            filesystem_path = self.files[path]

            # If it's a directory
            if os.path.isdir(filesystem_path):
                # Is there an index.html?
                index_path = os.path.join(path, 'index.html')
                if self.web.mode == 'website' and index_path in self.files:
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
                if self.web.mode == 'website' and index_path in self.files:
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
