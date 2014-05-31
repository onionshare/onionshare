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

def test_get_hidden_service_dir_windows_with_temp():
    """
    get_hidden_service_dir() uses a temporary directory from the
    Windows environment when defined
    """
    onionshare.get_platform = lambda: 'Windows'
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
