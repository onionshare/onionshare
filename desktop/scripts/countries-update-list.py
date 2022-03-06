#!/usr/bin/env python3
import os
import tempfile
import subprocess
import json

import onionshare_cli


def main():
    # Clone the country-list repo
    tmp_dir = tempfile.TemporaryDirectory()
    subprocess.run(
        ["git", "clone", "https://github.com/umpirsky/country-list.git"],
        cwd=tmp_dir.name,
    )
    repo_dir = os.path.join(tmp_dir.name, "country-list")

    # Get the list of enabled languages
    common = onionshare_cli.common.Common()
    settings = onionshare_cli.settings.Settings(common)
    available_locales = list(settings.available_locales)

    # Make a dictionary that makes a language's ISO 3166-1 to its name in all enabled languages
    os.makedirs(os.path.join("onionshare", "resources", "countries"), exist_ok=True)
    for locale in available_locales:
        with open(os.path.join(repo_dir, "data", locale, "country.json")) as f:
            countries = json.loads(f.read())

        # Remove countries we don't have images for
        for key in ["JE", "MH", "FM", "MP", "PS", "TV", "UM"]:
            del countries[key]

        with open(
            os.path.join("onionshare", "resources", "countries", f"{locale}.json"),
            "w",
        ) as f:
            f.write(json.dumps(countries))


if __name__ == "__main__":
    main()
