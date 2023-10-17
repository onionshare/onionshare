#!/usr/bin/env python3
import os
import shutil
import click
import subprocess


def get_binary_arches(app_dir):
    universal = []
    silicon = []
    intel = []
    for dirpath, dirnames, filenames in os.walk(app_dir):
        for basename in filenames:
            filename = os.path.join(dirpath, basename)
            if os.path.isfile(filename):
                out = subprocess.check_output(["file", filename]).decode("utf-8")
                if (
                    "Mach-O 64-bit executable" in out
                    or "Mach-O 64-bit dynamically linked shared library" in out
                ):
                    arm64, x86 = False, False
                    if "arm64" in out:
                        arm64 = True
                    if "x86_64" in out:
                        x86 = True

                    if arm64 and x86:
                        universal.append(filename)
                    elif arm64:
                        silicon.append(filename)
                    elif x86:
                        intel.append(filename)

    return universal, silicon, intel


@click.command()
@click.argument("intel_app", type=click.Path(exists=True))
@click.argument("silicon_app", type=click.Path(exists=True))
@click.argument("output_app", type=click.Path(exists=False))
def main(intel_app, silicon_app, output_app):
    # Get the list of binaries in each app
    print("Looking up binaries from Intel app:", intel_app)
    intel_universal, intel_silicon, intel_intel = get_binary_arches(intel_app)
    print("Looking up binaries from Silicon app:", silicon_app)
    silicon_universal, silicon_silicon, silicon_intel = get_binary_arches(silicon_app)

    # Find which binaries should be merged
    intel_intel_filenames = [i[len(intel_app) + 1 :] for i in intel_intel]
    silicon_silicon_filenames = [i[len(silicon_app) + 1 :] for i in silicon_silicon]
    intersection = set(intel_intel_filenames).intersection(
        set(silicon_silicon_filenames)
    )

    # Copy the Silicon app to the output app
    print("Copying the app bundle for the output app")
    shutil.copytree(silicon_app, output_app, symlinks=True)

    # Merge them
    for filename in intersection:
        print(f"Merging {filename}")
        intel_binary = os.path.join(intel_app, filename)
        silicon_binary = os.path.join(silicon_app, filename)
        output_binary = os.path.join(output_app, filename)
        subprocess.run(
            ["lipo", "-create", intel_binary, silicon_binary, "-output", output_binary]
        )

    print(f"Merge complete: {output_app}")


if __name__ == "__main__":
    main()
