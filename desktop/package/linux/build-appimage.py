#!/usr/bin/env python3
import os
import inspect
import subprocess
import shutil
import glob

root = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        )
    )
)


def run(cmd, cwd=None):
    subprocess.run(cmd, cwd=cwd, check=True)


def main():
    cli_dir = os.path.join(root, "cli")
    desktop_dir = os.path.join(root, "desktop")

    print("○ Clean up from last build")
    if os.path.exists(os.path.join(cli_dir, "dist")):
        shutil.rmtree(os.path.join(cli_dir, "dist"))
    if os.path.exists(os.path.join(desktop_dir, "linux")):
        shutil.rmtree(os.path.join(desktop_dir, "linux"))

    print("○ Building onionshare-cli")
    run(["poetry", "install"], cli_dir)
    run(["poetry", "build"], cli_dir)
    whl_filename = glob.glob(os.path.join(cli_dir, "dist", "*.whl"))[0]
    whl_basename = os.path.basename(whl_filename)
    shutil.copyfile(whl_filename, os.path.join(desktop_dir, whl_basename))

    print("○ Create the binary")
    run(["briefcase", "create"], desktop_dir)

    print("○ Create the AppImage")
    run(["briefcase", "build"], desktop_dir)


if __name__ == "__main__":
    main()