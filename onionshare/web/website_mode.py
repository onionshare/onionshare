import os
import sys
import tempfile
import mimetypes
from flask import Response, request, render_template, make_response, url_for, redirect

from .. import strings

class ShareModeWebsite(object):
    """
    All of the web logic for website share mode
    """
    def __init__(self, common, web):
        self.common = common
        self.common.log('ShareModeWebsite', '__init__')

        self.web = web
        self.download_filesize = None

        # Information about the files to be shared
        self.file_info = []
        self.connection_count = 0

        self.define_routes()

    def define_routes(self):
        """
        The web app routes for sharing files
        """
        @self.web.app.route("/<slug_candidate>")
        def index(slug_candidate):
            self.web.check_slug_candidate(slug_candidate)
            return path_logic(slug_candidate)

        @self.web.app.route('/<path:page_path>')
        def path_public(page_path):
            if self.common.settings.get('public_mode'):
                return path_logic('', page_path)
            elif self.web.slug:
                return redirect(self.web.slug + '/' + page_path)
            else:
                return self.web.error404()

        @self.web.app.route("/")
        def index_public():
            if not self.common.settings.get('public_mode'):
                return self.web.error404()
            return path_logic()

        @self.web.app.route('/<slug_candidate>/<path:page_path>')
        def static_page(slug_candidate, page_path):
            self.web.check_slug_candidate(slug_candidate)
            return path_logic(slug_candidate, page_path)

        def path_logic(slug_candidate='', page_path=''):
            """
            Render the onionshare website.
            """
            self.web.add_request(self.web.REQUEST_LOAD, request.path)

            if self.file_info['files']:
                website_folder = os.path.dirname(self.file_info['files'][0]['filename'])
                self.web.app.static_url_path = website_folder
                self.web.app.static_folder = website_folder
                if self.file_info['dirs']:
                    for item in self.file_info['dirs']:
                        if item['basename'] == 'static' or item['basename'] == 'assets':
                            self.web.app.static_url_path = item['filename']
                            self.web.app.static_folder = item['filename']
                            break
            elif self.file_info['dirs']:
                website_folder = self.file_info['dirs'][0]['filename']
                self.web.app.static_url_path = website_folder
                self.web.app.static_folder = website_folder
                self.web.app.static_url_path = website_folder + '/static'
                self.web.app.static_folder = website_folder + '/static'
            else:
                return self.web.error404()

            page = website_folder
            location = request.path

            if page_path:
                page += '/' + page_path + '/index.html'
            else:
                page += '/index.html'

            f = open(page, 'r')
            page_html = f.read()

            if self.web.slug:
                r = make_response(render_template(
                    'static.html',
                    html=page_html))
                r.headers['location'] = location
                r.autocorrect_location_header = False
            else:
                r = make_response(render_template(
                    'static.html',
                    html=page_html))
                r.headers['location'] = location
                r.autocorrect_location_header = False

            # Each connection has a unique id
            connection_id = self.connection_count
            self.connection_count += 1

            self.update_connections_count(request.path, connection_id)

            return self.web.add_security_headers(r)

    def update_connections_count(self, path, connection_id):
        # Tell GUI there is a new connection
        self.web.add_request(self.web.REQUEST_STARTED, path, {
            'id': connection_id
        })

    def set_file_info(self, filenames, processed_size_callback=None):
        """
        Using the list of filenames being shared, fill in details that the web
        page will need to display. This includes zipping up the file in order to
        get the zip file's name and size.
        """
        self.common.log("ShareModeWebsite", "set_file_info")
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
        self.file_info['files'] = sorted(self.file_info['files'], key=lambda k: k['basename'])
        self.file_info['dirs'] = sorted(self.file_info['dirs'], key=lambda k: k['basename'])

        return True
