#!/usr/bin/env python3
import subprocess
import tempfile
import json
import os


def main():
    tmp_dir = tempfile.TemporaryDirectory()
    flagsdir = os.path.join(tmp_dir.name, "flagsicon")
    subprocess.run(["git", "clone", "https://github.com/lipis/flag-icons.git", flagsdir])

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
        country = country.lower()
        if os.path.isfile(os.path.join(flagsdir, "flags", "4x3", f"{country}.svg")):
            src_filename = os.path.join(flagsdir, "flags", "4x3", f"{country}.svg")
            dest_filename = os.path.join(
                "onionshare",
                "resources",
                "images",
                "countries",
                f"{country}.png",
            )
            subprocess.run(
                [
                    "convert",
                    src_filename,
                    "-background",
                    "none",
                    "-density",
                    "100",
                    "-resize",
                    "64x",
                    dest_filename,
                ]
            )


if __name__ == "__main__":
    main()
