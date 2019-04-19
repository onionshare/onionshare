import os
import sys
import tempfile
import mimetypes
from flask import Response, request, render_template, make_response, send_from_directory
from flask_httpauth import HTTPBasicAuth

from .. import strings


class WebsiteModeWeb(object):
    """
    All of the web logic for share mode
    """
    def __init__(self, common, web):
        self.common = common
        self.common.log('WebsiteModeWeb', '__init__')

        self.web = web
        self.auth = HTTPBasicAuth()

        # Information about the file to be shared
        self.file_info = []
        self.website_folder = ''
        self.download_filesize = 0
        self.visit_count = 0

        self.users = { }

        self.define_routes()

    def define_routes(self):
        """
        The web app routes for sharing a website
        """

        @self.auth.get_password
        def get_pw(username):
            self.users['onionshare'] = self.web.slug

            if self.common.settings.get('public_mode'):
                return True  # let the request through, no questions asked!
            elif username in self.users:
                return self.users.get(username)
            else:
                return None

        @self.web.app.route('/download/<path:page_path>')
        @self.auth.login_required
        def path_download(page_path):
            return path_download(page_path)

        @self.web.app.route('/<path:page_path>')
        @self.auth.login_required
        def path_public(page_path):
            return path_logic(page_path)

        @self.web.app.route("/")
        @self.auth.login_required
        def index_public():
            return path_logic('')

        def path_download(file_path=''):
            """
            Render the download links.
            """
            self.web.add_request(self.web.REQUEST_LOAD, request.path)
            if not os.path.isfile(os.path.join(self.website_folder, file_path)):
                return self.web.error404()

            return send_from_directory(self.website_folder, file_path)

        def path_logic(page_path=''):
            """
            Render the onionshare website.
            """

            self.web.add_request(self.web.REQUEST_LOAD, request.path)

            if self.file_info['files']:
                self.website_folder = os.path.dirname(self.file_info['files'][0]['filename'])
            elif self.file_info['dirs']:
                self.website_folder = self.file_info['dirs'][0]['filename']
            else:
                return self.web.error404()

            if any((fname == 'index.html') for fname in os.listdir(self.website_folder)):
                self.web.app.static_url_path = self.website_folder
                self.web.app.static_folder = self.website_folder
                if not os.path.isfile(os.path.join(self.website_folder, page_path)):
                    page_path = os.path.join(page_path, 'index.html')

                return send_from_directory(self.website_folder, page_path)

            elif any(os.path.isfile(os.path.join(self.website_folder, i)) for i in os.listdir(self.website_folder)):
                filenames = []
                for i in os.listdir(self.website_folder):
                    filenames.append(os.path.join(self.website_folder, i))

                self.set_file_info(filenames)

                r = make_response(render_template(
                    'listing.html',
                    file_info=self.file_info,
                    filesize=self.download_filesize,
                    filesize_human=self.common.human_readable_filesize(self.download_filesize)))

                return self.web.add_security_headers(r)

            else:
                return self.web.error404()


    def set_file_info(self, filenames, processed_size_callback=None):
        """
        Using the list of filenames being shared, fill in details that the web
        page will need to display. This includes zipping up the file in order to
        get the zip file's name and size.
        """
        self.common.log("WebsiteModeWeb", "set_file_info")
        self.web.cancel_compression = True

        self.cleanup_filenames = []

        # build file info list
        self.file_info = {'files': [], 'dirs': []}
        for filename in filenames:
            info = {
                'filename': filename,
                'basename': os.path.basename(filename.rstrip('/'))
            }
            if os.path.isfile(filename):
                info['size'] = os.path.getsize(filename)
                info['size_human'] = self.common.human_readable_filesize(info['size'])
                self.file_info['files'].append(info)
            if os.path.isdir(filename):
                info['size'] = self.common.dir_size(filename)
                info['size_human'] = self.common.human_readable_filesize(info['size'])
                self.file_info['dirs'].append(info)

            self.download_filesize += info['size']

        self.file_info['files'] = sorted(self.file_info['files'], key=lambda k: k['basename'])
        self.file_info['dirs'] = sorted(self.file_info['dirs'], key=lambda k: k['basename'])

        # Check if there's only 1 file and no folders
        if len(self.file_info['files']) == 1 and len(self.file_info['dirs']) == 0:
            self.download_filename = self.file_info['files'][0]['filename']
            self.download_filesize = self.file_info['files'][0]['size']

            self.download_filesize = os.path.getsize(self.download_filename)


        return True
