import os
import tempfile
import json
from datetime import datetime
from flask import Request, request, render_template, make_response, flash, redirect
from werkzeug.utils import secure_filename

from .. import strings


class ReceiveModeWeb(object):
    """
    All of the web logic for receive mode
    """
    def __init__(self, common, web):
        self.common = common
        self.common.log('ReceiveModeWeb', '__init__')

        self.web = web

        self.can_upload = True
        self.upload_count = 0
        self.uploads_in_progress = []

        self.define_routes()

    def define_routes(self):
        """
        The web app routes for receiving files
        """
        def index_logic():
            self.web.add_request(self.web.REQUEST_LOAD, request.path)

            if self.common.settings.get('public_mode'):
                upload_action = '/upload'
            else:
                upload_action = '/{}/upload'.format(self.web.slug)

            r = make_response(render_template(
                'receive.html',
                upload_action=upload_action))
            return self.web.add_security_headers(r)

        @self.web.app.route("/<slug_candidate>")
        def index(slug_candidate):
            if not self.can_upload:
                return self.web.error403()
            self.web.check_slug_candidate(slug_candidate)
            return index_logic()

        @self.web.app.route("/")
        def index_public():
            if not self.can_upload:
                return self.web.error403()
            if not self.common.settings.get('public_mode'):
                return self.web.error404()
            return index_logic()


        def upload_logic(slug_candidate='', ajax=False):
            """
            Handle the upload files POST request, though at this point, the files have
            already been uploaded and saved to their correct locations.
            """
            files = request.files.getlist('file[]')
            filenames = []
            for f in files:
                if f.filename != '':
                    filename = secure_filename(f.filename)
                    filenames.append(filename)
                    local_path = os.path.join(request.receive_mode_dir, filename)
                    basename = os.path.basename(local_path)

                    # Tell the GUI the receive mode directory for this file
                    self.web.add_request(self.web.REQUEST_UPLOAD_SET_DIR, request.path, {
                        'id': request.upload_id,
                        'filename': basename,
                        'dir': request.receive_mode_dir
                    })

                    self.common.log('ReceiveModeWeb', 'define_routes', '/upload, uploaded {}, saving to {}'.format(f.filename, local_path))
                    print('\n' + strings._('receive_mode_received_file').format(local_path))

            if request.upload_error:
                self.common.log('ReceiveModeWeb', 'define_routes', '/upload, there was an upload error')

                self.web.add_request(self.web.REQUEST_ERROR_DATA_DIR_CANNOT_CREATE, request.path, {
                    "receive_mode_dir": request.receive_mode_dir
                })
                print(strings._('error_cannot_create_data_dir').format(request.receive_mode_dir))

                msg = 'Error uploading, please inform the OnionShare user'
                if ajax:
                    return json.dumps({"error_flashes": [msg]})
                else:
                    flash(msg, 'error')

                    if self.common.settings.get('public_mode'):
                        return redirect('/')
                    else:
                        return redirect('/{}'.format(slug_candidate))

            # Note that flash strings are in English, and not translated, on purpose,
            # to avoid leaking the locale of the OnionShare user
            if ajax:
                info_flashes = []

            if len(filenames) == 0:
                msg = 'No files uploaded'
                if ajax:
                    info_flashes.append(msg)
                else:
                    flash(msg, 'info')
            else:
                msg = 'Sent '
                for filename in filenames:
                    msg += '{}, '.format(filename)
                msg = msg.rstrip(', ')
                if ajax:
                    info_flashes.append(msg)
                else:
                    flash(msg, 'info')

            if self.can_upload:
                if ajax:
                    return json.dumps({"info_flashes": info_flashes})
                else:
                    if self.common.settings.get('public_mode'):
                        path = '/'
                    else:
                        path = '/{}'.format(slug_candidate)
                    return redirect('{}'.format(path))
            else:
                if ajax:
                    return json.dumps({"new_body": render_template('thankyou.html')})
                else:
                    # It was the last upload and the timer ran out
                    r = make_response(render_template('thankyou.html'))
                    return self.web.add_security_headers(r)

        @self.web.app.route("/<slug_candidate>/upload", methods=['POST'])
        def upload(slug_candidate):
            if not self.can_upload:
                return self.web.error403()
            self.web.check_slug_candidate(slug_candidate)
            return upload_logic(slug_candidate)

        @self.web.app.route("/upload", methods=['POST'])
        def upload_public():
            if not self.can_upload:
                return self.web.error403()
            if not self.common.settings.get('public_mode'):
                return self.web.error404()
            return upload_logic()

        @self.web.app.route("/<slug_candidate>/upload-ajax", methods=['POST'])
        def upload_ajax(slug_candidate):
            if not self.can_upload:
                return self.web.error403()
            self.web.check_slug_candidate(slug_candidate)
            return upload_logic(slug_candidate, ajax=True)

        @self.web.app.route("/upload-ajax", methods=['POST'])
        def upload_ajax_public():
            if not self.can_upload:
                return self.web.error403()
            if not self.common.settings.get('public_mode'):
                return self.web.error404()
            return upload_logic(ajax=True)


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
        environ['stop_q'] = self.web.stop_q
        return self.app(environ, start_response)


class ReceiveModeFile(object):
    """
    A custom file object that tells ReceiveModeRequest every time data gets
    written to it, in order to track the progress of uploads. It starts out with
    a .part file extension, and when it's complete it removes that extension.
    """
    def __init__(self, request, filename, write_func, close_func):
        self.onionshare_request = request
        self.onionshare_filename = filename
        self.onionshare_write_func = write_func
        self.onionshare_close_func = close_func

        self.filename = os.path.join(self.onionshare_request.receive_mode_dir, filename)
        self.filename_in_progress = '{}.part'.format(self.filename)

        # Open the file
        self.upload_error = False
        try:
            self.f = open(self.filename_in_progress, 'wb+')
        except:
            # This will only happen if someone is messing with the data dir while
            # OnionShare is running, but if it does make sure to throw an error
            self.upload_error = True
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
        if self.upload_error or (not self.onionshare_request.stop_q.empty()):
            self.close()
            self.onionshare_request.close()
            return

        try:
            bytes_written = self.f.write(b)
            self.onionshare_write_func(self.onionshare_filename, bytes_written)

        except:
            self.upload_error = True

    def close(self):
        """
        Custom close method that calls out to onionshare_close_func
        """
        try:
            self.f.close()

            if not self.upload_error:
                # Rename the in progress file to the final filename
                os.rename(self.filename_in_progress, self.filename)

        except:
            self.upload_error = True

        self.onionshare_close_func(self.onionshare_filename, self.upload_error)


class ReceiveModeRequest(Request):
    """
    A custom flask Request object that keeps track of how much data has been
    uploaded for each file, for receive mode.
    """
    def __init__(self, environ, populate_request=True, shallow=False):
        super(ReceiveModeRequest, self).__init__(environ, populate_request, shallow)
        self.web = environ['web']
        self.stop_q = environ['stop_q']

        self.web.common.log('ReceiveModeRequest', '__init__')

        # Prevent running the close() method more than once
        self.closed = False

        # Is this a valid upload request?
        self.upload_request = False
        if self.method == 'POST':
            if self.web.common.settings.get('public_mode'):
                if self.path == '/upload' or self.path == '/upload-ajax':
                    self.upload_request = True
            else:
                if self.path == '/{}/upload'.format(self.web.slug) or self.path == '/{}/upload-ajax'.format(self.web.slug):
                    self.upload_request = True

        if self.upload_request:
            # No errors yet
            self.upload_error = False

            # Figure out what files should be saved
            now = datetime.now()
            date_dir = now.strftime("%Y-%m-%d")
            time_dir = now.strftime("%H.%M.%S")
            self.receive_mode_dir = os.path.join(self.web.common.settings.get('data_dir'), date_dir, time_dir)

            # Create that directory, which shouldn't exist yet
            try:
                os.makedirs(self.receive_mode_dir, 0o700, exist_ok=False)
            except OSError:
                # If this directory already exists, maybe someone else is uploading files at
                # the same second, so use a different name in that case
                if os.path.exists(self.receive_mode_dir):
                    # Keep going until we find a directory name that's available
                    i = 1
                    while True:
                        new_receive_mode_dir = '{}-{}'.format(self.receive_mode_dir, i)
                        try:
                            os.makedirs(new_receive_mode_dir, 0o700, exist_ok=False)
                            self.receive_mode_dir = new_receive_mode_dir
                            break
                        except OSError:
                            pass
                        i += 1
                        # Failsafe
                        if i == 100:
                            self.web.common.log('ReceiveModeRequest', '__init__', 'Error finding available receive mode directory')
                            self.upload_error = True
                            break
            except PermissionError:
                self.web.add_request(self.web.REQUEST_ERROR_DATA_DIR_CANNOT_CREATE, request.path, {
                    "receive_mode_dir": self.receive_mode_dir
                })
                print(strings._('error_cannot_create_data_dir').format(self.receive_mode_dir))
                self.web.common.log('ReceiveModeRequest', '__init__', 'Permission denied creating receive mode directory')
                self.upload_error = True

            # If there's an error so far, finish early
            if self.upload_error:
                return

            # A dictionary that maps filenames to the bytes uploaded so far
            self.progress = {}

            # Prevent new uploads if we've said so (timer expired)
            if self.web.receive_mode.can_upload:

                # Create an upload_id, attach it to the request
                self.upload_id = self.web.receive_mode.upload_count

                self.web.receive_mode.upload_count += 1

               # Figure out the content length
                try:
                    self.content_length = int(self.headers['Content-Length'])
                except:
                    self.content_length = 0

                print("{}: {}".format(
                    datetime.now().strftime("%b %d, %I:%M%p"),
                    strings._("receive_mode_upload_starting").format(self.web.common.human_readable_filesize(self.content_length))
                ))

                # Don't tell the GUI that a request has started until we start receiving files
                self.told_gui_about_request = False

                self.previous_file = None

    def _get_file_stream(self, total_content_length, content_type, filename=None, content_length=None):
        """
        This gets called for each file that gets uploaded, and returns an file-like
        writable stream.
        """
        if self.upload_request:
            if not self.told_gui_about_request:
                # Tell the GUI about the request
                self.web.add_request(self.web.REQUEST_STARTED, self.path, {
                    'id': self.upload_id,
                    'content_length': self.content_length
                })
                self.web.receive_mode.uploads_in_progress.append(self.upload_id)

                self.told_gui_about_request = True

            self.filename = secure_filename(filename)

            self.progress[self.filename] = {
                'uploaded_bytes': 0,
                'complete': False
            }

        f = ReceiveModeFile(self, self.filename, self.file_write_func, self.file_close_func)
        if f.upload_error:
            self.web.common.log('ReceiveModeRequest', '_get_file_stream', 'Error creating file')
            self.upload_error = True
        return f

    def close(self):
        """
        Closing the request.
        """
        super(ReceiveModeRequest, self).close()

        # Prevent calling this method more than once per request
        if self.closed:
            return
        self.closed = True

        self.web.common.log('ReceiveModeRequest', 'close')

        try:
            if self.told_gui_about_request:
                upload_id = self.upload_id

                if not self.web.stop_q.empty() or not self.progress[self.filename]['complete']:
                    # Inform the GUI that the upload has canceled
                    self.web.add_request(self.web.REQUEST_UPLOAD_CANCELED, self.path, {
                        'id': upload_id
                    })
                else:
                    # Inform the GUI that the upload has finished
                    self.web.add_request(self.web.REQUEST_UPLOAD_FINISHED, self.path, {
                        'id': upload_id
                    })
                self.web.receive_mode.uploads_in_progress.remove(upload_id)

        except AttributeError:
            pass

    def file_write_func(self, filename, length):
        """
        This function gets called when a specific file is written to.
        """
        if self.closed:
            return

        if self.upload_request:
            self.progress[filename]['uploaded_bytes'] += length

            if self.previous_file != filename:
                self.previous_file = filename

            print('\r=> {:15s} {}'.format(
                self.web.common.human_readable_filesize(self.progress[filename]['uploaded_bytes']),
                filename
            ), end='')

            # Update the GUI on the upload progress
            if self.told_gui_about_request:
                self.web.add_request(self.web.REQUEST_PROGRESS, self.path, {
                    'id': self.upload_id,
                    'progress': self.progress
                })

    def file_close_func(self, filename, upload_error=False):
        """
        This function gets called when a specific file is closed.
        """
        self.progress[filename]['complete'] = True

        # If the file tells us there was an upload error, let the request know as well
        if upload_error:
            self.upload_error = True
