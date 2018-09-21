import tempfile
from datetime import datetime
from flask import Request

from .. import strings


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
