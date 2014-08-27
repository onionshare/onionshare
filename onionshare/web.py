import Queue, mimetypes, platform, os, sys
from flask import Flask, Response, request, render_template_string, abort

import strings, helpers

app = Flask(__name__)

# information about the file
filename = filesize = filehash = None
def set_file_info(new_filename, new_filehash, new_filesize):
    global filename, filehash, filesize
    filename = new_filename
    filehash = new_filehash
    filesize = new_filesize

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
        filename=os.path.basename(filename).decode("utf-8"),
        filehash=filehash,
        filesize=filesize,
        filesize_human=helpers.human_readable_filesize(filesize),
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

    dirname = os.path.dirname(filename)
    basename = os.path.basename(filename)

    def generate():
        chunk_size = 102400 # 100kb

        fp = open(filename, 'rb')
        done = False
        while not done:
            chunk = fp.read(102400)
            if chunk == '':
                done = True
            else:
                yield chunk

                # tell GUI the progress
                downloaded_bytes = fp.tell()
                percent = round((1.0 * downloaded_bytes / filesize) * 100, 2);
                sys.stdout.write("\r{0}, {1}%          ".format(helpers.human_readable_filesize(downloaded_bytes), percent))
                sys.stdout.flush()
                add_request(REQUEST_PROGRESS, path, { 'id':download_id, 'bytes':downloaded_bytes })

        fp.close()
        sys.stdout.write("\n")

        # download is finished, close the server
        if not stay_open:
            print strings._("closing_automatically")
            if shutdown_func is None:
                raise RuntimeError('Not running with the Werkzeug Server')
            shutdown_func()

    r = Response(generate())
    r.headers.add('Content-Length', filesize)
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

def start(port, stay_open=False):
    set_stay_open(stay_open)
    app.run(port=port)
