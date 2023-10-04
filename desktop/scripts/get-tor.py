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
import tempfile
import gnupg

torbrowser_latest_url = (
    "https://aus1.torproject.org/torbrowser/update_3/release/downloads.json"
)
tor_dev_fingerprint = "EF6E286DDA85EA2A4BA7DE684E2C6E8793298290"

# Common paths
root_path = os.path.dirname(
    os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
)
working_path = os.path.join(root_path, "build", "tor")


def get_latest_tor_version_urls(platform):
    r = requests.get(torbrowser_latest_url)
    if r.status_code != 200 or platform not in r.json()["downloads"]:
        print("Tor browser latest version url not working")
        sys.exit(-1)

    platform_url = r.json()["downloads"][platform]["ALL"]["binary"]
    platform_sig_url = r.json()["downloads"][platform]["ALL"]["sig"]
    platform_filename = platform_url.split("/")[-1]

    return platform_url, platform_filename, platform_sig_url


def get_tor_windows(gpg, torkey, win_url, win_filename, expected_win_sig):
    bin_filenames = ["tor.exe"]

    # Build paths
    win_path = os.path.join(working_path, win_filename)
    win_sig_path = os.path.join(working_path, f"{win_filename}.asc")
    dist_path = os.path.join(root_path, "onionshare", "resources", "tor")

    # Make sure the working folder exists
    if not os.path.exists(working_path):
        os.makedirs(working_path)

    # Make sure Tor Browser is downloaded
    if not os.path.exists(win_path):
        print("Downloading {}".format(win_url))
        r = requests.get(win_url)
        open(win_path, "wb").write(r.content)

    # Make sure Tor Browser signature is downloaded
    if not os.path.exists(win_sig_path):
        print("Downloading {}".format(expected_win_sig))
        r = requests.get(expected_win_sig)
        open(win_sig_path, "wb").write(r.content)

    # Verify the signature
    sig_stream = open(win_sig_path, "rb")
    verified = gpg.verify_file(sig_stream, win_path)
    if not verified.valid or verified.pubkey_fingerprint != tor_dev_fingerprint:
        print("ERROR! The tarball verification with the signature failed!")
        sys.exit(-1)

    print("Tor Browser verification successful!")

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


def get_tor_macos(gpg, torkey, macos_url, macos_filename, expected_macos_sig):
    # Build paths
    dmg_tor_path = os.path.join(
        "/Volumes", "Tor Browser", "Tor Browser.app", "Contents"
    )
    dmg_path = os.path.join(working_path, macos_filename)
    dmg_sig_path = os.path.join(working_path, f"{macos_filename}.asc")
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

    # Make sure the signature is downloaded
    if not os.path.exists(dmg_sig_path):
        print("Downloading {}".format(expected_macos_sig))
        r = requests.get(expected_macos_sig)
        open(dmg_sig_path, "wb").write(r.content)

    # Verify the signature
    sig_stream = open(dmg_sig_path, "rb")
    verified = gpg.verify_file(sig_stream, dmg_path)
    if not verified.valid or verified.pubkey_fingerprint != tor_dev_fingerprint:
        print("ERROR! The tarball verification with the signature failed!")
        sys.exit(-1)

    print("Tor Browser verification successful!")

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
        os.path.join(dmg_tor_path, "MacOS", "Tor", "tor"),
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


def get_tor_linux64(gpg, torkey, linux64_url, linux64_filename, expected_linux64_sig):
    # Build paths
    tarball_path = os.path.join(working_path, linux64_filename)
    tarball_sig_path = os.path.join(working_path, f"{linux64_filename}.asc")
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

    # Make sure the signature file is downloaded
    if not os.path.exists(tarball_sig_path):
        print("Downloading {}".format(expected_linux64_sig))
        r = requests.get(expected_linux64_sig)
        open(tarball_sig_path, "wb").write(r.content)

    # Verify signature
    sig_stream = open(tarball_sig_path, "rb")
    verified = gpg.verify_file(sig_stream, tarball_path)
    if not verified.valid or verified.pubkey_fingerprint != tor_dev_fingerprint:
        print("ERROR! The tarball verification with the signature failed!")
        sys.exit(-1)

    print("Tor Browser verification successful!")

    # Delete extracted tarball, if it's there
    shutil.rmtree(os.path.join(working_path, "tor-browser"), ignore_errors=True)

    # Extract the tarball
    subprocess.call(["tar", "-xvf", tarball_path], cwd=working_path)
    tarball_tor_path = os.path.join(
        working_path, "tor-browser", "Browser", "TorBrowser"
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
    valid_platforms = ["win64", "macos", "linux64"]
    if platform not in valid_platforms:
        click.echo(f"platform must be one of: {valid_platforms}")
        return

    (
        platform_url,
        platform_filename,
        expected_platform_sig,
    ) = get_latest_tor_version_urls(platform)
    tmpdir = tempfile.TemporaryDirectory()
    gpg = gnupg.GPG(gnupghome=tmpdir.name)
    torkey = gpg.import_keys_file(
        os.path.join(root_path, "scripts", "tor-browser-devs.gpg")
    )
    print(f"Imported Tor GPG key: {torkey.fingerprints}")

    if platform == "win64":
        get_tor_windows(
            gpg, torkey, platform_url, platform_filename, expected_platform_sig
        )
    elif platform == "macos":
        get_tor_macos(
            gpg, torkey, platform_url, platform_filename, expected_platform_sig
        )
    elif platform == "linux64":
        get_tor_linux64(
            gpg, torkey, platform_url, platform_filename, expected_platform_sig
        )
    else:
        click.echo("invalid platform")

    tmpdir.cleanup()


if __name__ == "__main__":
    main()
