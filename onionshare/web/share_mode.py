import os
import sys
import tempfile
import zipfile
import mimetypes
from flask import Response, request, render_template, make_response

from .. import strings


def share_routes(web):
    """
    The web app routes for sharing files
    """
    @web.app.route("/<slug_candidate>")
    def index(slug_candidate):
        web.check_slug_candidate(slug_candidate)
        return index_logic()

    @web.app.route("/")
    def index_public():
        if not web.common.settings.get('public_mode'):
            return web.error404()
        return index_logic()

    def index_logic(slug_candidate=''):
        """
        Render the template for the onionshare landing page.
        """
        web.add_request(web.REQUEST_LOAD, request.path)

        # Deny new downloads if "Stop After First Download" is checked and there is
        # currently a download
        deny_download = not web.stay_open and web.download_in_progress
        if deny_download:
            r = make_response(render_template('denied.html'))
            return web.add_security_headers(r)

        # If download is allowed to continue, serve download page
        if web.slug:
            r = make_response(render_template(
                'send.html',
                slug=web.slug,
                file_info=web.file_info,
                filename=os.path.basename(web.download_filename),
                filesize=web.download_filesize,
                filesize_human=web.common.human_readable_filesize(web.download_filesize),
                is_zipped=web.is_zipped))
        else:
            # If download is allowed to continue, serve download page
            r = make_response(render_template(
                'send.html',
                file_info=web.file_info,
                filename=os.path.basename(web.download_filename),
                filesize=web.download_filesize,
                filesize_human=web.common.human_readable_filesize(web.download_filesize),
                is_zipped=web.is_zipped))
        return web.add_security_headers(r)

    @web.app.route("/<slug_candidate>/download")
    def download(slug_candidate):
        web.check_slug_candidate(slug_candidate)
        return download_logic()

    @web.app.route("/download")
    def download_public():
        if not web.common.settings.get('public_mode'):
            return web.error404()
        return download_logic()

    def download_logic(slug_candidate=''):
        """
        Download the zip file.
        """
        # Deny new downloads if "Stop After First Download" is checked and there is
        # currently a download
        deny_download = not web.stay_open and web.download_in_progress
        if deny_download:
            r = make_response(render_template('denied.html'))
            return web.add_security_headers(r)

        # Each download has a unique id
        download_id = web.download_count
        web.download_count += 1

        # Prepare some variables to use inside generate() function below
        # which is outside of the request context
        shutdown_func = request.environ.get('werkzeug.server.shutdown')
        path = request.path

        # Tell GUI the download started
        web.add_request(web.REQUEST_STARTED, path, {
            'id': download_id}
        )

        dirname = os.path.dirname(web.download_filename)
        basename = os.path.basename(web.download_filename)

        def generate():
            # The user hasn't canceled the download
            web.client_cancel = False

            # Starting a new download
            if not web.stay_open:
                web.download_in_progress = True

            chunk_size = 102400  # 100kb

            fp = open(web.download_filename, 'rb')
            web.done = False
            canceled = False
            while not web.done:
                # The user has canceled the download, so stop serving the file
                if web.client_cancel:
                    web.add_request(web.REQUEST_CANCELED, path, {
                        'id': download_id
                    })
                    break

                chunk = fp.read(chunk_size)
                if chunk == b'':
                    web.done = True
                else:
                    try:
                        yield chunk

                        # tell GUI the progress
                        downloaded_bytes = fp.tell()
                        percent = (1.0 * downloaded_bytes / web.download_filesize) * 100

                        # only output to stdout if running onionshare in CLI mode, or if using Linux (#203, #304)
                        if not web.gui_mode or web.common.platform == 'Linux' or web.common.platform == 'BSD':
                            sys.stdout.write(
                                "\r{0:s}, {1:.2f}%          ".format(web.common.human_readable_filesize(downloaded_bytes), percent))
                            sys.stdout.flush()

                        web.add_request(web.REQUEST_PROGRESS, path, {
                            'id': download_id,
                            'bytes': downloaded_bytes
                            })
                        web.done = False
                    except:
                        # looks like the download was canceled
                        web.done = True
                        canceled = True

                        # tell the GUI the download has canceled
                        web.add_request(web.REQUEST_CANCELED, path, {
                            'id': download_id
                        })

            fp.close()

            if web.common.platform != 'Darwin':
                sys.stdout.write("\n")

            # Download is finished
            if not web.stay_open:
                web.download_in_progress = False

            # Close the server, if necessary
            if not web.stay_open and not canceled:
                print(strings._("closing_automatically"))
                web.running = False
                try:
                    if shutdown_func is None:
                        raise RuntimeError('Not running with the Werkzeug Server')
                    shutdown_func()
                except:
                    pass

        r = Response(generate())
        r.headers.set('Content-Length', web.download_filesize)
        r.headers.set('Content-Disposition', 'attachment', filename=basename)
        r = web.add_security_headers(r)
        # guess content type
        (content_type, _) = mimetypes.guess_type(basename, strict=False)
        if content_type is not None:
            r.headers.set('Content-Type', content_type)
        return r


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
