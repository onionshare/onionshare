"""
Tests that the output of the subprocesses OnionShare starts (tor, meek-client)
is always drained. A child process that writes to a pipe nobody reads blocks
once the pipe is full. For tor that also freezes its control port, which hangs
every stem call, and with it the GUI. The pipe holds ~4 KiB on Windows, which is
why built-in obfs4 bridges froze OnionShare there.
"""

import os
import subprocess
import sys
import textwrap
import threading

import pytest

from onionshare_cli.meek import Meek, MeekNotRunning

# More than any OS's default pipe buffer (4 KiB on Windows, 64 KiB on Linux)
FLOOD_BYTES = 512 * 1024

needs_posix = pytest.mark.skipif(
    sys.platform == "win32",
    reason="the fake meek-client is a script, and Windows needs an .exe",
)


def run_with_timeout(func, timeout=20):
    """
    Run func in a thread, so a regression shows up as a test failure
    instead of hanging the test suite forever.
    """
    result = {}

    def target():
        try:
            result["value"] = func()
        except Exception as e:
            result["error"] = e

    t = threading.Thread(target=target, daemon=True)
    t.start()
    t.join(timeout)
    assert not t.is_alive(), f"timed out after {timeout}s"
    if "error" in result:
        raise result["error"]
    return result.get("value")


def write_fake_meek_client(tmp_path, body):
    path = tmp_path / "meek-client"
    path.write_text(f"#!{sys.executable}\n" + textwrap.dedent(body))
    path.chmod(0o755)
    return str(path)


def fake_tor_paths(meek_client_path):
    return lambda: (None, None, None, None, None, meek_client_path, None)


class TestDrainSubprocessOutput:
    def test_child_flooding_its_pipe_can_exit(self, common_obj):
        logged = []
        common_obj.log = lambda module, func, msg=None: logged.append(msg)

        code = (
            "import sys\n"
            f"for i in range({FLOOD_BYTES} // 64):\n"
            "    print('x' * 63)\n"
            "    print('y' * 63, file=sys.stderr)\n"
            "print('last line')\n"
        )
        proc = subprocess.Popen(
            [sys.executable, "-c", code],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        thread = common_obj.drain_subprocess_output(proc.stdout, "Test")

        # Without draining, the child blocks on a full pipe and never exits
        assert proc.wait(timeout=20) == 0
        thread.join(timeout=10)
        assert not thread.is_alive()
        assert logged[-1] == "last line"
        assert len(logged) == 2 * (FLOOD_BYTES // 64) + 1

    def test_text_mode_pipe(self, common_obj):
        logged = []
        common_obj.log = lambda module, func, msg=None: logged.append(msg)

        proc = subprocess.Popen(
            [sys.executable, "-c", "print('hello'); print(''); print('world')"],
            stdout=subprocess.PIPE,
            universal_newlines=True,
        )
        thread = common_obj.drain_subprocess_output(proc.stdout, "Test")
        assert proc.wait(timeout=20) == 0
        thread.join(timeout=10)
        # Blank lines are skipped, and lines arrive as str without newlines
        assert logged == ["hello", "world"]


@needs_posix
class TestMeekStart:
    def test_client_exiting_without_a_port_raises(self, common_obj, tmp_path):
        meek_client = write_fake_meek_client(
            tmp_path,
            """
            print("VERSION 1", flush=True)
            """,
        )
        meek = Meek(common_obj, get_tor_paths=fake_tor_paths(meek_client))

        # This used to spin forever: the pipe is in text mode, so readline()
        # returns "" at EOF and never matched the b"" sentinel.
        with pytest.raises(MeekNotRunning):
            run_with_timeout(meek.start)

    def test_client_reporting_cmethod_error_raises(self, common_obj, tmp_path):
        meek_client = write_fake_meek_client(
            tmp_path,
            """
            print("CMETHOD-ERROR meek something went wrong", flush=True)
            import time; time.sleep(30)
            """,
        )
        meek = Meek(common_obj, get_tor_paths=fake_tor_paths(meek_client))

        with pytest.raises(MeekNotRunning):
            run_with_timeout(meek.start)

    def test_chatty_client_does_not_block(self, common_obj, tmp_path):
        # Floods stderr before and after reporting its port, and stdout after.
        # It only exits by itself if OnionShare keeps reading both pipes.
        meek_client = write_fake_meek_client(
            tmp_path,
            f"""
            import sys
            for i in range({FLOOD_BYTES} // 64):
                print("e" * 63, file=sys.stderr)
            print("VERSION 1")
            print("CMETHOD meek socks5 127.0.0.1:12345")
            print("CMETHODS DONE", flush=True)
            for i in range({FLOOD_BYTES} // 64):
                print("e" * 63, file=sys.stderr)
                print("o" * 63)
            """,
        )
        meek = Meek(common_obj, get_tor_paths=fake_tor_paths(meek_client))

        run_with_timeout(meek.start)
        try:
            assert meek.meek_port == "12345"
            assert meek.meek_proxies["https"] == "socks5h://127.0.0.1:12345"
            assert meek.meek_proc.wait(timeout=20) == 0
        finally:
            meek.cleanup()
