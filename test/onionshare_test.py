from onionshare import *
import tempfile

def test_get_platform_on_tails():
    "get_platform() returns 'Tails' when hostname is 'amnesia'"
    onionshare.platform.uname = lambda: ('Linux', 'amnesia', '3.14-1-amd64', '#1 SMP Debian 3.14.4-1 (2014-05-13)', 'x86_64', '')
    assert get_platform() == 'Tails'

def test_get_platform_returns_platform_system():
    "get_platform() returns platform.system() when ONIONSHARE_PLATFORM is not defined"
    onionshare.platform.system = lambda: 'Sega Saturn'
    assert get_platform() == 'Sega Saturn'

def test_get_hidden_service_dir_windows_with_temp():
    "get_hidden_service_dir() uses a directory from the Windows environment when defined"
    onionshare.platform.system = lambda: 'Windows'
    os.environ['Temp'] = "C:\Internet Explorer\Secrets"
    expected_path = "C:/Internet Explorer/Secrets/onionshare_hidden_service_port"
    assert get_hidden_service_dir('port') == expected_path

def test_get_hidden_service_dir_windows_default():
    "get_hidden_service_dir() uses C:/tmp by default on Windows"
    onionshare.get_platform = lambda: 'Windows'
    os.environ.pop('Temp', None)
    expected_path = "C:/tmp/onionshare_hidden_service_port"
    assert get_hidden_service_dir('port') == expected_path

def test_get_hidden_service_dir_posix():
    "get_hidden_service_dir() uses /tmp by default on POSIX"
    onionshare.get_platform = lambda: 'Not Windows'
    expected_path = "/tmp/onionshare_hidden_service_port"
    assert get_hidden_service_dir('port') == expected_path

class MockSubprocess():
  def __init__(self):
      self.last_call = None

  def call(self, args):
      self.last_call = args

  def last_call_args(self):
      return self.last_call

def test_tails_open_port():
    "tails_open_port() calls iptables with ACCEPT arg"
    onionshare.get_platform = lambda: 'Tails'
    onionshare.strings = {'punching_a_hole': ''}

    mock_subprocess = MockSubprocess()
    onionshare.subprocess = mock_subprocess
    onionshare.tails_open_port('port')

    expected_call = [
        '/sbin/iptables', '-I', 'OUTPUT',
        '-o', 'lo', '-p',
        'tcp', '--dport', 'port', '-j', 'ACCEPT'
        ]
    actual_call = mock_subprocess.last_call_args()
    assert actual_call == expected_call

def test_tails_close_port():
    "tails_close_port() calls iptables with REJECT arg"
    onionshare.get_platform = lambda: 'Tails'
    onionshare.strings = {'closing_hole': ''}

    mock_subprocess = MockSubprocess()
    onionshare.subprocess = mock_subprocess
    onionshare.tails_close_port('port')

    expected_call = [
        '/sbin/iptables', '-I', 'OUTPUT',
        '-o', 'lo', '-p',
        'tcp', '--dport', 'port', '-j', 'REJECT'
        ]
    actual_call = mock_subprocess.last_call_args()
    assert actual_call == expected_call

def test_load_strings_defaults_to_english():
    "load_strings() loads English by default"
    locale.getdefaultlocale = lambda: ('en_US', 'UTF-8')
    load_strings()
    assert onionshare.strings['calculating_sha1'] == "Calculating SHA1 checksum."

def test_load_strings_loads_other_languages():
    "load_strings() loads other languages in different locales"
    locale.getdefaultlocale = lambda: ('fr_FR', 'UTF-8')
    load_strings("fr")
    assert onionshare.strings['calculating_sha1'] == "Calculer un hachage SHA-1."

def test_generate_slug_length():
    "generates a 32-character slug"
    assert len(slug) == 32

def test_generate_slug_characters():
    "generates a hex slug"

    def is_hex(string):
        hex_alphabet = "01234556789abcdef"
        return all(char in hex_alphabet for char in string)

    assert is_hex(slug)

def test_starts_with_empty_strings():
    "creates an empty strings dict by default"
    assert strings == {}

def test_choose_port_returns_a_port_number():
    "choose_port() returns a port number"
    assert  1024 <= choose_port()  <= 65535

def test_choose_port_returns_an_open_port():
    "choose_port() returns an open port"
    port = choose_port()
    socket.socket().bind(("127.0.0.1", port))

def write_tempfile(text):
    tempdir = tempfile.mkdtemp()
    path = tempdir + "/test-file.txt"
    with open(path, "w") as f:
      f.write(text)
      f.close()
    return path

def test_filehash_returns_correct_hash():
    "file_crunching() returns correct hash"

    text = """
           If you want a picture of the future, imagine a boot stamping on an
           encrypted, redundant, distributed filesystem -- forever.
           """
    tempfile = write_tempfile(text)
    filehash, _ = file_crunching(tempfile)

    assert filehash == 'bc004fe72e6530a545570b4c6ce76bcb78ea526b'

def test_filehash_returns_correct_size():
    "file_crunching() returns correct size"

    text = "AUSCANNZUKUS has always been at war with Eastasia."
    tempfile = write_tempfile(text)
    _, filesize = file_crunching(tempfile)

    assert filesize == 50
