import hmac
import logging
import mimetypes
import os
import queue
import socket
import sys
import tempfile
from distutils.version import LooseVersion as Version
from urllib.request import urlopen

import flask
from flask import (
    Flask, Response, request, render_template, abort, make_response,
    flash, redirect, __version__ as flask_version
)
from werkzeug.utils import secure_filename

from .. import strings
from ..common import DownloadsDirErrorCannotCreate, DownloadsDirErrorNotWritable

from .share_mode import ZipWriter
from .receive_mode import ReceiveModeWSGIMiddleware, ReceiveModeTemporaryFile, ReceiveModeRequest


# Stub out flask's show_server_banner function, to avoiding showing warnings that
# are not applicable to OnionShare
def stubbed_show_server_banner(env, debug, app_import_path, eager_loading):
    pass

flask.cli.show_server_banner = stubbed_show_server_banner


class Web(object):
    """
    The Web object is the OnionShare web server, powered by flask
    """
    REQUEST_LOAD = 0
    REQUEST_STARTED = 1
    REQUEST_PROGRESS = 2
    REQUEST_OTHER = 3
    REQUEST_CANCELED = 4
    REQUEST_RATE_LIMIT = 5
    REQUEST_CLOSE_SERVER = 6
    REQUEST_UPLOAD_FILE_RENAMED = 7
    REQUEST_UPLOAD_FINISHED = 8
    REQUEST_ERROR_DOWNLOADS_DIR_CANNOT_CREATE = 9
    REQUEST_ERROR_DOWNLOADS_DIR_NOT_WRITABLE = 10

    def __init__(self, common, gui_mode, receive_mode=False):
        self.common = common

        # The flask app
        self.app = Flask(__name__,
                         static_folder=self.common.get_resource_path('static'),
                         template_folder=self.common.get_resource_path('templates'))
        self.app.secret_key = self.common.random_string(8)

        # Debug mode?
        if self.common.debug:
            self.debug_mode()

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
        self.is_zipped = False
        self.download_filename = None
        self.download_filesize = None
        self.zip_writer = None

        self.security_headers = [
            ('Content-Security-Policy', 'default-src \'self\'; style-src \'self\'; script-src \'self\'; img-src \'self\' data:;'),
            ('X-Frame-Options', 'DENY'),
            ('X-Xss-Protection', '1; mode=block'),
            ('X-Content-Type-Options', 'nosniff'),
            ('Referrer-Policy', 'no-referrer'),
            ('Server', 'OnionShare')
        ]

        self.q = queue.Queue()

        self.slug = None

        self.download_count = 0
        self.upload_count = 0

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

        # Keep track if the server is running
        self.running = False

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
            self.check_slug_candidate(slug_candidate)
            return index_logic()

        @self.app.route("/")
        def index_public():
            if not self.common.settings.get('public_mode'):
                return self.error404()
            return index_logic()

        def index_logic(slug_candidate=''):
            """
            Render the template for the onionshare landing page.
            """
            self.add_request(Web.REQUEST_LOAD, request.path)

            # Deny new downloads if "Stop After First Download" is checked and there is
            # currently a download
            deny_download = not self.stay_open and self.download_in_progress
            if deny_download:
                r = make_response(render_template('denied.html'))
                return self.add_security_headers(r)

            # If download is allowed to continue, serve download page
            if self.slug:
                r = make_response(render_template(
                    'send.html',
                    slug=self.slug,
                    file_info=self.file_info,
                    filename=os.path.basename(self.download_filename),
                    filesize=self.download_filesize,
                    filesize_human=self.common.human_readable_filesize(self.download_filesize),
                    is_zipped=self.is_zipped))
            else:
                # If download is allowed to continue, serve download page
                r = make_response(render_template(
                    'send.html',
                    file_info=self.file_info,
                    filename=os.path.basename(self.download_filename),
                    filesize=self.download_filesize,
                    filesize_human=self.common.human_readable_filesize(self.download_filesize),
                    is_zipped=self.is_zipped))
            return self.add_security_headers(r)

        @self.app.route("/<slug_candidate>/download")
        def download(slug_candidate):
            self.check_slug_candidate(slug_candidate)
            return download_logic()

        @self.app.route("/download")
        def download_public():
            if not self.common.settings.get('public_mode'):
                return self.error404()
            return download_logic()

        def download_logic(slug_candidate=''):
            """
            Download the zip file.
            """
            # Deny new downloads if "Stop After First Download" is checked and there is
            # currently a download
            deny_download = not self.stay_open and self.download_in_progress
            if deny_download:
                r = make_response(render_template('denied.html'))
                return self.add_security_headers(r)

            # Each download has a unique id
            download_id = self.download_count
            self.download_count += 1

            # Prepare some variables to use inside generate() function below
            # which is outside of the request context
            shutdown_func = request.environ.get('werkzeug.server.shutdown')
            path = request.path

            # Tell GUI the download started
            self.add_request(Web.REQUEST_STARTED, path, {
                'id': download_id}
            )

            dirname = os.path.dirname(self.download_filename)
            basename = os.path.basename(self.download_filename)

            def generate():
                # The user hasn't canceled the download
                self.client_cancel = False

                # Starting a new download
                if not self.stay_open:
                    self.download_in_progress = True

                chunk_size = 102400  # 100kb

                fp = open(self.download_filename, 'rb')
                self.done = False
                canceled = False
                while not self.done:
                    # The user has canceled the download, so stop serving the file
                    if self.client_cancel:
                        self.add_request(Web.REQUEST_CANCELED, path, {
                            'id': download_id
                        })
                        break

                    chunk = fp.read(chunk_size)
                    if chunk == b'':
                        self.done = True
                    else:
                        try:
                            yield chunk

                            # tell GUI the progress
                            downloaded_bytes = fp.tell()
                            percent = (1.0 * downloaded_bytes / self.download_filesize) * 100

                            # only output to stdout if running onionshare in CLI mode, or if using Linux (#203, #304)
                            if not self.gui_mode or self.common.platform == 'Linux' or self.common.platform == 'BSD':
                                sys.stdout.write(
                                    "\r{0:s}, {1:.2f}%          ".format(self.common.human_readable_filesize(downloaded_bytes), percent))
                                sys.stdout.flush()

                            self.add_request(Web.REQUEST_PROGRESS, path, {
                                'id': download_id,
                                'bytes': downloaded_bytes
                                })
                            self.done = False
                        except:
                            # looks like the download was canceled
                            self.done = True
                            canceled = True

                            # tell the GUI the download has canceled
                            self.add_request(Web.REQUEST_CANCELED, path, {
                                'id': download_id
                            })

                fp.close()

                if self.common.platform != 'Darwin':
                    sys.stdout.write("\n")

                # Download is finished
                if not self.stay_open:
                    self.download_in_progress = False

                # Close the server, if necessary
                if not self.stay_open and not canceled:
                    print(strings._("closing_automatically"))
                    self.running = False
                    try:
                        if shutdown_func is None:
                            raise RuntimeError('Not running with the Werkzeug Server')
                        shutdown_func()
                    except:
                        pass

            r = Response(generate())
            r.headers.set('Content-Length', self.download_filesize)
            r.headers.set('Content-Disposition', 'attachment', filename=basename)
            r = self.add_security_headers(r)
            # guess content type
            (content_type, _) = mimetypes.guess_type(basename, strict=False)
            if content_type is not None:
                r.headers.set('Content-Type', content_type)
            return r

    def receive_routes(self):
        """
        The web app routes for receiving files
        """
        def index_logic():
            self.add_request(Web.REQUEST_LOAD, request.path)

            if self.common.settings.get('public_mode'):
                upload_action = '/upload'
                close_action = '/close'
            else:
                upload_action = '/{}/upload'.format(self.slug)
                close_action = '/{}/close'.format(self.slug)

            r = make_response(render_template(
                'receive.html',
                upload_action=upload_action,
                close_action=close_action,
                receive_allow_receiver_shutdown=self.common.settings.get('receive_allow_receiver_shutdown')))
            return self.add_security_headers(r)

        @self.app.route("/<slug_candidate>")
        def index(slug_candidate):
            self.check_slug_candidate(slug_candidate)
            return index_logic()

        @self.app.route("/")
        def index_public():
            if not self.common.settings.get('public_mode'):
                return self.error404()
            return index_logic()


        def upload_logic(slug_candidate=''):
            """
            Upload files.
            """
            # Make sure downloads_dir exists
            valid = True
            try:
                self.common.validate_downloads_dir()
            except DownloadsDirErrorCannotCreate:
                self.add_request(Web.REQUEST_ERROR_DOWNLOADS_DIR_CANNOT_CREATE, request.path)
                print(strings._('error_cannot_create_downloads_dir').format(self.common.settings.get('downloads_dir')))
                valid = False
            except DownloadsDirErrorNotWritable:
                self.add_request(Web.REQUEST_ERROR_DOWNLOADS_DIR_NOT_WRITABLE, request.path)
                print(strings._('error_downloads_dir_not_writable').format(self.common.settings.get('downloads_dir')))
                valid = False
            if not valid:
                flash('Error uploading, please inform the OnionShare user', 'error')
                if self.common.settings.get('public_mode'):
                    return redirect('/')
                else:
                    return redirect('/{}'.format(slug_candidate))

            files = request.files.getlist('file[]')
            filenames = []
            print('')
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

                    basename = os.path.basename(local_path)
                    if f.filename != basename:
                        # Tell the GUI that the file has changed names
                        self.add_request(Web.REQUEST_UPLOAD_FILE_RENAMED, request.path, {
                            'id': request.upload_id,
                            'old_filename': f.filename,
                            'new_filename': basename
                        })

                    self.common.log('Web', 'receive_routes', '/upload, uploaded {}, saving to {}'.format(f.filename, local_path))
                    print(strings._('receive_mode_received_file').format(local_path))
                    f.save(local_path)

            # Note that flash strings are on English, and not translated, on purpose,
            # to avoid leaking the locale of the OnionShare user
            if len(filenames) == 0:
                flash('No files uploaded', 'info')
            else:
                for filename in filenames:
                    flash('Sent {}'.format(filename), 'info')

            if self.common.settings.get('public_mode'):
                return redirect('/')
            else:
                return redirect('/{}'.format(slug_candidate))

        @self.app.route("/<slug_candidate>/upload", methods=['POST'])
        def upload(slug_candidate):
            self.check_slug_candidate(slug_candidate)
            return upload_logic(slug_candidate)

        @self.app.route("/upload", methods=['POST'])
        def upload_public():
            if not self.common.settings.get('public_mode'):
                return self.error404()
            return upload_logic()


        def close_logic(slug_candidate=''):
            if self.common.settings.get('receive_allow_receiver_shutdown'):
                self.force_shutdown()
                r = make_response(render_template('closed.html'))
                self.add_request(Web.REQUEST_CLOSE_SERVER, request.path)
                return self.add_security_headers(r)
            else:
                return redirect('/{}'.format(slug_candidate))

        @self.app.route("/<slug_candidate>/close", methods=['POST'])
        def close(slug_candidate):
            self.check_slug_candidate(slug_candidate)
            return close_logic(slug_candidate)

        @self.app.route("/close", methods=['POST'])
        def close_public():
            if not self.common.settings.get('public_mode'):
                return self.error404()
            return close_logic()

    def common_routes(self):
        """
        Common web app routes between sending and receiving
        """
        @self.app.errorhandler(404)
        def page_not_found(e):
            """
            404 error page.
            """
            return self.error404()

        @self.app.route("/<slug_candidate>/shutdown")
        def shutdown(slug_candidate):
            """
            Stop the flask web server, from the context of an http request.
            """
            self.check_shutdown_slug_candidate(slug_candidate)
            self.force_shutdown()
            return ""

    def error404(self):
        self.add_request(Web.REQUEST_OTHER, request.path)
        if request.path != '/favicon.ico':
            self.error404_count += 1

            # In receive mode, with public mode enabled, skip rate limiting 404s
            if not self.common.settings.get('public_mode'):
                if self.error404_count == 20:
                    self.add_request(Web.REQUEST_RATE_LIMIT, request.path)
                    self.force_shutdown()
                    print(strings._('error_rate_limit'))

        r = make_response(render_template('404.html'), 404)
        return self.add_security_headers(r)

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
        self.common.log("Web", "set_file_info")
        self.cancel_compression = False

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

        # Check if there's only 1 file and no folders
        if len(self.file_info['files']) == 1 and len(self.file_info['dirs']) == 0:
            self.is_zipped = False
            self.download_filename = self.file_info['files'][0]['filename']
            self.download_filesize = self.file_info['files'][0]['size']
        else:
            # Zip up the files and folders
            self.zip_writer = ZipWriter(self.common, processed_size_callback=processed_size_callback)
            self.download_filename = self.zip_writer.zip_filename
            for info in self.file_info['files']:
                self.zip_writer.add_file(info['filename'])
                # Canceling early?
                if self.cancel_compression:
                    self.zip_writer.close()
                    return False

            for info in self.file_info['dirs']:
                if not self.zip_writer.add_dir(info['filename']):
                    return False

            self.zip_writer.close()
            self.download_filesize = os.path.getsize(self.download_filename)
            self.is_zipped = True

        return True

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

    def generate_slug(self, persistent_slug=None):
        self.common.log('Web', 'generate_slug', 'persistent_slug={}'.format(persistent_slug))
        if persistent_slug != None and persistent_slug != '':
            self.slug = persistent_slug
            self.common.log('Web', 'generate_slug', 'persistent_slug sent, so slug is: "{}"'.format(self.slug))
        else:
            self.slug = self.common.build_slug()
            self.common.log('Web', 'generate_slug', 'built random slug: "{}"'.format(self.slug))

    def debug_mode(self):
        """
        Turn on debugging mode, which will log flask errors to a debug file.
        """
        temp_dir = tempfile.gettempdir()
        log_handler = logging.FileHandler(
            os.path.join(temp_dir, 'onionshare_server.log'))
        log_handler.setLevel(logging.WARNING)
        self.app.logger.addHandler(log_handler)

    def check_slug_candidate(self, slug_candidate):
        self.common.log('Web', 'check_slug_candidate: slug_candidate={}'.format(slug_candidate))
        if self.common.settings.get('public_mode'):
            abort(404)
        if not hmac.compare_digest(self.slug, slug_candidate):
            abort(404)

    def check_shutdown_slug_candidate(self, slug_candidate):
        self.common.log('Web', 'check_shutdown_slug_candidate: slug_candidate={}'.format(slug_candidate))
        if not hmac.compare_digest(self.shutdown_slug, slug_candidate):
            abort(404)

    def force_shutdown(self):
        """
        Stop the flask web server, from the context of the flask app.
        """
        # Shutdown the flask service
        try:
            func = request.environ.get('werkzeug.server.shutdown')
            if func is None:
                raise RuntimeError('Not running with the Werkzeug Server')
            func()
        except:
            pass
        self.running = False

    def start(self, port, stay_open=False, public_mode=False, persistent_slug=None):
        """
        Start the flask web server.
        """
        self.common.log('Web', 'start', 'port={}, stay_open={}, public_mode={}, persistent_slug={}'.format(port, stay_open, public_mode, persistent_slug))
        if not public_mode:
            self.generate_slug(persistent_slug)

        self.stay_open = stay_open

        # In Whonix, listen on 0.0.0.0 instead of 127.0.0.1 (#220)
        if os.path.exists('/usr/share/anon-ws-base-files/workstation'):
            host = '0.0.0.0'
        else:
            host = '127.0.0.1'

        self.running = True
        self.app.run(host=host, port=port, threaded=True)

    def stop(self, port):
        """
        Stop the flask web server by loading /shutdown.
        """

        # If the user cancels the download, let the download function know to stop
        # serving the file
        self.client_cancel = True

        # To stop flask, load http://127.0.0.1:<port>/<shutdown_slug>/shutdown
        if self.running:
            try:
                s = socket.socket()
                s.connect(('127.0.0.1', port))
                s.sendall('GET /{0:s}/shutdown HTTP/1.1\r\n\r\n'.format(self.shutdown_slug))
            except:
                try:
                    urlopen('http://127.0.0.1:{0:d}/{1:s}/shutdown'.format(port, self.shutdown_slug)).read()
                except:
                    pass
