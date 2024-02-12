import os
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
                    or "Mach-O 64-bit bundle" in out
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
