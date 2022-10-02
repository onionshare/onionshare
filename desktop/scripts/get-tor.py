#!/usr/bin/env python3
import inspect
import os
from re import M
import sys
import hashlib
import shutil
import subprocess
import requests
import click

torbrowser_version = "11.5.2"
expected_win32_sha256 = (
    "07e721ae76bc7eefe25f20792091009238e9568d500331fc64bdd8796fec8c0f"
)
expected_win64_sha256 = (
    "8237bca22b5fa545de21f84ba8c9270c84442d0fc50a2e626f757d069e4bc7a8"
)
expected_macos_sha256 = (
    "b80d3dba83b343fab7a6c8fc08440b2751da1ac12f86fe593da8e74069e4d7f6"
)
expected_linux64_sha256 = (
    "90cdce3854e9114ee7232aaa74672a2d9f3a40b6fa8ac33971f586ee3a3cf75a"
)

win32_url = f"https://dist.torproject.org/torbrowser/{torbrowser_version}/torbrowser-install-{torbrowser_version}_en-US.exe"
win32_filename = f"torbrowser-install-{torbrowser_version}_en-US.exe"
win64_url = f"https://dist.torproject.org/torbrowser/{torbrowser_version}/torbrowser-install-win64-{torbrowser_version}_en-US.exe"
win64_filename = f"torbrowser-install-win64-{torbrowser_version}_en-US.exe"
macos_url = f"https://dist.torproject.org/torbrowser/{torbrowser_version}/TorBrowser-{torbrowser_version}-osx64_en-US.dmg"
macos_filename = f"TorBrowser-{torbrowser_version}-osx64_en-US.dmg"
linux64_url = f"https://dist.torproject.org/torbrowser/{torbrowser_version}/tor-browser-linux64-{torbrowser_version}_en-US.tar.xz"
linux64_filename = f"tor-browser-linux64-{torbrowser_version}_en-US.tar.xz"


# Common paths
root_path = os.path.dirname(
    os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
)
working_path = os.path.join(root_path, "build", "tor")


def get_tor_windows(platform):
    if platform == "win32":
        win_url = win32_url
        win_filename = win32_filename
        expected_win_sha256 = expected_win32_sha256
        bin_filenames = [
            "libcrypto-1_1.dll",
            "libevent-2-1-7.dll",
            "libevent_core-2-1-7.dll",
            "libevent_extra-2-1-7.dll",
            "libgcc_s_dw2-1.dll",
            "libssl-1_1.dll",
            "libssp-0.dll",
            "libwinpthread-1.dll",
            "tor.exe",
            "zlib1.dll",
        ]
    elif platform == "win64":
        win_url = win64_url
        win_filename = win64_filename
        expected_win_sha256 = expected_win64_sha256
        bin_filenames = [
            "libcrypto-1_1-x64.dll",
            "libevent-2-1-7.dll",
            "libevent_core-2-1-7.dll",
            "libevent_extra-2-1-7.dll",
            "libgcc_s_seh-1.dll",
            "libssl-1_1-x64.dll",
            "libssp-0.dll",
            "libwinpthread-1.dll",
            "tor.exe",
            "zlib1.dll",
        ]
    else:
        click.echo("invalid platform")
        return

    # Build paths
    win_path = os.path.join(working_path, win_filename)
    dist_path = os.path.join(root_path, "onionshare", "resources", "tor")

    # Make sure the working folder exists
    if not os.path.exists(working_path):
        os.makedirs(working_path)

    # Make sure Tor Browser is downloaded
    if not os.path.exists(win_path):
        print("Downloading {}".format(win_url))
        r = requests.get(win_url)
        open(win_path, "wb").write(r.content)
        win_sha256 = hashlib.sha256(r.content).hexdigest()
    else:
        print("Already downloaded: {}".format(win_path))
        win_data = open(win_path, "rb").read()
        win_sha256 = hashlib.sha256(win_data).hexdigest()

    # Compare the hash
    if win_sha256 != expected_win_sha256:
        print("ERROR! The sha256 doesn't match:")
        print("expected: {}".format(expected_win32_sha256))
        print("  actual: {}".format(win_sha256))
        sys.exit(-1)

    # Extract the bits we need from the exe
    subprocess.Popen(
        [
            "7z",
            "e",
            "-y",
            win_path,
            "Browser\\TorBrowser\\Tor",
            "-o%s" % os.path.join(working_path, "Tor"),
        ]
    ).wait()
    subprocess.Popen(
        [
            "7z",
            "e",
            "-y",
            win_path,
            "Browser\\TorBrowser\\Data\\Tor\\geoip*",
            "-o%s" % os.path.join(working_path, "Data"),
        ]
    ).wait()

    # Copy into the onionshare resources
    if os.path.exists(dist_path):
        shutil.rmtree(dist_path)
    os.makedirs(dist_path)
    for filename in bin_filenames:
        shutil.copyfile(
            os.path.join(working_path, "Tor", filename),
            os.path.join(dist_path, filename),
        )
    for filename in ["geoip", "geoip6"]:
        shutil.copyfile(
            os.path.join(working_path, "Data", filename),
            os.path.join(dist_path, filename),
        )

    # Fetch the built-in bridges
    update_tor_bridges()


def get_tor_macos():
    # Build paths
    dmg_tor_path = os.path.join(
        "/Volumes", "Tor Browser", "Tor Browser.app", "Contents"
    )
    dmg_path = os.path.join(working_path, macos_filename)
    dist_path = os.path.join(root_path, "onionshare", "resources", "tor")
    if not os.path.exists(dist_path):
        os.makedirs(dist_path, exist_ok=True)

    # Make sure the working folder exists
    if not os.path.exists(working_path):
        os.makedirs(working_path)

    # Make sure the zip is downloaded
    if not os.path.exists(dmg_path):
        print("Downloading {}".format(macos_url))
        r = requests.get(macos_url)
        open(dmg_path, "wb").write(r.content)
        dmg_sha256 = hashlib.sha256(r.content).hexdigest()
    else:
        dmg_data = open(dmg_path, "rb").read()
        dmg_sha256 = hashlib.sha256(dmg_data).hexdigest()

    # Compare the hash
    if dmg_sha256 != expected_macos_sha256:
        print("ERROR! The sha256 doesn't match:")
        print("expected: {}".format(expected_macos_sha256))
        print("  actual: {}".format(dmg_sha256))
        sys.exit(-1)

    # Mount the dmg, copy data to the working path
    subprocess.call(["hdiutil", "attach", dmg_path])

    # Copy into dist
    shutil.copyfile(
        os.path.join(dmg_tor_path, "Resources", "TorBrowser", "Tor", "geoip"),
        os.path.join(dist_path, "geoip"),
    )
    shutil.copyfile(
        os.path.join(dmg_tor_path, "Resources", "TorBrowser", "Tor", "geoip6"),
        os.path.join(dist_path, "geoip6"),
    )
    shutil.copyfile(
        os.path.join(dmg_tor_path, "MacOS", "Tor", "tor.real"),
        os.path.join(dist_path, "tor"),
    )
    os.chmod(os.path.join(dist_path, "tor"), 0o755)
    shutil.copyfile(
        os.path.join(dmg_tor_path, "MacOS", "Tor", "libevent-2.1.7.dylib"),
        os.path.join(dist_path, "libevent-2.1.7.dylib"),
    )

    # Eject dmg
    subprocess.call(["diskutil", "eject", "/Volumes/Tor Browser"])

    # Fetch the built-in bridges
    update_tor_bridges()


def get_tor_linux64():
    # Build paths
    tarball_path = os.path.join(working_path, linux64_filename)
    dist_path = os.path.join(root_path, "onionshare", "resources", "tor")

    # Make sure dirs exist
    if not os.path.exists(working_path):
        os.makedirs(working_path, exist_ok=True)

    if not os.path.exists(dist_path):
        os.makedirs(dist_path, exist_ok=True)

    # Make sure the tarball is downloaded
    if not os.path.exists(tarball_path):
        print("Downloading {}".format(linux64_url))
        r = requests.get(linux64_url)
        open(tarball_path, "wb").write(r.content)
        tarball_sha256 = hashlib.sha256(r.content).hexdigest()
    else:
        tarball_data = open(tarball_path, "rb").read()
        tarball_sha256 = hashlib.sha256(tarball_data).hexdigest()

    # Compare the hash
    if tarball_sha256 != expected_linux64_sha256:
        print("ERROR! The sha256 doesn't match:")
        print("expected: {}".format(expected_linux64_sha256))
        print("  actual: {}".format(tarball_sha256))
        sys.exit(-1)

    # Delete extracted tarball, if it's there
    shutil.rmtree(os.path.join(working_path, "tor-browser_en-US"), ignore_errors=True)

    # Extract the tarball
    subprocess.call(["tar", "-xvf", tarball_path], cwd=working_path)
    tarball_tor_path = os.path.join(
        working_path, "tor-browser_en-US", "Browser", "TorBrowser"
    )

    # Copy into dist
    shutil.copyfile(
        os.path.join(tarball_tor_path, "Data", "Tor", "geoip"),
        os.path.join(dist_path, "geoip"),
    )
    shutil.copyfile(
        os.path.join(tarball_tor_path, "Data", "Tor", "geoip6"),
        os.path.join(dist_path, "geoip6"),
    )
    shutil.copyfile(
        os.path.join(tarball_tor_path, "Tor", "tor"),
        os.path.join(dist_path, "tor"),
    )
    os.chmod(os.path.join(dist_path, "tor"), 0o755)
    shutil.copyfile(
        os.path.join(tarball_tor_path, "Tor", "libcrypto.so.1.1"),
        os.path.join(dist_path, "libcrypto.so.1.1"),
    )
    shutil.copyfile(
        os.path.join(tarball_tor_path, "Tor", "libevent-2.1.so.7"),
        os.path.join(dist_path, "libevent-2.1.so.7"),
    )
    shutil.copyfile(
        os.path.join(tarball_tor_path, "Tor", "libssl.so.1.1"),
        os.path.join(dist_path, "libssl.so.1.1"),
    )
    shutil.copyfile(
        os.path.join(tarball_tor_path, "Tor", "libstdc++", "libstdc++.so.6"),
        os.path.join(dist_path, "libstdc++.so.6"),
    )

    print(f"Tor binaries extracted to: {dist_path}")

    # Fetch the built-in bridges
    update_tor_bridges()


def update_tor_bridges():
    """
    Update the built-in Tor Bridges in OnionShare's torrc templates.
    """
    torrc_template_dir = os.path.join(
        root_path, os.pardir, "cli/onionshare_cli/resources"
    )

    r = requests.get("https://gitweb.torproject.org/builders/tor-browser-build.git/plain/projects/tor-browser/Bundle-Data/PTConfigs/bridge_prefs.js")
    if r.status_code != 200:
        print(
            f"There was a problem fetching the latest built-in bridges: status_code={r.status_code}"
        )
        return False
    
    # Parse the bridges from this javascript file
    bridges = {}
    for line in r.content.decode().split("\n"):
        if line.startswith('pref("extensions.torlauncher.default_bridge.'):
            i = line.index('", "') + 4
            bridge = line[i:].rstrip('");')

            bridge_type = bridge.split()[0]
            if bridge_type not in bridges:
                bridges[bridge_type] = []

            bridges[bridge_type].append(bridge)
    
    for bridge_type in bridges:
        if bridge_type == "meek_lite":
            torrc_template_extension = "meek_lite_azure"
        else:
            torrc_template_extension = bridge_type
        
        torrc_template = os.path.join(
            root_path,
            torrc_template_dir,
            f"torrc_template-{torrc_template_extension}",
        )

        with open(torrc_template, "w") as f:
            f.write(f"# Enable built-in {bridge_type} bridge\n")
            # Sorts the bridges numerically by IP, since they come back in
            # random order from the API each time, and create noisy git diff.
            bridges[bridge_type].sort(key=lambda s: s.split()[1])
            for item in bridges[bridge_type]:
                f.write(f"Bridge {item}\n")


@click.command()
@click.argument("platform")
def main(platform):
    """
    Download Tor Browser and extract tor binaries
    """
    valid_platforms = ["win32", "win64", "macos", "linux64"]
    if platform not in valid_platforms:
        click.echo(f"platform must be one of: {valid_platforms}")
        return

    if platform == "win32":
        get_tor_windows(platform)
    elif platform == "win64":
        get_tor_windows(platform)
    elif platform == "macos":
        get_tor_macos()
    elif platform == "linux64":
        get_tor_linux64()
    else:
        click.echo("invalid platform")


if __name__ == "__main__":
    main()
