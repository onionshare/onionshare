import os
import sys
import tempfile
import zipfile
import mimetypes
import gzip
from flask import Response, request, render_template, make_response

from .. import strings


class ShareModeWeb(object):
    """
    All of the web logic for share mode
    """
    def __init__(self, common, web):
        self.common = common
        self.common.log('ShareModeWeb', '__init__')

        self.web = web

        # Information about the file to be shared
        self.file_info = []
        self.is_zipped = False
        self.download_filename = None
        self.download_filesize = None
        self.gzip_filename = None
        self.gzip_filesize = None
        self.zip_writer = None

        self.download_count = 0

        # If "Stop After First Download" is checked (stay_open == False), only allow
        # one download at a time.
        self.download_in_progress = False

        # Reset assets path
        self.web.app.static_folder=self.common.get_resource_path('static')


        self.define_routes()

    def define_routes(self):
        """
        The web app routes for sharing files
        """
        @self.web.app.route("/")
        def index():
            """
            Render the template for the onionshare landing page.
            """
            self.web.add_request(self.web.REQUEST_LOAD, request.path)

            # Deny new downloads if "Stop After First Download" is checked and there is
            # currently a download
            deny_download = not self.web.stay_open and self.download_in_progress
            if deny_download:
                r = make_response(render_template('denied.html'))
                return self.web.add_security_headers(r)

            # If download is allowed to continue, serve download page
            if self.should_use_gzip():
                self.filesize = self.gzip_filesize
            else:
                self.filesize = self.download_filesize

            r = make_response(render_template(
                'send.html',
                file_info=self.file_info,
                filename=os.path.basename(self.download_filename),
                filesize=self.filesize,
                filesize_human=self.common.human_readable_filesize(self.download_filesize),
                is_zipped=self.is_zipped))
            return self.web.add_security_headers(r)

        @self.web.app.route("/download")
        def download():
            """
            Download the zip file.
            """
            # Deny new downloads if "Stop After First Download" is checked and there is
            # currently a download
            deny_download = not self.web.stay_open and self.download_in_progress
            if deny_download:
                r = make_response(render_template('denied.html'))
                return self.web.add_security_headers(r)

            # Each download has a unique id
            download_id = self.download_count
            self.download_count += 1

            # Prepare some variables to use inside generate() function below
            # which is outside of the request context
            shutdown_func = request.environ.get('werkzeug.server.shutdown')
            path = request.path

            # If this is a zipped file, then serve as-is. If it's not zipped, then,
            # if the http client supports gzip compression, gzip the file first
            # and serve that
            use_gzip = self.should_use_gzip()
            if use_gzip:
                file_to_download = self.gzip_filename
                self.filesize = self.gzip_filesize
            else:
                file_to_download = self.download_filename
                self.filesize = self.download_filesize

            # Tell GUI the download started
            self.web.add_request(self.web.REQUEST_STARTED, path, {
                'id': download_id,
                'use_gzip': use_gzip
            })

            basename = os.path.basename(self.download_filename)

            def generate():
                # Starting a new download
                if not self.web.stay_open:
                    self.download_in_progress = True

                chunk_size = 102400  # 100kb

                fp = open(file_to_download, 'rb')
                self.web.done = False
                canceled = False
                while not self.web.done:
                    # The user has canceled the download, so stop serving the file
                    if not self.web.stop_q.empty():
                        self.web.add_request(self.web.REQUEST_CANCELED, path, {
                            'id': download_id
                        })
                        break

                    chunk = fp.read(chunk_size)
                    if chunk == b'':
                        self.web.done = True
                    else:
                        try:
                            yield chunk

                            # tell GUI the progress
                            downloaded_bytes = fp.tell()
                            percent = (1.0 * downloaded_bytes / self.filesize) * 100

                            # only output to stdout if running onionshare in CLI mode, or if using Linux (#203, #304)
                            if not self.web.is_gui or self.common.platform == 'Linux' or self.common.platform == 'BSD':
                                sys.stdout.write(
                                    "\r{0:s}, {1:.2f}%          ".format(self.common.human_readable_filesize(downloaded_bytes), percent))
                                sys.stdout.flush()

                            self.web.add_request(self.web.REQUEST_PROGRESS, path, {
                                'id': download_id,
                                'bytes': downloaded_bytes
                                })
                            self.web.done = False
                        except:
                            # looks like the download was canceled
                            self.web.done = True
                            canceled = True

                            # tell the GUI the download has canceled
                            self.web.add_request(self.web.REQUEST_CANCELED, path, {
                                'id': download_id
                            })

                fp.close()

                if self.common.platform != 'Darwin':
                    sys.stdout.write("\n")

                # Download is finished
                if not self.web.stay_open:
                    self.download_in_progress = False

                # Close the server, if necessary
                if not self.web.stay_open and not canceled:
                    print("Stopped because transfer is complete")
                    self.web.running = False
                    try:
                        if shutdown_func is None:
                            raise RuntimeError('Not running with the Werkzeug Server')
                        shutdown_func()
                    except:
                        pass

            r = Response(generate())
            if use_gzip:
                r.headers.set('Content-Encoding', 'gzip')
            r.headers.set('Content-Length', self.filesize)
            r.headers.set('Content-Disposition', 'attachment', filename=basename)
            r = self.web.add_security_headers(r)
            # guess content type
            (content_type, _) = mimetypes.guess_type(basename, strict=False)
            if content_type is not None:
                r.headers.set('Content-Type', content_type)
            return r

    def set_file_info(self, filenames, processed_size_callback=None):
        """
        Using the list of filenames being shared, fill in details that the web
        page will need to display. This includes zipping up the file in order to
        get the zip file's name and size.
        """
        self.common.log("ShareModeWeb", "set_file_info")
        self.web.cancel_compression = False

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

        # Check if there's only 1 file and no folders
        if len(self.file_info['files']) == 1 and len(self.file_info['dirs']) == 0:
            self.download_filename = self.file_info['files'][0]['filename']
            self.download_filesize = self.file_info['files'][0]['size']

            # Compress the file with gzip now, so we don't have to do it on each request
            self.gzip_filename = tempfile.mkstemp('wb+')[1]
            self._gzip_compress(self.download_filename, self.gzip_filename, 6, processed_size_callback)
            self.gzip_filesize = os.path.getsize(self.gzip_filename)

            # Make sure the gzip file gets cleaned up when onionshare stops
            self.cleanup_filenames.append(self.gzip_filename)

            self.is_zipped = False

        else:
            # Zip up the files and folders
            self.zip_writer = ZipWriter(self.common, processed_size_callback=processed_size_callback)
            self.download_filename = self.zip_writer.zip_filename
            for info in self.file_info['files']:
                self.zip_writer.add_file(info['filename'])
                # Canceling early?
                if self.web.cancel_compression:
                    self.zip_writer.close()
                    return False

            for info in self.file_info['dirs']:
                if not self.zip_writer.add_dir(info['filename']):
                    return False

            self.zip_writer.close()
            self.download_filesize = os.path.getsize(self.download_filename)

            # Make sure the zip file gets cleaned up when onionshare stops
            self.cleanup_filenames.append(self.zip_writer.zip_filename)

            self.is_zipped = True

        return True

    def should_use_gzip(self):
        """
        Should we use gzip for this browser?
        """
        return (not self.is_zipped) and ('gzip' in request.headers.get('Accept-Encoding', '').lower())

    def _gzip_compress(self, input_filename, output_filename, level, processed_size_callback=None):
        """
        Compress a file with gzip, without loading the whole thing into memory
        Thanks: https://stackoverflow.com/questions/27035296/python-how-to-gzip-a-large-text-file-without-memoryerror
        """
        bytes_processed = 0
        blocksize = 1 << 16 # 64kB
        with open(input_filename, 'rb') as input_file:
            output_file = gzip.open(output_filename, 'wb', level)
            while True:
                if processed_size_callback is not None:
                    processed_size_callback(bytes_processed)

                block = input_file.read(blocksize)
                if len(block) == 0:
                    break
                output_file.write(block)
                bytes_processed += blocksize

            output_file.close()


class ZipWriter(object):
    """
    ZipWriter accepts files and directories and compresses them into a zip file
    with. If a zip_filename is not passed in, it will use the default onionshare
    filename.
    """
    def __init__(self, common, zip_filename=None, processed_size_callback=None):
        self.common = common
        self.cancel_compression = False

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
                # Canceling early?
                if self.cancel_compression:
                    return False

                full_filename = os.path.join(dirpath, f)
                if not os.path.islink(full_filename):
                    arc_filename = full_filename[len(dir_to_strip):]
                    self.z.write(full_filename, arc_filename, zipfile.ZIP_DEFLATED)
                    self._size += os.path.getsize(full_filename)
                    self.processed_size_callback(self._size)

        return True

    def close(self):
        """
        Close the zip archive.
        """
        self.z.close()
