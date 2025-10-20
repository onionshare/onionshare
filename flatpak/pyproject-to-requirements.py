#!/usr/bin/env python3
import sys
import click

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


def format_version(dep, version):
    if version == "*":
        return dep
    # If it's a dictionary, assume it's in the format {extras = ["socks"], version = "*"}
    elif isinstance(version, dict) and "version" in version:
        version = version["version"]
        if version == "*":
            return dep
        elif version.startswith("^"):
            return f"{dep}>={version[1:]}.0"
        elif version.startswith((">=", "<=", "!=", "==", "<", ">")):
            return f"{dep}{version}"
        else:
            return f"{dep}=={version}"
    elif version.startswith("^"):
        return f"{dep}>={version[1:]}.0"
    elif version.startswith((">=", "<=", "!=", "==", "<", ">")):
        return f"{dep}{version}"
    else:
        return f"{dep}=={version}"


@click.command()
@click.argument("pyproject_filename")
def poetry_to_requirements(pyproject_filename):
    """Convert poetry dependencies in a pyproject.toml to requirements format."""
    with open(pyproject_filename, "r") as f:
        data = tomllib.load(f)

    dependencies = data.get("tool", {}).get("poetry", {}).get("dependencies", {})

    requirements = []

    for dep, version in dependencies.items():
        if dep == "python" or dep == "onionshare_cli":
            continue

        formatted = format_version(dep, version)
        if formatted:
            requirements.append(formatted)

    for req in requirements:
        print(req)


@click.command()
@click.argument("pyproject_filename")
def pyproject_to_requirements(pyproject_filename):
    """Convert PEP 631 dependencies in a pyproject.toml to requirements format."""
    with open(pyproject_filename, "r") as f:
        data = tomllib.load(f)

    dependencies = data.get("project", {}).get("dependencies", [])

    requirements = []

    for dep in dependencies:
        if dep == "onionshare_cli":
            continue

        requirements.append(dependencies)

    for req in requirements:
        print(req)


if __name__ == "__main__":
    pyproject_to_requirements()
