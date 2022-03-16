#!/usr/bin/env python3
import subprocess
import tempfile
import json
import os


def main():
    tmp_dir = tempfile.TemporaryDirectory()
    flagsdir = os.path.join(tmp_dir.name, "flagsicon")
    subprocess.run(["git", "clone", "https://github.com/gosquared/flags.git", flagsdir])

    with open(
        os.path.join("onionshare", "resources", "countries", "en.json")
    ) as f:
        countries = list(json.loads(f.read()))

    os.makedirs(
        os.path.join(
            "onionshare",
            "resources",
            "images",
            "countries",
        ),
        exist_ok=True,
    )

    for country in countries:
        if os.path.isfile(os.path.join(flagsdir, "flags", "flags-iso", "flat", "64", f"{country}.png")):
            src_filename = os.path.join(flagsdir, "flags", "flags-iso", "flat", "64", f"{country}.png")
            dest_filename = os.path.join(
                "onionshare",
                "resources",
                "images",
                "countries",
                f"{country}.png",
            )
            subprocess.run(["cp", src_filename, dest_filename])


if __name__ == "__main__":
    main()
