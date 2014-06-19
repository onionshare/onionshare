from flask import Flask, render_template
import threading, json, os, time

onionshare = None
onionshare_port = None
filename = None
onion_host = None
qtapp = None
clipboard = None

url = None

app = Flask(__name__, template_folder='./templates')

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/init_info")
def init_info():
    global onionshare, filename
    basename = os.path.basename(filename)

    return json.dumps({
        'strings': onionshare.strings,
        'basename': basename
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
    global clipboard
    clipboard.setText(url)
    return ''

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

