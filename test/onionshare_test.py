from onionshare import *

def test_get_platform_returns_env_var():
    "get_platform() returns ONIONSHARE_PLATFORM from the environment"
    os.environ['ONIONSHARE_PLATFORM'] = 'TI-83+'
    assert get_platform() == 'TI-83+'

def test_get_platform_returns_platform_system():
    """
    get_platform() returns platform.system() when
    ONIONSHARE_PLATFORM is not defined
    """
    os.environ.pop('ONIONSHARE_PLATFORM', None)
    onionshare.platform.system = lambda: 'Sega Saturn'
    assert get_platform() == 'Sega Saturn'

def test_tails_appends_to_path():
    "adds '/../tails/lib' to the path when running on Tails"
    original_path = sys.path
    onionshare.platform.system = lambda: 'Tails'
    append_lib_on_tails()
    assert sys.path[-1][-13:] == '/../tails/lib'

def test_get_hidden_service_dir_windows_with_temp():
    """
    get_hidden_service_dir() uses a temporary directory from the
    Windows environment when defined
    """
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

def test_load_strings_defaults_to_english():
    "load_strings() loads English by default"
    locale.getdefaultlocale = lambda: ('en_US', 'UTF-8')
    load_strings()
    assert onionshare.strings['calculating_sha1'] == "Calculating SHA1 checksum."

def test_load_strings_loads_other_languages():
    "load_strings() loads other languages in different locales"
    locale.getdefaultlocale = lambda: ('fr_FR', 'UTF-8')
    load_strings("fr")
    print onionshare.strings
    assert onionshare.strings['calculating_sha1'] == "Calculer un hachage SHA-1."

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
