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
        
        self.visit_count = 0
        self.download_count = 0

        # If "Stop After First Download" is checked (stay_open == False), only allow
        # one download at a time.
        self.download_in_progress = False

        # Reset assets path
        self.web.app.static_folder=self.common.get_resource_path('static')


    def init(self):
        """
        Add custom initialization here.
        """
        pass
