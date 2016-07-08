# -*- coding: utf-8 -*-
"""
OnionShare | https://onionshare.org/

Copyright (C) 2016 Micah Lee <micah@micahflee.com>

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
import queue, mimetypes, platform, os, sys
from urllib.request import urlopen
from flask import Flask, Response, request, render_template_string, abort

from . import strings, helpers

app = Flask(__name__)

# information about the file
file_info = []
zip_filename = None
zip_filesize = None


def set_file_info(filenames):
    """
    Using the list of filenames being shared, fill in details that the web
    page will need to display. This includes zipping up the file in order to
    get the zip file's name and size.
    """
    global file_info, zip_filename, zip_filesize

    # build file info list
    file_info = {'files': [], 'dirs': []}
    for filename in filenames:
        info = {
            'filename': filename,
            'basename': os.path.basename(filename.rstrip('/'))
        }
        if os.path.isfile(filename):
            info['size'] = os.path.getsize(filename)
            info['size_human'] = helpers.human_readable_filesize(info['size'])
            file_info['files'].append(info)
        if os.path.isdir(filename):
            info['size'] = helpers.dir_size(filename)
            info['size_human'] = helpers.human_readable_filesize(info['size'])
            file_info['dirs'].append(info)
    file_info['files'] = sorted(file_info['files'], key=lambda k: k['basename'])
    file_info['dirs'] = sorted(file_info['dirs'], key=lambda k: k['basename'])

    # zip up the files and folders
    z = helpers.ZipWriter()
    for info in file_info['files']:
        z.add_file(info['filename'])
    for info in file_info['dirs']:
        z.add_dir(info['filename'])
    z.close()
    zip_filename = z.zip_filename
    zip_filesize = os.path.getsize(zip_filename)


REQUEST_LOAD = 0
REQUEST_DOWNLOAD = 1
REQUEST_PROGRESS = 2
REQUEST_OTHER = 3
REQUEST_CANCELED = 4
REQUEST_RATE_LIMIT = 4
q = queue.Queue()


def add_request(request_type, path, data=None):
    """
    Add a request to the queue, to communicate with the GUI.
    """
    global q
    q.put({
        'type': request_type,
        'path': path,
        'data': data
    })


slug = None
def generate_slug():
    global slug
    slug = helpers.build_slug()

download_count = 0
error404_count = 0

stay_open = 0
def set_stay_open(new_stay_open):
    """
    Set stay_open variable.
    """
    global stay_open
    stay_open = new_stay_open
def get_stay_open():
    """
    Get stay_open variable.
    """
    return stay_open

transparent_torification = False
def set_transparent_torification(new_transparent_torification):
    """
    Set transparent_torification variable.
    """
    global transparent_torification
    stay_open = new_transparent_torification
def get_transparent_torification():
    """
    Get transparent_torification variable."
    """
    return transparent_torification

def debug_mode():
    """
    Turn on debugging mode, which will log flask errors to a debug file.
    """
    import logging

    if platform.system() == 'Windows':
        temp_dir = os.environ['Temp'].replace('\\', '/')
    else:
        temp_dir = '/tmp/'

    log_handler = logging.FileHandler('{0:s}/onionshare_server.log'.format(temp_dir))
    log_handler.setLevel(logging.WARNING)
    app.logger.addHandler(log_handler)

def check_slug_candidate(slug_candidate, slug_compare = None):
    global slug
    if not slug_compare:
        slug_compare = slug
    if not helpers.constant_time_compare(slug_compare.encode('ascii'), slug_candidate.encode('ascii')):
        abort(404)


# If "Stop sharing automatically" is checked (stay_open == False), only allow
# one download at a time.
download_in_progress = False

@app.route("/<slug_candidate>")
def index(slug_candidate):
    """
    Render the template for the onionshare landing page.
    """
    check_slug_candidate(slug_candidate)

    add_request(REQUEST_LOAD, request.path)

    # Deny new downloads if "Stop sharing automatically" is checked and there is
    # currently a download
    global stay_open, download_in_progress
    deny_download = (stay_open == 0) and download_in_progress
    if deny_download:
        return render_template_string(open(helpers.get_resource_path('html/denied.html')).read())

    # If download is allowed to continue, serve download page
    return render_template_string(
        open(helpers.get_resource_path('html/index.html')).read(),
        slug=slug,
        file_info=file_info,
        filename=os.path.basename(zip_filename),
        filesize=zip_filesize,
        filesize_human=helpers.human_readable_filesize(zip_filesize))

# If the client closes the OnionShare window while a download is in progress,
# it should immediately stop serving the file. The client_cancel global is
# used to tell the download function that the client is canceling the download.
client_cancel = False

@app.route("/<slug_candidate>/download")
def download(slug_candidate):
    """
    Download the zip file.
    """
    check_slug_candidate(slug_candidate)

    # Deny new downloads if "Stop sharing automatically" is checked and there is
    # currently a download
    global stay_open, download_in_progress
    deny_download = not stay_open and download_in_progress
    if deny_download:
        return render_template_string(open(helpers.get_resource_path('html/denied.html')).read())

    global download_count

    # each download has a unique id
    download_id = download_count
    download_count += 1

    # prepare some variables to use inside generate() function below
    # which is outside of the request context
    shutdown_func = request.environ.get('werkzeug.server.shutdown')
    path = request.path

    # tell GUI the download started
    add_request(REQUEST_DOWNLOAD, path, {'id': download_id})

    dirname = os.path.dirname(zip_filename)
    basename = os.path.basename(zip_filename)

    def generate():
        # The user hasn't canceled the download
        global client_cancel
        client_cancel = False

        # Starting a new download
        global stay_open, download_in_progress
        if not stay_open:
            download_in_progress = True

        chunk_size = 102400  # 100kb

        fp = open(zip_filename, 'rb')
        done = False
        canceled = False
        while not done:
            # The user has canceled the download, so stop serving the file
            if client_cancel:
                add_request(REQUEST_CANCELED, path, {'id': download_id})
                break

            chunk = fp.read(chunk_size)
            if chunk == b'':
                done = True
            else:
                try:
                    yield chunk

                    # tell GUI the progress
                    downloaded_bytes = fp.tell()
                    percent = (1.0 * downloaded_bytes / zip_filesize) * 100

                    # suppress stdout platform on OSX (#203)
                    if helpers.get_platform() != 'Darwin':
                        sys.stdout.write(
                            "\r{0:s}, {1:.2f}%          ".format(helpers.human_readable_filesize(downloaded_bytes), percent))
                        sys.stdout.flush()

                    add_request(REQUEST_PROGRESS, path, {'id': download_id, 'bytes': downloaded_bytes})
                except:
                    # looks like the download was canceled
                    done = True
                    canceled = True

                    # tell the GUI the download has canceled
                    add_request(REQUEST_CANCELED, path, {'id': download_id})

        fp.close()

        if helpers.get_platform() != 'Darwin':
            sys.stdout.write("\n")

        # Download is finished
        if not stay_open:
            download_in_progress = False

        # Close the server, if necessary
        if (stay_open == 0) and not canceled:
            print(strings._("closing_automatically"))
            if shutdown_func is None:
                raise RuntimeError('Not running with the Werkzeug Server')
            shutdown_func()

    r = Response(generate())
    r.headers.add('Content-Length', zip_filesize)
    r.headers.add('Content-Disposition', 'attachment', filename=basename)

    # guess content type
    (content_type, _) = mimetypes.guess_type(basename, strict=False)
    if content_type is not None:
        r.headers.add('Content-Type', content_type)
    return r


@app.errorhandler(404)
def page_not_found(e):
    """
    404 error page.
    """
    add_request(REQUEST_OTHER, request.path)

    global error404_count
    if request.path != '/favicon.ico':
        error404_count += 1
        if error404_count == 20:
            add_request(REQUEST_RATE_LIMIT, request.path)
            force_shutdown()
            print(strings._('error_rate_limit'))

    return render_template_string(open(helpers.get_resource_path('html/404.html')).read())

# shutting down the server only works within the context of flask, so the easiest way to do it is over http
shutdown_slug = helpers.random_string(16)


@app.route("/<slug_candidate>/shutdown")
def shutdown(slug_candidate):
    """
    Stop the flask web server, from the context of an http request.
    """
    check_slug_candidate(slug_candidate, shutdown_slug)
    force_shutdown()
    return ""


def force_shutdown():
    """
    Stop the flask web server, from the context of the flask app.
    """
    # shutdown the flask service
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()


def start(port, stay_open=0, transparent_torification=False):
    """
    Start the flask web server.
    """
    generate_slug()

    set_stay_open(stay_open)
    set_transparent_torification(transparent_torification)
    app.run(port=port, threaded=True)


def stop(port):
    """
    Stop the flask web server by loading /shutdown.
    """

    # If the user cancels the download, let the download function know to stop
    # serving the file
    global client_cancel
    client_cancel = True

    # to stop flask, load http://127.0.0.1:<port>/<shutdown_slug>/shutdown
    try:
        if transparent_torification:
            import socket

            s = socket.socket()
            s.connect(('127.0.0.1', port))
            s.sendall('GET /{0:s}/shutdown HTTP/1.1\r\n\r\n'.format(shutdown_slug))
        else:
            urlopen('http://127.0.0.1:{0:d}/{1:s}/shutdown'.format(port, shutdown_slug)).read()
    except:
        pass
