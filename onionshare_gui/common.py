import os, inspect, platform

def get_onionshare_gui_dir():
    if platform.system() == 'Darwin':
        onionshare_gui_dir = os.path.dirname(__file__)
    else:
        onionshare_gui_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    return onionshare_gui_dir

onionshare_gui_dir = get_onionshare_gui_dir()
