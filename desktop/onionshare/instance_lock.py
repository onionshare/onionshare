# -*- coding: utf-8 -*-
"""
OnionShare | https://onionshare.org/

Copyright (C) 2014-2026 Micah Lee, et al. <micah@micahflee.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import os


def acquire_flatpak_lock(lock_filename):
    """Acquire the Flatpak GUI instance lock.

    Flatpak processes can reuse namespace-local PIDs between launches. An
    advisory file lock is owned by the running process instead, and the kernel
    releases it automatically when that process exits or crashes.
    """
    import fcntl

    lock_file = open(lock_filename, "a+")

    try:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        lock_file.seek(0)
        existing_pid = lock_file.read().strip() or "unknown"
        lock_file.close()
        return None, existing_pid

    lock_file.seek(0)
    lock_file.truncate()
    lock_file.write(f"{os.getpid()}\n")
    lock_file.flush()

    return lock_file, None
