from flask import Flask, render_template
import threading, json, os, time, platform, sys

onionshare = None
onionshare_port = None
filename = None
onion_host = None
qtapp = None
clipboard = None
stay_open = None
debug = None

url = None

# figure out this platform's temp dir
if platform.system() == 'Windows':
    temp_dir = os.environ['Temp'].replace('\\', '/')
else:
    temp_dir = '/tmp/'

# suppress output in windows
if platform.system() == 'Windows':
    sys.stdout = open('{0}/onionshare.stdout.log'.format(temp_dir), 'w')
    sys.stderr = open('{0}/onionshare.stderr.log'.format(temp_dir), 'w')

# log web errors to file
import logging
log_handler = logging.FileHandler('{0}/onionshare.web.log'.format(temp_dir))
log_handler.setLevel(logging.WARNING)

app = Flask(__name__, template_folder='./templates')
app.logger.addHandler(log_handler)

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/init_info")
def init_info():
    global onionshare, filename, stay_open
    basename = os.path.basename(filename)

    return json.dumps({
        'strings': onionshare.strings,
        'basename': basename,
        'stay_open': stay_open
    })

@app.route("/start_onionshare")
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
def stay_open_true():
    global onionshare
    onionshare.set_stay_open(True)

@app.route("/stay_open_false")
def stay_open_false():
    global onionshare
    onionshare.set_stay_open(False)

@app.route("/heartbeat")
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
def close():
    global qtapp
    time.sleep(1)
    qtapp.closeAllWindows()
    return ''

