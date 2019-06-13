import os
import sys
import tempfile
import mimetypes
from flask import Response, request, render_template, make_response

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


    def directory_listing(self, path, filenames, filesystem_path=None):
        # If filesystem_path is None, this is the root directory listing
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

        r = make_response(render_template('listing.html',
            path=path,
            files=files,
            dirs=dirs,
            static_url_path=self.web.static_url_path))
        return self.web.add_security_headers(r)


    def set_file_info(self, filenames, processed_size_callback=None):
        """
        Build a data structure that describes the list of files
        """
        if self.web.mode == 'website':
            self.common.log("WebsiteModeWeb", "set_file_info")
            self.web.cancel_compression = True

            # This is only the root files and dirs, as opposed to all of them
            self.root_files = {}

            # If there's just one folder, replace filenames with a list of files inside that folder
            if len(filenames) == 1 and os.path.isdir(filenames[0]):
                filenames = [os.path.join(filenames[0], x) for x in os.listdir(filenames[0])]

            self.build_file_list(filenames)

        elif self.web.mode == 'share':
            self.common.log("ShareModeWeb", "set_file_info")
            self.web.cancel_compression = False
            self.build_zipfile_list(filenames, processed_size_callback)

        return True
