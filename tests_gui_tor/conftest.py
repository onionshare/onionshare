import sys
# Force tests to look for resources in the source code tree
sys.onionshare_dev_mode = True

import os
import shutil
import tempfile

import pytest

from onionshare import common, web, settings, strings

@pytest.fixture
def temp_dir_1024():
    """ Create a temporary directory that has a single file of a
    particular size (1024 bytes).
    """

    tmp_dir = tempfile.mkdtemp()
    tmp_file, tmp_file_path = tempfile.mkstemp(dir=tmp_dir)
    with open(tmp_file, 'wb') as f:
        f.write(b'*' * 1024)
    return tmp_dir


# pytest > 2.9 only needs @pytest.fixture
@pytest.yield_fixture
def temp_dir_1024_delete():
    """ Create a temporary directory that has a single file of a
    particular size (1024 bytes). The temporary directory (including
    the file inside) will be deleted after fixture usage.
    """

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_file, tmp_file_path = tempfile.mkstemp(dir=tmp_dir)
        with open(tmp_file, 'wb') as f:
            f.write(b'*' * 1024)
        yield tmp_dir


@pytest.fixture
def temp_file_1024():
    """ Create a temporary file of a particular size (1024 bytes). """

    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(b'*' * 1024)
    return tmp_file.name


# pytest > 2.9 only needs @pytest.fixture
@pytest.yield_fixture
def temp_file_1024_delete():
    """
    Create a temporary file of a particular size (1024 bytes).
    The temporary file will be deleted after fixture usage.
    """

    with tempfile.NamedTemporaryFile() as tmp_file:
        tmp_file.write(b'*' * 1024)
        tmp_file.flush()
        yield tmp_file.name


# pytest > 2.9 only needs @pytest.fixture
@pytest.yield_fixture(scope='session')
def custom_zw():
    zw = web.share_mode.ZipWriter(
        common.Common(),
        zip_filename=common.Common.random_string(4, 6),
        processed_size_callback=lambda _: 'custom_callback'
    )
    yield zw
    zw.close()
    os.remove(zw.zip_filename)


# pytest > 2.9 only needs @pytest.fixture
@pytest.yield_fixture(scope='session')
def default_zw():
    zw = web.share_mode.ZipWriter(common.Common())
    yield zw
    zw.close()
    tmp_dir = os.path.dirname(zw.zip_filename)
    shutil.rmtree(tmp_dir)


@pytest.fixture
def locale_en(monkeypatch):
    monkeypatch.setattr('locale.getdefaultlocale', lambda: ('en_US', 'UTF-8'))


@pytest.fixture
def locale_fr(monkeypatch):
    monkeypatch.setattr('locale.getdefaultlocale', lambda: ('fr_FR', 'UTF-8'))


@pytest.fixture
def locale_invalid(monkeypatch):
    monkeypatch.setattr('locale.getdefaultlocale', lambda: ('xx_XX', 'UTF-8'))


@pytest.fixture
def locale_ru(monkeypatch):
    monkeypatch.setattr('locale.getdefaultlocale', lambda: ('ru_RU', 'UTF-8'))


@pytest.fixture
def platform_darwin(monkeypatch):
    monkeypatch.setattr('platform.system', lambda: 'Darwin')


@pytest.fixture  # (scope="session")
def platform_linux(monkeypatch):
    monkeypatch.setattr('platform.system', lambda: 'Linux')


@pytest.fixture
def platform_windows(monkeypatch):
    monkeypatch.setattr('platform.system', lambda: 'Windows')


@pytest.fixture
def sys_argv_sys_prefix(monkeypatch):
    monkeypatch.setattr('sys.argv', [sys.prefix])


@pytest.fixture
def sys_frozen(monkeypatch):
    monkeypatch.setattr('sys.frozen', True, raising=False)


@pytest.fixture
def sys_meipass(monkeypatch):
    monkeypatch.setattr(
        'sys._MEIPASS', os.path.expanduser('~'), raising=False)


@pytest.fixture  # (scope="session")
def sys_onionshare_dev_mode(monkeypatch):
    monkeypatch.setattr('sys.onionshare_dev_mode', True, raising=False)


@pytest.fixture
def time_time_100(monkeypatch):
    monkeypatch.setattr('time.time', lambda: 100)


@pytest.fixture
def time_strftime(monkeypatch):
    monkeypatch.setattr('time.strftime', lambda _: 'Jun 06 2013 11:05:00')

@pytest.fixture
def common_obj():
    _common = common.Common()
    _common.settings = settings.Settings(_common)
    strings.load_strings(_common)
    return _common

@pytest.fixture
def settings_obj(sys_onionshare_dev_mode, platform_linux):
    _common = common.Common()
    _common.version = 'DUMMY_VERSION_1.2.3'
    return settings.Settings(_common)
