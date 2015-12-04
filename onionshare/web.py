# -*- coding: utf-8 -*-
"""
OnionShare | https://onionshare.org/

Copyright (C) 2015 Micah Lee <micah@micahflee.com>

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
import Queue, mimetypes, platform, os, sys, urllib2
from flask import Flask, Response, request, render_template_string, abort
from functools import wraps
import strings, helpers

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
q = Queue.Queue()


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


slug = helpers.random_string(16)
download_count = 0

stay_open = False
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

def check_slug_candidate(slug):
    def slug_dec(f):
        @wraps(f)
        def slug_wrapper(slug_candidate, *args, **kwargs):
            if not helpers.constant_time_compare(slug.encode('ascii'),slug_candidate.encode('ascii')):
                abort(404)
            return f(*args, **kwargs)
        return slug_wrapper
    return slug_dec


@app.route("/<slug_candidate>")
@check_slug_candidate(slug)
def index():
    """
    Render the template for the onionshare landing page.
    """
    add_request(REQUEST_LOAD, request.path)
    return render_template_string(
        open(helpers.get_html_path('index.html')).read(),
        slug=slug,
        file_info=file_info,
        filename=os.path.basename(zip_filename).decode("utf-8"),
        filesize=zip_filesize,
        filesize_human=helpers.human_readable_filesize(zip_filesize)
    )


@app.route("/<slug_candidate>/download")
@check_slug_candidate(slug)
def download():
    """
    Download the zip file.
    """
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
        chunk_size = 102400  # 100kb

        fp = open(zip_filename, 'rb')
        done = False
        canceled = False
        while not done:
            chunk = fp.read(chunk_size)
            if chunk == '':
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

        # download is finished, close the server
        if not stay_open and not canceled:
            print strings._("closing_automatically")
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
    return render_template_string(open(helpers.get_html_path('404.html')).read())

# shutting down the server only works within the context of flask, so the easiest way to do it is over http
shutdown_slug = helpers.random_string(16)


@app.route("/<slug_candidate>/shutdown")
@check_slug_candidate(shutdown_slug)
def shutdown():
    """
    Stop the flask web server.
    """
    # shutdown the flask service
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

    return ""


def start(port, stay_open=False, transparent_torification=False):
    """
    Start the flask web server.
    """
    set_stay_open(stay_open)
    set_transparent_torification(transparent_torification)
    app.run(port=port, threaded=True)


def stop(port):
    """
    Stop the flask web server by loading /shutdown.
    """
    # to stop flask, load http://127.0.0.1:<port>/<shutdown_slug>/shutdown
    if transparent_torification:
        import socket

        s = socket.socket()
        s.connect(('127.0.0.1', port))
        s.sendall('GET /{0:s}/shutdown HTTP/1.1\r\n\r\n'.format(shutdown_slug))
    else:
        urllib2.urlopen('http://127.0.0.1:{0:d}/{1:s}/shutdown'.format(port, shutdown_slug)).read()
