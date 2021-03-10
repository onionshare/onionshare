#!/usr/bin/env python3
"""
This script builds the CLI python wheel, copies it to the desktop folder,
and installs it in the virtual environment.
"""

import inspect
import os
import glob
import subprocess
import shutil


def main():
    # Build paths
    root_path = os.path.dirname(
        os.path.dirname(
            os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        )
    )
    cli_path = os.path.join(root_path, "cli")
    desktop_path = os.path.join(root_path, "desktop")

    # Delete old wheels
    for filename in glob.glob(os.path.join(cli_path, "dist", "*.whl")):
        os.remove(filename)

    # Build new wheel
    subprocess.call(["poetry", "install"], cwd=cli_path)
    subprocess.call(["poetry", "build"], cwd=cli_path)
    wheel_filename = glob.glob(os.path.join(cli_path, "dist", "*.whl"))[0]
    wheel_basename = os.path.basename(wheel_filename)
    shutil.copyfile(
        wheel_filename,
        os.path.join(desktop_path, wheel_basename),
    )

    # Reinstall the new wheel
    subprocess.call(["pip", "uninstall", "onionshare-cli", "-y"])
    subprocess.call(["pip", "install", os.path.join(desktop_path, wheel_basename)])


if __name__ == "__main__":
    main()
