#!/usr/bin/env python3
import os
import inspect
import subprocess
import argparse
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
    if os.path.exists(os.path.join(desktop_dir, "windows")):
        shutil.rmtree(os.path.join(desktop_dir, "windows"))

    print("○ Building onionshare-cli")
    run(["poetry", "install"], cli_dir)
    run(["poetry", "build"], cli_dir)
    whl_filename = glob.glob(os.path.join(cli_dir, "dist", "*.whl"))[0]
    whl_basename = os.path.basename(whl_filename)
    shutil.copyfile(whl_filename, os.path.join(desktop_dir, whl_basename))

    print("○ Create the binary")
    run(["briefcase", "create"], desktop_dir)
    run(["briefcase", "package"], desktop_dir)
    msi_filename = glob.glob(os.path.join(desktop_dir, "windows", "OnionShare-*.msi"))[
        0
    ]
    print(f"○ Created unsigned installer: {msi_filename}")

    print(f"○ Signing installer")
    run(
        [
            "signtool.exe",
            "sign",
            "/v",
            "/d",
            "OnionShare",
            "/a",
            "/tr",
            "http://time.certum.pl/",
            msi_filename,
        ],
        desktop_dir,
    )
    print(f"○ Signed installer: {msi_filename}")


if __name__ == "__main__":
    main()