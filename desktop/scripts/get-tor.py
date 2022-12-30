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

torbrowser_version = "12.0"
expected_win32_sha256 = (
    "a9cc0f0af2ce8ca0d7a27d65c7efa37f6419cfc793fa80371e7db73d44b4cc02"
)
expected_win64_sha256 = (
    "f496cc0219c8b73f1f100124d6514bad55f503ff76202747f23620a6677e83c2"
)
expected_macos_sha256 = (
    "11c8360187356e6c0837612a320f1a117303fc449602c9fd73f4faf9f9bbcfc9"
)
expected_linux64_sha256 = (
    "850ce601d815bac63e4f5937646d2b497173be28b27b30a7526ebb946a459874"
)

win32_filename = f"torbrowser-install-{torbrowser_version}_ALL.exe"
win32_url = f"https://dist.torproject.org/torbrowser/{torbrowser_version}/{win32_filename}"
win64_filename = f"torbrowser-install-win64-{torbrowser_version}_ALL.exe"
win64_url = f"https://dist.torproject.org/torbrowser/{torbrowser_version}/{win64_filename}"
macos_filename = f"TorBrowser-{torbrowser_version}-macos_ALL.dmg"
macos_url = f"https://dist.torproject.org/torbrowser/{torbrowser_version}/{macos_filename}"
linux64_filename = f"tor-browser-linux64-{torbrowser_version}_ALL.tar.xz"
linux64_url = f"https://dist.torproject.org/torbrowser/{torbrowser_version}/{linux64_filename}"


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
            "tor.exe"
        ]
    elif platform == "win64":
        win_url = win64_url
        win_filename = win64_filename
        expected_win_sha256 = expected_win64_sha256
        bin_filenames = [
            "tor.exe"
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


def get_tor_macos_x86_64():
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


def get_tor_macos_aarch64():
    # Versions and shasums
    torbin_version = "0.4.7.10"
    libevent_version = "2.1.12"
    expected_torbin_sha256 = "01abf45e673649f6c0fee07f1fcffcce82b2bdb5f5db0c15a9cdcfda6e5eb187"
    expected_geoip_sha256 = "7e777efc194ea9788171636085b19875d19397d3249fbb88136534037a3dc38f"
    expected_geoip6_sha256 = "f11bd1d7546cad00b6db0a1594f3ac1daf9f541004fd7efb5414e068693d6add"
    expected_libevent_sha256 = "2de95fd8cf8849028f9146f04cbde8cc7399ba0191b65ab92825a9a5e691a464"

    # Build paths
    dist_path = os.path.join(root_path, "onionshare", "resources", "tor")

    # Make sure homebrew is installed and in path
    brew_path = shutil.which("brew")
    if brew_path is None:
        print("brew not found in path. Homebrew must be installed")
        sys.exit(-1)
    brew_prefix = os.path.dirname(os.path.dirname(brew_path))

    # Check that tor is installed, otherwise install it
    tor_path = os.path.join(brew_prefix, "Cellar", "tor", torbin_version)
    libevent_path = os.path.join(brew_prefix, "Cellar", "libevent", libevent_version)
    torbin_path = os.path.join(tor_path, "bin", "tor")
    if not os.path.exists(torbin_path):
        print(f"Installing tor v{torbin_version}...")
        if subprocess.call([os.path.join(brew_path), "install", "tor"]) != 0:
            print(f"Could not install tor using homebrew")
            sys.exit(-1)
    
    # Compute the hashes
    torbin_data = open(torbin_path, "rb").read()
    torbin_sha256 = hashlib.sha256(torbin_data).hexdigest()
    geoip_data = open(
        os.path.join(tor_path, "share", "tor", "geoip"),
        "rb").read()
    geoip_sha256 = hashlib.sha256(geoip_data).hexdigest()
    geoip6_data = open(
        os.path.join(tor_path, "share", "tor", "geoip6"),
        "rb").read()
    geoip6_sha256 = hashlib.sha256(geoip6_data).hexdigest()
    libeventlib_path = os.path.join(libevent_path, "lib", "libevent-2.1.7.dylib")
    libevent_data = open(libeventlib_path, "rb").read()
    libevent_sha256 = hashlib.sha256(libevent_data).hexdigest()

    # Compare the hashes
    if torbin_sha256 != expected_torbin_sha256:
        print("ERROR! The sha256 doesn't match (tor):")
        print("expected: {}".format(expected_torbin_sha256))
        print("  actual: {}".format(torbin_sha256))
        sys.exit(-1)
    if geoip_sha256 != expected_geoip_sha256:
        print("ERROR! The sha256 doesn't match (geoip):")
        print("expected: {}".format(expected_geoip_sha256))
        print("  actual: {}".format(geoip_sha256))
        sys.exit(-1)
    if geoip6_sha256 != expected_geoip6_sha256:
        print("ERROR! The sha256 doesn't match (geoip6):")
        print("expected: {}".format(expected_geoip6_sha256))
        print("  actual: {}".format(geoip6_sha256))
        sys.exit(-1)
    if libevent_sha256 != expected_libevent_sha256:
        print("ERROR! The sha256 doesn't match (libevent):")
        print("expected: {}".format(expected_libevent_sha256))
        print("  actual: {}".format(libevent_sha256))
        sys.exit(-1)
    
    # Copy into dist
    shutil.copyfile(
        os.path.join(tor_path, "share", "tor", "geoip"),
        os.path.join(dist_path, "geoip"),
    )
    shutil.copyfile(
        os.path.join(tor_path, "share", "tor", "geoip6"),
        os.path.join(dist_path, "geoip6"),
    )
    shutil.copyfile(
        torbin_path,
        os.path.join(dist_path, "tor"),
    )
    os.chmod(os.path.join(dist_path, "tor"), 0o755)
    shutil.copyfile(
        libeventlib_path,
        os.path.join(dist_path, "libevent-2.1.7.dylib"),
    )


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
    endpoint = "https://bridges.torproject.org/moat/circumvention/builtin"
    r = requests.post(
        endpoint,
        headers={"Content-Type": "application/vnd.api+json"},
    )
    if r.status_code != 200:
        print(
            f"There was a problem fetching the latest built-in bridges: status_code={r.status_code}"
        )
        sys.exit(1)

    result = r.json()
    print(f"Built-in bridges: {result}")

    if "errors" in result:
        print(
            f"There was a problem fetching the latest built-in bridges: errors={result['errors']}"
        )
        sys.exit(1)

    for bridge_type in ["meek-azure", "obfs4", "snowflake"]:
        if bridge_type in result and result[bridge_type]:
            if bridge_type == "meek-azure":
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
                bridges = result[bridge_type]
                # Sorts the bridges numerically by IP, since they come back in
                # random order from the API each time, and create noisy git diff.
                bridges.sort(key=lambda s: s.split()[1])
                for item in bridges:
                    f.write(f"Bridge {item}\n")


@click.command()
@click.argument("platform")
def main(platform):
    """
    Download Tor Browser and extract tor binaries
    """
    valid_platforms = ["win32", "win64", "macos-x86_64", "macos-aarch64", "linux64"]
    if platform not in valid_platforms:
        click.echo(f"platform must be one of: {valid_platforms}")
        return

    if platform == "win32":
        get_tor_windows(platform)
    elif platform == "win64":
        get_tor_windows(platform)
    elif platform == "macos-x86_64":
        get_tor_macos_x86_64()
    elif platform == "macos-aarch64":
        get_tor_macos_aarch64()
    elif platform == "linux64":
        get_tor_linux64()
    else:
        click.echo("invalid platform")


if __name__ == "__main__":
    main()
