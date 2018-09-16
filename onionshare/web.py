# -*- coding: utf-8 -*-
"""
OnionShare | https://onionshare.org/

Copyright (C) 2018 Micah Lee <micah@micahflee.com>

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

import hmac
import logging
import mimetypes
import os
import queue
import socket
import sys
import tempfile
import zipfile
import re
import io
from distutils.version import LooseVersion as Version
from urllib.request import urlopen

import flask
from flask import (
    Flask, Response, Request, request, render_template, abort, make_response,
    flash, redirect, __version__ as flask_version
)
from werkzeug.utils import secure_filename

from . import strings, common


# Stub out flask's show_server_banner function, to avoiding showing warnings that
# are not applicable to OnionShare
def stubbed_show_server_banner(env, debug, app_import_path, eager_loading):
    pass

flask.cli.show_server_banner = stubbed_show_server_banner


class Web(object):
    """
    The Web object is the OnionShare web server, powered by flask
    """
    def __init__(self, common, stay_open, gui_mode, receive_mode=False):
        self.common = common

        # The flask app
        self.app = Flask(__name__,
                         static_folder=common.get_resource_path('static'),
                         template_folder=common.get_resource_path('templates'))
        self.app.secret_key = self.common.random_string(8)

        # Debug mode?
        if self.common.debug:
            self.debug_mode()

        # Stay open after the first download?
        self.stay_open = stay_open

        # Are we running in GUI mode?
        self.gui_mode = gui_mode

        # Are we using receive mode?
        self.receive_mode = receive_mode
        if self.receive_mode:
            # Use custom WSGI middleware, to modify environ
            self.app.wsgi_app = ReceiveModeWSGIMiddleware(self.app.wsgi_app, self)
            # Use a custom Request class to track upload progess
            self.app.request_class = ReceiveModeRequest

        # Starting in Flask 0.11, render_template_string autoescapes template variables
        # by default. To prevent content injection through template variables in
        # earlier versions of Flask, we force autoescaping in the Jinja2 template
        # engine if we detect a Flask version with insecure default behavior.
        if Version(flask_version) < Version('0.11'):
            # Monkey-patch in the fix from https://github.com/pallets/flask/commit/99c99c4c16b1327288fd76c44bc8635a1de452bc
            Flask.select_jinja_autoescape = self._safe_select_jinja_autoescape

        # Information about the file
        self.file_info = []
        self.zip_filename = None
        self.zip_filesize = None

        self.security_headers = [
            ('Content-Security-Policy', 'default-src \'self\'; style-src \'self\'; script-src \'self\'; img-src \'self\' data:;'),
            ('X-Frame-Options', 'DENY'),
            ('X-Xss-Protection', '1; mode=block'),
            ('X-Content-Type-Options', 'nosniff'),
            ('Referrer-Policy', 'no-referrer'),
            ('Server', 'OnionShare')
        ]

        self.REQUEST_LOAD = 0
        self.REQUEST_DOWNLOAD = 1
        self.REQUEST_PROGRESS = 2
        self.REQUEST_OTHER = 3
        self.REQUEST_CANCELED = 4
        self.REQUEST_RATE_LIMIT = 5
        self.q = queue.Queue()

        self.slug = None

        self.download_count = 0
        self.error404_count = 0

        # If "Stop After First Download" is checked (stay_open == False), only allow
        # one download at a time.
        self.download_in_progress = False

        self.done = False

        # If the client closes the OnionShare window while a download is in progress,
        # it should immediately stop serving the file. The client_cancel global is
        # used to tell the download function that the client is canceling the download.
        self.client_cancel = False

        # shutting down the server only works within the context of flask, so the easiest way to do it is over http
        self.shutdown_slug = self.common.random_string(16)

        # Define the ewb app routes
        self.common_routes()
        if self.receive_mode:
            self.receive_routes()
        else:
            self.send_routes()

    def send_routes(self):
        """
        The web app routes for sharing files
        """
        @self.app.route("/<slug_candidate>")
        def index(slug_candidate):
            """
            Render the template for the onionshare landing page.
            """
            self.check_slug_candidate(slug_candidate)

            self.add_request(self.REQUEST_LOAD, request.path)

            # Deny new downloads if "Stop After First Download" is checked and there is
            # currently a download
            deny_download = not self.stay_open and self.download_in_progress
            if deny_download:
                r = make_response(render_template('denied.html'))
                return self.add_security_headers(r)

            # If download is allowed to continue, serve download page
            r = make_response(render_template(
                'send.html',
                slug=self.slug,
                file_info=self.file_info,
                filename=os.path.basename(self.zip_filename),
                filesize=self.zip_filesize,
                filesize_human=self.common.human_readable_filesize(self.zip_filesize)))
            return self.add_security_headers(r)

        @self.app.route("/<slug_candidate>/download")
        def download(slug_candidate):
            """
            Download the zip file.
            """
            self.check_slug_candidate(slug_candidate)

            # Deny new downloads if "Stop After First Download" is checked and there is
            # currently a download
            deny_download = not self.stay_open and self.download_in_progress
            if deny_download:
                r = make_response(render_template('denied.html'))
                return self.add_security_headers(r)

            # each download has a unique id
            download_id = self.download_count
            self.download_count += 1

            # prepare some variables to use inside generate() function below
            # which is outside of the request context
            shutdown_func = request.environ.get('werkzeug.server.shutdown')
            path = request.path

            # tell GUI the download started
            self.add_request(self.REQUEST_DOWNLOAD, path, {'id': download_id})

            dirname = os.path.dirname(self.zip_filename)
            basename = os.path.basename(self.zip_filename)

            def generate():
                # The user hasn't canceled the download
                self.client_cancel = False

                # Starting a new download
                if not self.stay_open:
                    self.download_in_progress = True

                chunk_size = 102400  # 100kb

                fp = open(self.zip_filename, 'rb')
                self.done = False
                canceled = False
                while not self.done:
                    # The user has canceled the download, so stop serving the file
                    if self.client_cancel:
                        self.add_request(self.REQUEST_CANCELED, path, {'id': download_id})
                        break

                    chunk = fp.read(chunk_size)
                    if chunk == b'':
                        self.done = True
                    else:
                        try:
                            yield chunk

                            # tell GUI the progress
                            downloaded_bytes = fp.tell()
                            percent = (1.0 * downloaded_bytes / self.zip_filesize) * 100

                            # only output to stdout if running onionshare in CLI mode, or if using Linux (#203, #304)
                            if not self.gui_mode or self.common.platform == 'Linux' or self.common.platform == 'BSD':
                                sys.stdout.write(
                                    "\r{0:s}, {1:.2f}%          ".format(self.common.human_readable_filesize(downloaded_bytes), percent))
                                sys.stdout.flush()

                            self.add_request(self.REQUEST_PROGRESS, path, {'id': download_id, 'bytes': downloaded_bytes})
                            self.done = False
                        except:
                            # looks like the download was canceled
                            self.done = True
                            canceled = True

                            # tell the GUI the download has canceled
                            self.add_request(self.REQUEST_CANCELED, path, {'id': download_id})

                fp.close()

                if self.common.platform != 'Darwin':
                    sys.stdout.write("\n")

                # Download is finished
                if not self.stay_open:
                    self.download_in_progress = False

                # Close the server, if necessary
                if not self.stay_open and not canceled:
                    print(strings._("closing_automatically"))
                    if shutdown_func is None:
                        raise RuntimeError('Not running with the Werkzeug Server')
                    shutdown_func()

            r = Response(generate())
            r.headers.set('Content-Length', self.zip_filesize)
            r.headers.set('Content-Disposition', 'attachment', filename=basename)
            r = self.add_security_headers(r)
            # guess content type
            (content_type, _) = mimetypes.guess_type(basename, strict=False)
            if content_type is not None:
                r.headers.set('Content-Type', content_type)
            return r

    def receive_routes(self):
        """
        The web app routes for sharing files
        """
        @self.app.route("/<slug_candidate>")
        def index(slug_candidate):
            self.check_slug_candidate(slug_candidate)

            r = make_response(render_template(
                'receive.html',
                slug=self.slug))
            return self.add_security_headers(r)

        @self.app.route("/<slug_candidate>/upload", methods=['POST'])
        def upload(slug_candidate):
            self.check_slug_candidate(slug_candidate)

            files = request.files.getlist('file[]')
            filenames = []
            for f in files:
                if f.filename != '':
                    # Automatically rename the file, if a file of the same name already exists
                    filename = secure_filename(f.filename)
                    filenames.append(filename)
                    local_path = os.path.join(self.common.settings.get('downloads_dir'), filename)
                    if os.path.exists(local_path):
                        if '.' in filename:
                            # Add "-i", e.g. change "foo.txt" to "foo-2.txt"
                            parts = filename.split('.')
                            name = parts[:-1]
                            ext = parts[-1]

                            i = 2
                            valid = False
                            while not valid:
                                new_filename = '{}-{}.{}'.format('.'.join(name), i, ext)
                                local_path = os.path.join(self.common.settings.get('downloads_dir'), new_filename)
                                if os.path.exists(local_path):
                                    i += 1
                                else:
                                    valid = True
                        else:
                            # If no extension, just add "-i", e.g. change "foo" to "foo-2"
                            i = 2
                            valid = False
                            while not valid:
                                new_filename = '{}-{}'.format(filename, i)
                                local_path = os.path.join(self.common.settings.get('downloads_dir'), new_filename)
                                if os.path.exists(local_path):
                                    i += 1
                                else:
                                    valid = True

                    self.common.log('Web', 'receive_routes', '/upload, uploaded {}, saving to {}'.format(f.filename, local_path))
                    print(strings._('receive_mode_received_file').format(local_path))
                    f.save(local_path)

            # Note that flash strings are on English, and not translated, on purpose,
            # to avoid leaking the locale of the OnionShare user
            if len(filenames) == 0:
                flash('No files uploaded')
            else:
                for filename in filenames:
                    flash('Uploaded {}'.format(filename))

            return redirect('/{}'.format(slug_candidate))

        @self.app.route("/<slug_candidate>/close", methods=['POST'])
        def close(slug_candidate):
            self.check_slug_candidate(slug_candidate)
            self.force_shutdown()
            r = make_response(render_template('closed.html'))
            return self.add_security_headers(r)

    def common_routes(self):
        """
        Common web app routes between sending and receiving
        """
        @self.app.errorhandler(404)
        def page_not_found(e):
            """
            404 error page.
            """
            self.add_request(self.REQUEST_OTHER, request.path)

            if request.path != '/favicon.ico':
                self.error404_count += 1
                if self.error404_count == 20:
                    self.add_request(self.REQUEST_RATE_LIMIT, request.path)
                    self.force_shutdown()
                    print(strings._('error_rate_limit'))

            r = make_response(render_template('404.html'), 404)
            return self.add_security_headers(r)

        @self.app.route("/<slug_candidate>/shutdown")
        def shutdown(slug_candidate):
            """
            Stop the flask web server, from the context of an http request.
            """
            self.check_slug_candidate(slug_candidate, self.shutdown_slug)
            self.force_shutdown()
            return ""

    def add_security_headers(self, r):
        """
        Add security headers to a request
        """
        for header, value in self.security_headers:
            r.headers.set(header, value)
        return r

    def set_file_info(self, filenames, processed_size_callback=None):
        """
        Using the list of filenames being shared, fill in details that the web
        page will need to display. This includes zipping up the file in order to
        get the zip file's name and size.
        """
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

        # zip up the files and folders
        z = ZipWriter(self.common, processed_size_callback=processed_size_callback)
        for info in self.file_info['files']:
            z.add_file(info['filename'])
        for info in self.file_info['dirs']:
            z.add_dir(info['filename'])
        z.close()
        self.zip_filename = z.zip_filename
        self.zip_filesize = os.path.getsize(self.zip_filename)

    def _safe_select_jinja_autoescape(self, filename):
        if filename is None:
            return True
        return filename.endswith(('.html', '.htm', '.xml', '.xhtml'))

    def add_request(self, request_type, path, data=None):
        """
        Add a request to the queue, to communicate with the GUI.
        """
        self.q.put({
            'type': request_type,
            'path': path,
            'data': data
        })

    def generate_slug(self, persistent_slug=''):
        if persistent_slug:
            self.slug = persistent_slug
        else:
            self.slug = self.common.build_slug()

    def debug_mode(self):
        """
        Turn on debugging mode, which will log flask errors to a debug file.
        """
        temp_dir = tempfile.gettempdir()
        log_handler = logging.FileHandler(
            os.path.join(temp_dir, 'onionshare_server.log'))
        log_handler.setLevel(logging.WARNING)
        self.app.logger.addHandler(log_handler)

    def check_slug_candidate(self, slug_candidate, slug_compare=None):
        if not slug_compare:
            slug_compare = self.slug
        if not hmac.compare_digest(slug_compare, slug_candidate):
            abort(404)

    def force_shutdown(self):
        """
        Stop the flask web server, from the context of the flask app.
        """
        # shutdown the flask service
        func = request.environ.get('werkzeug.server.shutdown')
        if func is None:
            raise RuntimeError('Not running with the Werkzeug Server')
        func()

    def start(self, port, stay_open=False, persistent_slug=''):
        """
        Start the flask web server.
        """
        self.generate_slug(persistent_slug)

        self.stay_open = stay_open

        # In Whonix, listen on 0.0.0.0 instead of 127.0.0.1 (#220)
        if os.path.exists('/usr/share/anon-ws-base-files/workstation'):
            host = '0.0.0.0'
        else:
            host = '127.0.0.1'

        self.app.run(host=host, port=port, threaded=True)

    def stop(self, port):
        """
        Stop the flask web server by loading /shutdown.
        """

        # If the user cancels the download, let the download function know to stop
        # serving the file
        self.client_cancel = True

        # to stop flask, load http://127.0.0.1:<port>/<shutdown_slug>/shutdown
        try:
            s = socket.socket()
            s.connect(('127.0.0.1', port))
            s.sendall('GET /{0:s}/shutdown HTTP/1.1\r\n\r\n'.format(self.shutdown_slug))
        except:
            try:
                urlopen('http://127.0.0.1:{0:d}/{1:s}/shutdown'.format(port, self.shutdown_slug)).read()
            except:
                pass


class ZipWriter(object):
    """
    ZipWriter accepts files and directories and compresses them into a zip file
    with. If a zip_filename is not passed in, it will use the default onionshare
    filename.
    """
    def __init__(self, common, zip_filename=None, processed_size_callback=None):
        self.common = common

        if zip_filename:
            self.zip_filename = zip_filename
        else:
            self.zip_filename = '{0:s}/onionshare_{1:s}.zip'.format(tempfile.mkdtemp(), self.common.random_string(4, 6))

        self.z = zipfile.ZipFile(self.zip_filename, 'w', allowZip64=True)
        self.processed_size_callback = processed_size_callback
        if self.processed_size_callback is None:
            self.processed_size_callback = lambda _: None
        self._size = 0
        self.processed_size_callback(self._size)

    def add_file(self, filename):
        """
        Add a file to the zip archive.
        """
        self.z.write(filename, os.path.basename(filename), zipfile.ZIP_DEFLATED)
        self._size += os.path.getsize(filename)
        self.processed_size_callback(self._size)

    def add_dir(self, filename):
        """
        Add a directory, and all of its children, to the zip archive.
        """
        dir_to_strip = os.path.dirname(filename.rstrip('/'))+'/'
        for dirpath, dirnames, filenames in os.walk(filename):
            for f in filenames:
                full_filename = os.path.join(dirpath, f)
                if not os.path.islink(full_filename):
                    arc_filename = full_filename[len(dir_to_strip):]
                    self.z.write(full_filename, arc_filename, zipfile.ZIP_DEFLATED)
                    self._size += os.path.getsize(full_filename)
                    self.processed_size_callback(self._size)

    def close(self):
        """
        Close the zip archive.
        """
        self.z.close()


class ReceiveModeWSGIMiddleware(object):
    """
    Custom WSGI middleware in order to attach the Web object to environ, so
    ReceiveModeRequest can access it.
    """
    def __init__(self, app, web):
        self.app = app
        self.web = web

    def __call__(self, environ, start_response):
        environ['web'] = self.web
        return self.app(environ, start_response)

class ReceiveModeTemporaryFile(object):
    """
    A custom TemporaryFile that tells ReceiveModeRequest every time data gets
    written to it, in order to track the progress of uploads.
    """
    def __init__(self, filename, update_func):
        self.onionshare_filename = filename
        self.onionshare_update_func = update_func

        # Create a temporary file
        self.f = tempfile.TemporaryFile('wb+')

        # Make all the file-like methods and attributes actually access the
        # TemporaryFile, except for write
        attrs = ['close', 'closed', 'detach', 'fileno', 'flush', 'isatty', 'mode',
                 'name', 'peek', 'raw', 'read', 'read1', 'readable', 'readinto',
                 'readinto1', 'readline', 'readlines', 'seek', 'seekable', 'tell',
                 'truncate', 'writable', 'writelines']
        for attr in attrs:
            setattr(self, attr, getattr(self.f, attr))

    def write(self, b):
        """
        Custom write method that calls out to onionshare_update_func
        """
        bytes_written = self.f.write(b)
        self.onionshare_update_func(self.onionshare_filename, bytes_written)


class ReceiveModeRequest(Request):
    """
    A custom flask Request object that keeps track of how much data has been
    uploaded for each file, for receive mode.
    """
    def __init__(self, environ, populate_request=True, shallow=False):
        super(ReceiveModeRequest, self).__init__(environ, populate_request, shallow)
        self.web = environ['web']

        # A dictionary that maps filenames to the bytes uploaded so far
        self.onionshare_progress = {}

    def _get_file_stream(self, total_content_length, content_type, filename=None, content_length=None):
        """
        This gets called for each file that gets uploaded, and returns an file-like
        writable stream.
        """
        if len(self.onionshare_progress) > 0:
            print('')
        self.onionshare_progress[filename] = 0
        return ReceiveModeTemporaryFile(filename, self.onionshare_update_func)

    def close(self):
        """
        When closing the request, print a newline if this was a file upload.
        """
        super(ReceiveModeRequest, self).close()
        if len(self.onionshare_progress) > 0:
            print('')

    def onionshare_update_func(self, filename, length):
        """
        Keep track of the bytes uploaded so far for all files.
        """
        self.onionshare_progress[filename] += length
        print('{} - {}     '.format(self.web.common.human_readable_filesize(self.onionshare_progress[filename]), filename), end='\r')
