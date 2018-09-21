import os
import sys
import tempfile
import zipfile
import mimetypes
from flask import Response, request, render_template, make_response

from .. import strings


class ShareModeWeb(object):
    """
    All of the web logic for share mode
    """
    def __init__(self, web):
        self.web = web
        self.define_routes()

    def define_routes(self):
        """
        The web app routes for sharing files
        """
        @self.web.app.route("/<slug_candidate>")
        def index(slug_candidate):
            self.web.check_slug_candidate(slug_candidate)
            return index_logic()

        @self.web.app.route("/")
        def index_public():
            if not self.web.common.settings.get('public_mode'):
                return self.web.error404()
            return index_logic()

        def index_logic(slug_candidate=''):
            """
            Render the template for the onionshare landing page.
            """
            self.web.add_request(self.web.REQUEST_LOAD, request.path)

            # Deny new downloads if "Stop After First Download" is checked and there is
            # currently a download
            deny_download = not self.web.stay_open and self.web.download_in_progress
            if deny_download:
                r = make_response(render_template('denied.html'))
                return self.web.add_security_headers(r)

            # If download is allowed to continue, serve download page
            if self.web.slug:
                r = make_response(render_template(
                    'send.html',
                    slug=self.web.slug,
                    file_info=self.web.file_info,
                    filename=os.path.basename(self.web.download_filename),
                    filesize=self.web.download_filesize,
                    filesize_human=self.web.common.human_readable_filesize(self.web.download_filesize),
                    is_zipped=self.web.is_zipped))
            else:
                # If download is allowed to continue, serve download page
                r = make_response(render_template(
                    'send.html',
                    file_info=self.web.file_info,
                    filename=os.path.basename(self.web.download_filename),
                    filesize=self.web.download_filesize,
                    filesize_human=self.web.common.human_readable_filesize(self.web.download_filesize),
                    is_zipped=self.web.is_zipped))
            return self.web.add_security_headers(r)

        @self.web.app.route("/<slug_candidate>/download")
        def download(slug_candidate):
            self.web.check_slug_candidate(slug_candidate)
            return download_logic()

        @self.web.app.route("/download")
        def download_public():
            if not self.web.common.settings.get('public_mode'):
                return self.web.error404()
            return download_logic()

        def download_logic(slug_candidate=''):
            """
            Download the zip file.
            """
            # Deny new downloads if "Stop After First Download" is checked and there is
            # currently a download
            deny_download = not self.web.stay_open and self.web.download_in_progress
            if deny_download:
                r = make_response(render_template('denied.html'))
                return self.web.add_security_headers(r)

            # Each download has a unique id
            download_id = self.web.download_count
            self.web.download_count += 1

            # Prepare some variables to use inside generate() function below
            # which is outside of the request context
            shutdown_func = request.environ.get('werkzeug.server.shutdown')
            path = request.path

            # Tell GUI the download started
            self.web.add_request(self.web.REQUEST_STARTED, path, {
                'id': download_id}
            )

            dirname = os.path.dirname(self.web.download_filename)
            basename = os.path.basename(self.web.download_filename)

            def generate():
                # The user hasn't canceled the download
                self.web.client_cancel = False

                # Starting a new download
                if not self.web.stay_open:
                    self.web.download_in_progress = True

                chunk_size = 102400  # 100kb

                fp = open(self.web.download_filename, 'rb')
                self.web.done = False
                canceled = False
                while not self.web.done:
                    # The user has canceled the download, so stop serving the file
                    if self.web.client_cancel:
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
                            percent = (1.0 * downloaded_bytes / self.web.download_filesize) * 100

                            # only output to stdout if running onionshare in CLI mode, or if using Linux (#203, #304)
                            if not self.web.is_gui or self.web.common.platform == 'Linux' or self.web.common.platform == 'BSD':
                                sys.stdout.write(
                                    "\r{0:s}, {1:.2f}%          ".format(self.web.common.human_readable_filesize(downloaded_bytes), percent))
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

                if self.web.common.platform != 'Darwin':
                    sys.stdout.write("\n")

                # Download is finished
                if not self.web.stay_open:
                    self.web.download_in_progress = False

                # Close the server, if necessary
                if not self.web.stay_open and not canceled:
                    print(strings._("closing_automatically"))
                    self.web.running = False
                    try:
                        if shutdown_func is None:
                            raise RuntimeError('Not running with the Werkzeug Server')
                        shutdown_func()
                    except:
                        pass

            r = Response(generate())
            r.headers.set('Content-Length', self.web.download_filesize)
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
        self.web.common.log("Web", "set_file_info")
        self.web.cancel_compression = False

        # build file info list
        self.web.file_info = {'files': [], 'dirs': []}
        for filename in filenames:
            info = {
                'filename': filename,
                'basename': os.path.basename(filename.rstrip('/'))
            }
            if os.path.isfile(filename):
                info['size'] = os.path.getsize(filename)
                info['size_human'] = self.web.common.human_readable_filesize(info['size'])
                self.web.file_info['files'].append(info)
            if os.path.isdir(filename):
                info['size'] = self.web.common.dir_size(filename)
                info['size_human'] = self.web.common.human_readable_filesize(info['size'])
                self.web.file_info['dirs'].append(info)
        self.web.file_info['files'] = sorted(self.web.file_info['files'], key=lambda k: k['basename'])
        self.web.file_info['dirs'] = sorted(self.web.file_info['dirs'], key=lambda k: k['basename'])

        # Check if there's only 1 file and no folders
        if len(self.web.file_info['files']) == 1 and len(self.web.file_info['dirs']) == 0:
            self.web.is_zipped = False
            self.web.download_filename = self.web.file_info['files'][0]['filename']
            self.web.download_filesize = self.web.file_info['files'][0]['size']
        else:
            # Zip up the files and folders
            self.web.zip_writer = ZipWriter(self.web.common, processed_size_callback=processed_size_callback)
            self.web.download_filename = self.web.zip_writer.zip_filename
            for info in self.web.file_info['files']:
                self.web.zip_writer.add_file(info['filename'])
                # Canceling early?
                if self.web.cancel_compression:
                    self.web.zip_writer.close()
                    return False

            for info in self.web.file_info['dirs']:
                if not self.web.zip_writer.add_dir(info['filename']):
                    return False

            self.web.zip_writer.close()
            self.web.download_filesize = os.path.getsize(self.web.download_filename)
            self.web.is_zipped = True

        return True


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
