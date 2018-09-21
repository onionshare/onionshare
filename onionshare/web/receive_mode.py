import os
import tempfile
from datetime import datetime
from flask import Request, request, render_template, make_response, flash, redirect
from werkzeug.utils import secure_filename

from ..common import DownloadsDirErrorCannotCreate, DownloadsDirErrorNotWritable
from .. import strings


def receive_routes(web):
    """
    The web app routes for receiving files
    """
    def index_logic():
        web.add_request(web.REQUEST_LOAD, request.path)

        if web.common.settings.get('public_mode'):
            upload_action = '/upload'
            close_action = '/close'
        else:
            upload_action = '/{}/upload'.format(web.slug)
            close_action = '/{}/close'.format(web.slug)

        r = make_response(render_template(
            'receive.html',
            upload_action=upload_action,
            close_action=close_action,
            receive_allow_receiver_shutdown=web.common.settings.get('receive_allow_receiver_shutdown')))
        return web.add_security_headers(r)

    @web.app.route("/<slug_candidate>")
    def index(slug_candidate):
        web.check_slug_candidate(slug_candidate)
        return index_logic()

    @web.app.route("/")
    def index_public():
        if not web.common.settings.get('public_mode'):
            return web.error404()
        return index_logic()


    def upload_logic(slug_candidate=''):
        """
        Upload files.
        """
        # Make sure downloads_dir exists
        valid = True
        try:
            web.common.validate_downloads_dir()
        except DownloadsDirErrorCannotCreate:
            web.add_request(web.REQUEST_ERROR_DOWNLOADS_DIR_CANNOT_CREATE, request.path)
            print(strings._('error_cannot_create_downloads_dir').format(web.common.settings.get('downloads_dir')))
            valid = False
        except DownloadsDirErrorNotWritable:
            web.add_request(web.REQUEST_ERROR_DOWNLOADS_DIR_NOT_WRITABLE, request.path)
            print(strings._('error_downloads_dir_not_writable').format(web.common.settings.get('downloads_dir')))
            valid = False
        if not valid:
            flash('Error uploading, please inform the OnionShare user', 'error')
            if web.common.settings.get('public_mode'):
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
                local_path = os.path.join(web.common.settings.get('downloads_dir'), filename)
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
                            local_path = os.path.join(web.common.settings.get('downloads_dir'), new_filename)
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
                            local_path = os.path.join(web.common.settings.get('downloads_dir'), new_filename)
                            if os.path.exists(local_path):
                                i += 1
                            else:
                                valid = True

                basename = os.path.basename(local_path)
                if f.filename != basename:
                    # Tell the GUI that the file has changed names
                    web.add_request(web.REQUEST_UPLOAD_FILE_RENAMED, request.path, {
                        'id': request.upload_id,
                        'old_filename': f.filename,
                        'new_filename': basename
                    })

                web.common.log('Web', 'receive_routes', '/upload, uploaded {}, saving to {}'.format(f.filename, local_path))
                print(strings._('receive_mode_received_file').format(local_path))
                f.save(local_path)

        # Note that flash strings are on English, and not translated, on purpose,
        # to avoid leaking the locale of the OnionShare user
        if len(filenames) == 0:
            flash('No files uploaded', 'info')
        else:
            for filename in filenames:
                flash('Sent {}'.format(filename), 'info')

        if web.common.settings.get('public_mode'):
            return redirect('/')
        else:
            return redirect('/{}'.format(slug_candidate))

    @web.app.route("/<slug_candidate>/upload", methods=['POST'])
    def upload(slug_candidate):
        web.check_slug_candidate(slug_candidate)
        return upload_logic(slug_candidate)

    @web.app.route("/upload", methods=['POST'])
    def upload_public():
        if not web.common.settings.get('public_mode'):
            return web.error404()
        return upload_logic()


    def close_logic(slug_candidate=''):
        if web.common.settings.get('receive_allow_receiver_shutdown'):
            web.force_shutdown()
            r = make_response(render_template('closed.html'))
            web.add_request(web.REQUEST_CLOSE_SERVER, request.path)
            return web.add_security_headers(r)
        else:
            return redirect('/{}'.format(slug_candidate))

    @web.app.route("/<slug_candidate>/close", methods=['POST'])
    def close(slug_candidate):
        web.check_slug_candidate(slug_candidate)
        return close_logic(slug_candidate)

    @web.app.route("/close", methods=['POST'])
    def close_public():
        if not web.common.settings.get('public_mode'):
            return web.error404()
        return close_logic()


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
    def __init__(self, filename, write_func, close_func):
        self.onionshare_filename = filename
        self.onionshare_write_func = write_func
        self.onionshare_close_func = close_func

        # Create a temporary file
        self.f = tempfile.TemporaryFile('wb+')

        # Make all the file-like methods and attributes actually access the
        # TemporaryFile, except for write
        attrs = ['closed', 'detach', 'fileno', 'flush', 'isatty', 'mode',
                 'name', 'peek', 'raw', 'read', 'read1', 'readable', 'readinto',
                 'readinto1', 'readline', 'readlines', 'seek', 'seekable', 'tell',
                 'truncate', 'writable', 'writelines']
        for attr in attrs:
            setattr(self, attr, getattr(self.f, attr))

    def write(self, b):
        """
        Custom write method that calls out to onionshare_write_func
        """
        bytes_written = self.f.write(b)
        self.onionshare_write_func(self.onionshare_filename, bytes_written)

    def close(self):
        """
        Custom close method that calls out to onionshare_close_func
        """
        self.f.close()
        self.onionshare_close_func(self.onionshare_filename)


class ReceiveModeRequest(Request):
    """
    A custom flask Request object that keeps track of how much data has been
    uploaded for each file, for receive mode.
    """
    def __init__(self, environ, populate_request=True, shallow=False):
        super(ReceiveModeRequest, self).__init__(environ, populate_request, shallow)
        self.web = environ['web']

        # Is this a valid upload request?
        self.upload_request = False
        if self.method == 'POST':
            if self.path == '/{}/upload'.format(self.web.slug):
                self.upload_request = True
            else:
                if self.web.common.settings.get('public_mode'):
                    if self.path == '/upload':
                        self.upload_request = True

        if self.upload_request:
            # A dictionary that maps filenames to the bytes uploaded so far
            self.progress = {}

            # Create an upload_id, attach it to the request
            self.upload_id = self.web.upload_count
            self.web.upload_count += 1

            # Figure out the content length
            try:
                self.content_length = int(self.headers['Content-Length'])
            except:
                self.content_length = 0

            print("{}: {}".format(
                datetime.now().strftime("%b %d, %I:%M%p"),
                strings._("receive_mode_upload_starting").format(self.web.common.human_readable_filesize(self.content_length))
            ))

            # Tell the GUI
            self.web.add_request(self.web.REQUEST_STARTED, self.path, {
                'id': self.upload_id,
                'content_length': self.content_length
            })

            self.previous_file = None

    def _get_file_stream(self, total_content_length, content_type, filename=None, content_length=None):
        """
        This gets called for each file that gets uploaded, and returns an file-like
        writable stream.
        """
        if self.upload_request:
            self.progress[filename] = {
                'uploaded_bytes': 0,
                'complete': False
            }

        return ReceiveModeTemporaryFile(filename, self.file_write_func, self.file_close_func)

    def close(self):
        """
        Closing the request.
        """
        super(ReceiveModeRequest, self).close()
        if self.upload_request:
            # Inform the GUI that the upload has finished
            self.web.add_request(self.web.REQUEST_UPLOAD_FINISHED, self.path, {
                'id': self.upload_id
            })

    def file_write_func(self, filename, length):
        """
        This function gets called when a specific file is written to.
        """
        if self.upload_request:
            self.progress[filename]['uploaded_bytes'] += length

            if self.previous_file != filename:
                if self.previous_file is not None:
                    print('')
                self.previous_file = filename

            print('\r=> {:15s} {}'.format(
                self.web.common.human_readable_filesize(self.progress[filename]['uploaded_bytes']),
                filename
            ), end='')

            # Update the GUI on the upload progress
            self.web.add_request(self.web.REQUEST_PROGRESS, self.path, {
                'id': self.upload_id,
                'progress': self.progress
            })

    def file_close_func(self, filename):
        """
        This function gets called when a specific file is closed.
        """
        self.progress[filename]['complete'] = True
