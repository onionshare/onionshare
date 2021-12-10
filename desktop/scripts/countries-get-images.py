#!/usr/bin/env python3
import subprocess
import tempfile
import json
import os


def main():
    tmp_dir = tempfile.TemporaryDirectory()
    mapsdir = os.path.join(tmp_dir.name, "mapsicon")
    subprocess.run(["git", "clone", "https://github.com/djaiss/mapsicon.git", mapsdir])

    with open(
        os.path.join("src", "onionshare", "resources", "countries", "en.json")
    ) as f:
        countries = list(json.loads(f.read()))

    os.makedirs(
        os.path.join(
            "src",
            "onionshare",
            "resources",
            "images",
            "countries",
        ),
        exist_ok=True,
    )

    for country in countries:
        country = country.lower()
        if os.path.isdir(os.path.join(mapsdir, "all", f"{country}")):
            src_filename = os.path.join(mapsdir, "all", f"{country}", "256.png")
            dest_light_filename = os.path.join(
                "src",
                "onionshare",
                "resources",
                "images",
                "countries",
                f"{country}-light.png",
            )
            dest_dark_filename = os.path.join(
                "src",
                "onionshare",
                "resources",
                "images",
                "countries",
                f"{country}-dark.png",
            )
            subprocess.run(
                [
                    "convert",
                    src_filename,
                    "-fill",
                    "#5a2063",
                    "+opaque",
                    "none",
                    dest_light_filename,
                ]
            )
            subprocess.run(
                [
                    "convert",
                    src_filename,
                    "-fill",
                    "#d950ee",
                    "+opaque",
                    "none",
                    dest_dark_filename,
                ]
            )


if __name__ == "__main__":
    main()
