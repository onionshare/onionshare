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
    print(root)
    return
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--with-codesign",
        action="store_true",
        dest="with_codesign",
        help="Codesign the app bundle",
    )
    args = parser.parse_args()

    cli_dir = os.path.join(root, "cli")
    desktop_dir = os.path.join(root, "desktop")

    print("○ Building onionshare-cli")
    run(["poetry", "install"], cli_dir)
    run(["poetry", "build"], cli_dir)
    whl_filename = glob.glob(f"{cli_dir}/dist/*.whl")[0]
    whl_basename = os.path.basename(whl_filename)
    shutil.copyfile(whl_filename, os.path.join(desktop_dir, whl_basename))

    print("○ Clean up from last build")
    if os.path.exists(os.path.join(desktop_dir, "macOS")):
        shutil.rmtree(os.path.join(desktop_dir, "macOS"))

    print("○ Create app bundle")
    run(["briefcase", "create"], desktop_dir)
    app_path = os.path.join(desktop_dir, "macOS", "OnionShare", "OnionShare.app")
    print(f"○ Unsigned app bundle: {app_path}")

    if args.with_codesign:
        identity_name_application = "Developer ID Application: Micah Lee (N9B95FDWH4)"
        entitlements_child_filename = os.path.join(
            desktop_dir, "package", "macos", "ChildEntitlements.plist"
        )
        entitlements_filename = os.path.join(
            desktop_dir, "package", "macos", "Entitlements.plist"
        )

        print("○ Code signing app bundle")
        run(
            [
                "codesign",
                "--deep",
                "-s",
                identity_name_application,
                "--force",
                "--entitlements",
                entitlements_child_filename,
                "--timestamp",
                app_path,
            ]
        )
        run(
            [
                "codesign",
                "-s",
                identity_name_application,
                "--force",
                "--entitlements",
                entitlements_filename,
                "--timestamp",
                app_path,
            ]
        )
        print(f"○ Signed app bundle: {app_path}")

        print("○ TODO: Make a DMG package")


if __name__ == "__main__":
    main()