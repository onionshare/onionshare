import os
import subprocess
import sys

from onionshare.instance_lock import acquire_flatpak_lock


def test_flatpak_lock_reclaims_stale_reused_pid(tmp_path):
    lock_filename = tmp_path / "lock"
    lock_filename.write_text(f"{os.getpid()}\n")

    lock_file, existing_pid = acquire_flatpak_lock(str(lock_filename))
    try:
        assert lock_file is not None
        assert existing_pid is None
        assert lock_filename.read_text() == f"{os.getpid()}\n"
    finally:
        lock_file.close()


def test_flatpak_lock_blocks_live_instance_and_recovers_after_release(tmp_path):
    lock_filename = tmp_path / "lock"

    first_lock, existing_pid = acquire_flatpak_lock(str(lock_filename))
    assert first_lock is not None
    assert existing_pid is None

    second_lock, existing_pid = acquire_flatpak_lock(str(lock_filename))
    assert second_lock is None
    assert existing_pid == str(os.getpid())

    first_lock.close()

    recovered_lock, existing_pid = acquire_flatpak_lock(str(lock_filename))
    try:
        assert recovered_lock is not None
        assert existing_pid is None
    finally:
        recovered_lock.close()


def test_flatpak_lock_recovers_after_holder_is_killed(tmp_path):
    lock_filename = tmp_path / "lock"
    child_code = """
import sys
import time

from onionshare.instance_lock import acquire_flatpak_lock

lock_file, existing_pid = acquire_flatpak_lock(sys.argv[1])
assert lock_file is not None
assert existing_pid is None
print("locked", flush=True)
time.sleep(30)
"""

    holder = subprocess.Popen(
        [sys.executable, "-c", child_code, str(lock_filename)],
        stdout=subprocess.PIPE,
        text=True,
    )

    try:
        assert holder.stdout.readline().strip() == "locked"

        blocked_lock, existing_pid = acquire_flatpak_lock(str(lock_filename))
        assert blocked_lock is None
        assert existing_pid == str(holder.pid)

        holder.kill()
        holder.wait(timeout=5)

        recovered_lock, existing_pid = acquire_flatpak_lock(str(lock_filename))
        try:
            assert recovered_lock is not None
            assert existing_pid is None
        finally:
            recovered_lock.close()
    finally:
        if holder.poll() is None:
            holder.kill()
            holder.wait(timeout=5)
