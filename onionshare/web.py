import Queue, mimetypes, platform, os, sys, zipfile
from flask import Flask, Response, request, render_template_string, abort

import strings, helpers

app = Flask(__name__)

# information about the file
file_info = []
zip_filename = None
zip_filesize = None
def set_file_info(filenames):
    global file_info, zip_filename, zip_filesize

    # build file info list
    file_info = {'files':[], 'dirs':[]}
    for filename in filenames:
        info = {
            'filename': filename,
            'basename': os.path.basename(filename)
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
q = Queue.Queue()

def add_request(type, path, data=None):
    global q
    q.put({
      'type': type,
      'path': path,
      'data': data
    })

slug = helpers.random_string(16)
download_count = 0

stay_open = False
def set_stay_open(new_stay_open):
    global stay_open
    stay_open = new_stay_open
def get_stay_open():
    return stay_open

gui_mode = False
def set_gui_mode(new_gui_mode):
    global gui_mode
    gui_mode = new_gui_mode
def get_gui_mode():
    return gui_mode



def debug_mode():
    import logging

    if platform.system() == 'Windows':
        temp_dir = os.environ['Temp'].replace('\\', '/')
    else:
        temp_dir = '/tmp/'

    log_handler = logging.FileHandler('{0}/onionshare_server.log'.format(temp_dir))
    log_handler.setLevel(logging.WARNING)
    app.logger.addHandler(log_handler)

@app.route("/<slug_candidate>")
def index(slug_candidate):
    if not helpers.constant_time_compare(slug.encode('ascii'), slug_candidate.encode('ascii')):
        abort(404)

    add_request(REQUEST_LOAD, request.path)
    return render_template_string(
        open('{0}/index.html'.format(helpers.get_onionshare_dir())).read(),
        slug=slug,
        file_info=file_info,
        filename=os.path.basename(zip_filename).decode("utf-8"),
        filesize=zip_filesize,
        filesize_human=helpers.human_readable_filesize(zip_filesize),
        strings=strings.strings
    )

@app.route("/<slug_candidate>/download")
def download(slug_candidate):
    global download_count
    if not helpers.constant_time_compare(slug.encode('ascii'), slug_candidate.encode('ascii')):
        abort(404)

    # each download has a unique id
    download_id = download_count
    download_count += 1

    # prepare some variables to use inside generate() function below
    # which is outsie of the request context
    shutdown_func = request.environ.get('werkzeug.server.shutdown')
    path = request.path

    # tell GUI the download started
    add_request(REQUEST_DOWNLOAD, path, { 'id':download_id })

    dirname = os.path.dirname(zip_filename)
    basename = os.path.basename(zip_filename)

    def generate():
        chunk_size = 102400 # 100kb

        fp = open(zip_filename, 'rb')
        done = False
        while not done:
            chunk = fp.read(102400)
            if chunk == '':
                done = True
            else:
                yield chunk

                # tell GUI the progress
                downloaded_bytes = fp.tell()
                percent = round((1.0 * downloaded_bytes / zip_filesize) * 100, 2);
                sys.stdout.write("\r{0}, {1}%          ".format(helpers.human_readable_filesize(downloaded_bytes), percent))
                sys.stdout.flush()
                add_request(REQUEST_PROGRESS, path, { 'id':download_id, 'bytes':downloaded_bytes })

        fp.close()
        sys.stdout.write("\n")

        # download is finished, close the server
        if not stay_open:
            if not gui_mode:
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
    add_request(REQUEST_OTHER, request.path)
    return render_template_string(open('{0}/404.html'.format(helpers.get_onionshare_dir())).read())

# shutting down the server only works within the context of flask, so the easiest way to do it is over http
shutdown_slug = helpers.random_string(16)
@app.route("/<shutdown_slug_candidate>/shutdown")
def shutdown(shutdown_slug_candidate):
    if not helpers.constant_time_compare(shutdown_slug.encode('ascii'), shutdown_slug_candidate.encode('ascii')):
        abort(404)
    
    # shutdown the flask service
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

    return ""

def start(port, stay_open=False, gui_mode=False):
    set_stay_open(stay_open)
    set_gui_mode(gui_mode)
    app.run(port=port)

