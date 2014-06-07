from flask import Flask, render_template
import threading, json, os, gtk

onionshare = None
onionshare_port = None
filename = None
onion_host = None

clipboard = gtk.clipboard_get(gtk.gdk.SELECTION_CLIPBOARD)
url = None

app = Flask(__name__, template_folder='./templates')

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/start_onionshare")
def start_onionshare():
    global onionshare, onionshare_port, filename, onion_host, url

    url = 'http://{0}/{1}'.format(onion_host, onionshare.slug)

    basename = os.path.basename(filename)
    filehash, filesize = onionshare.file_crunching(filename)
    onionshare.set_file_info(filename, filehash, filesize)

    # start onionshare service in new thread
    t = threading.Thread(target=onionshare.app.run, kwargs={'port': onionshare_port})
    t.daemon = True
    t.start()

    return json.dumps({
        'strings': onionshare.strings,
        'basename': basename,
        'filehash': filehash,
        'filesize': filesize,
        'url': url
    })

@app.route("/copy_url")
def copy_url():
    global clipboard
    clipboard.set_text(url)
    return ''

