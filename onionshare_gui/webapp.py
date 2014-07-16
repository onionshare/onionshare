from flask import Flask, render_template, make_response
from functools import wraps
import threading, json, os, time, platform, sys

onionshare = None
onionshare_port = None
filename = None
onion_host = None
qtapp = None
clipboard = None
stay_open = None

url = None

app = Flask(__name__, template_folder='./templates')

def debug_mode():
    import logging
    global app

    if platform.system() == 'Windows':
        temp_dir = os.environ['Temp'].replace('\\', '/')
    else:
        temp_dir = '/tmp/'

    log_handler = logging.FileHandler('{0}/onionshare_gui.log'.format(temp_dir))
    log_handler.setLevel(logging.WARNING)
    app.logger.addHandler(log_handler)

def add_response_headers(headers={}):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            resp = make_response(f(*args, **kwargs))
            h = resp.headers
            for header, value in headers.items():
                h[header] = value
            return resp
        return decorated_function
    return decorator

def csp(f):
    @wraps(f)
    # disable inline js, external js
    @add_response_headers({'Content-Security-Policy': "default-src 'self'; connect-src 'self'"})
    # ugh, webkit embedded in Qt4 is stupid old
    # TODO: remove webkit, build GUI with normal Qt widgets
    @add_response_headers({'X-WebKit-CSP': "default-src 'self'; connect-src 'self'"})
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated_function

@app.route("/")
@csp
def index():
    return render_template('index.html')

@app.route("/init_info")
@csp
def init_info():
    global onionshare, filename, stay_open
    basename = os.path.basename(filename)

    return json.dumps({
        'strings': onionshare.strings,
        'basename': basename,
        'stay_open': stay_open
    })

@app.route("/start_onionshare")
@csp
def start_onionshare():
    global onionshare, onionshare_port, filename, onion_host, url

    url = 'http://{0}/{1}'.format(onion_host, onionshare.slug)

    filehash, filesize = onionshare.file_crunching(filename)
    onionshare.set_file_info(filename, filehash, filesize)

    # start onionshare service in new thread
    t = threading.Thread(target=onionshare.app.run, kwargs={'port': onionshare_port})
    t.daemon = True
    t.start()

    return json.dumps({
        'filehash': filehash,
        'filesize': filesize,
        'url': url
    })

@app.route("/copy_url")
@csp
def copy_url():
    if platform.system() == 'Windows':
        # Qt's QClipboard isn't working in Windows
        # https://github.com/micahflee/onionshare/issues/46
        import ctypes
        GMEM_DDESHARE = 0x2000
        ctypes.windll.user32.OpenClipboard(None)
        ctypes.windll.user32.EmptyClipboard()
        hcd = ctypes.windll.kernel32.GlobalAlloc(GMEM_DDESHARE, len(bytes(url))+1)
        pch_data = ctypes.windll.kernel32.GlobalLock(hcd)
        ctypes.cdll.msvcrt.strcpy(ctypes.c_char_p(pch_data), bytes(url))
        ctypes.windll.kernel32.GlobalUnlock(hcd)
        ctypes.windll.user32.SetClipboardData(1, hcd)
        ctypes.windll.user32.CloseClipboard()
    else:
        global clipboard
        clipboard.setText(url)
    return ''

@app.route("/stay_open_true")
@csp
def stay_open_true():
    global onionshare
    onionshare.set_stay_open(True)

@app.route("/stay_open_false")
@csp
def stay_open_false():
    global onionshare
    onionshare.set_stay_open(False)

@app.route("/heartbeat")
@csp
def check_for_requests():
    global onionshare
    events = []

    done = False
    while not done:
        try:
            r = onionshare.q.get(False)
            events.append(r)
        except onionshare.Queue.Empty:
            done = True

    return json.dumps(events)

@app.route("/close")
@csp
def close():
    global qtapp
    time.sleep(1)
    qtapp.closeAllWindows()
    return ''

