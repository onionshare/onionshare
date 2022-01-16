import sys
import os
import shutil
import tempfile

import pytest

from onionshare_cli import common, web

# Force tests to look for resources in the source code tree
sys.onionshare_dev_mode = True

# Let OnionShare know the tests are running, to avoid colliding with settings files
sys.onionshare_test_mode = True

# The temporary directory for CLI tests
test_temp_dir = None


def pytest_addoption(parser):
    parser.addoption(
        "--runtor", action="store_true", default=False, help="run tor tests"
    )


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--runtor"):
        # --runtor given in cli: do not skip tor tests
        skip_tor = pytest.mark.skip(reason="need --runtor option to run")
        for item in items:
            if "tor" in item.keywords:
                item.add_marker(skip_tor)


@pytest.fixture
def temp_dir():
    """Creates a persistent temporary directory for the CLI tests to use"""
    global test_temp_dir
    if not test_temp_dir:
        test_temp_dir = tempfile.TemporaryDirectory()
    return test_temp_dir


@pytest.fixture
def temp_dir_1024(temp_dir):
    """Create a temporary directory that has a single file of a
    particular size (1024 bytes).
    """

    new_temp_dir = tempfile.TemporaryDirectory(dir=temp_dir.name)
    tmp_file = tempfile.NamedTemporaryFile(dir=new_temp_dir.name)
    tmp_file.write(b"*" * 1024)
    return new_temp_dir


@pytest.fixture
def temp_dir_1024_delete(temp_dir):
    """Create a temporary directory that has a single file of a
    particular size (1024 bytes). The temporary directory (including
    the file inside) will be deleted after fixture usage.
    """

    with tempfile.TemporaryDirectory(dir=temp_dir.name) as new_temp_dir:
        with open(os.path.join(new_temp_dir, "file"), "wb") as f:
            f.write(b"*" * 1024)
        yield new_temp_dir


@pytest.fixture
def temp_file_1024(temp_dir):
    """Create a temporary file of a particular size (1024 bytes)."""

    filename = os.path.join(temp_dir.name, "file")
    with open(filename, "wb") as f:
        f.write(b"*" * 1024)
    return filename


@pytest.fixture
def temp_file_1024_delete(temp_dir):
    """
    Create a temporary file of a particular size (1024 bytes).
    The temporary file will be deleted after fixture usage.
    """

    with tempfile.NamedTemporaryFile(dir=temp_dir.name, delete=False) as tmp_file:
        tmp_file.write(b"*" * 1024)
        tmp_file.flush()
        tmp_file.close()
        yield tmp_file


@pytest.fixture(scope="session")
def custom_zw():
    zw = web.share_mode.ZipWriter(
        common.Common(),
        zip_filename=common.Common.random_string(4, 6),
        processed_size_callback=lambda _: "custom_callback",
    )
    yield zw
    zw.close()
    os.remove(zw.zip_filename)


@pytest.fixture(scope="session")
def default_zw():
    zw = web.share_mode.ZipWriter(common.Common())
    yield zw
    zw.close()
    tmp_dir = os.path.dirname(zw.zip_filename)
    try:
        shutil.rmtree(tmp_dir, ignore_errors=True)
    except Exception:
        pass


@pytest.fixture
def locale_en(monkeypatch):
    monkeypatch.setattr("locale.getdefaultlocale", lambda: ("en_US", "UTF-8"))


@pytest.fixture
def locale_fr(monkeypatch):
    monkeypatch.setattr("locale.getdefaultlocale", lambda: ("fr_FR", "UTF-8"))


@pytest.fixture
def locale_invalid(monkeypatch):
    monkeypatch.setattr("locale.getdefaultlocale", lambda: ("xx_XX", "UTF-8"))


@pytest.fixture
def locale_ru(monkeypatch):
    monkeypatch.setattr("locale.getdefaultlocale", lambda: ("ru_RU", "UTF-8"))


@pytest.fixture
def platform_darwin(monkeypatch):
    monkeypatch.setattr("platform.system", lambda: "Darwin")


@pytest.fixture  # (scope="session")
def platform_linux(monkeypatch):
    monkeypatch.setattr("platform.system", lambda: "Linux")


@pytest.fixture
def platform_windows(monkeypatch):
    monkeypatch.setattr("platform.system", lambda: "Windows")


@pytest.fixture
def sys_argv_sys_prefix(monkeypatch):
    monkeypatch.setattr("sys.argv", [sys.prefix])


@pytest.fixture
def sys_frozen(monkeypatch):
    monkeypatch.setattr("sys.frozen", True, raising=False)


@pytest.fixture
def sys_meipass(monkeypatch):
    monkeypatch.setattr("sys._MEIPASS", os.path.expanduser("~"), raising=False)


@pytest.fixture  # (scope="session")
def sys_onionshare_dev_mode(monkeypatch):
    monkeypatch.setattr("sys.onionshare_dev_mode", True, raising=False)


@pytest.fixture
def time_time_100(monkeypatch):
    monkeypatch.setattr("time.time", lambda: 100)


@pytest.fixture
def time_strftime(monkeypatch):
    monkeypatch.setattr("time.strftime", lambda _: "Jun 06 2013 11:05:00")


@pytest.fixture
def common_obj():
    return common.Common()
