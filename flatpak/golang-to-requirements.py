#!/usr/bin/env python3
# coding: utf-8

import argparse
import subprocess
import sys
import json
import os
import re
import tempfile

import yaml
import requests
from bs4 import BeautifulSoup


def parse_args():
    """
    Parse arguments to the script
    """
    parser = argparse.ArgumentParser(description="Extract dependencies for Golang")
    parser.add_argument("--url", dest="url", required=True, help="Pass repo URL")
    parser.add_argument(
        "--name", dest="name", required=True, help="Pass repo short name"
    )
    parser.add_argument("--version", default="", dest="version", help="Pass tag name")
    parser.add_argument(
        "--folder", default="", dest="folder", help="Pass optional folder name"
    )
    return parser.parse_args()


def extract_commit_id(module_version):
    # Regex to match formats like: v0.0.0-20190819201941-24fa4b261c55
    complex_format_regex = re.compile(
        r"v\d+\.\d+\.\d+-\d{14}-(?P<commit>[a-fA-F0-9]{12,40})"
    )

    match = complex_format_regex.search(module_version)
    if match:
        return match.group("commit")

    # If the version is just a simple version like v1.4.0 or v0.13.0, return None
    return None


def get_commit_id_from_git(
    git_url,
    version=None,
    short_commit_id=None,
):
    # If short_commit_id is provided, simply expand it
    if short_commit_id:
        print(
            f"✨ Cloning {git_url} to find long commit ID version of {short_commit_id}"
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            subprocess.run(["git", "clone", "--bare", git_url, tmp_dir], check=True)
            result = subprocess.run(
                ["git", "rev-parse", short_commit_id],
                cwd=tmp_dir,
                check=True,
                capture_output=True,
                text=True,
            )
            commit_id = result.stdout.strip()
            print(f"✨ Found commit ID: {commit_id}")
            return commit_id

    # If it's a GitHub URL, use the GitHub API
    parsed_url = urlparse(git_url)
    if parsed_url.hostname == "github.com":
        repo_parts = parsed_url.path.lstrip("/").split("/")
        if len(repo_parts) == 2:
            owner, repo = repo_parts
            tag_url = (
                f"https://api.github.com/repos/{owner}/{repo}/git/refs/tags/{version}"
            )

            response = requests.get(tag_url)
            if response.status_code == 200:
                json_data = response.json()
                commit_id = json_data["object"]["sha"]
                print(f"✨ Used GitHub API to find commit ID: {commit_id}")
                return commit_id

    # If it's a GitLab URL, use the GitLab API
    elif parsed_url.hostname == "gitlab.com":
        repo_parts = parsed_url.path.lstrip("/").rstrip(".git").split("/")
        if len(repo_parts) >= 2:
            tag_url = f"https://gitlab.com/api/v4/projects/{'%2F'.join(repo_parts)}/repository/tags/{version}"

            response = requests.get(tag_url)
            if response.status_code == 200:
                json_data = response.json()
                commit_id = json_data["commit"]["id"]
                print(f"✨ Used GitLab API to find commit ID: {commit_id}")
                return commit_id

    # Otherwise, clone the git repo to find the commit id
    with tempfile.TemporaryDirectory() as tmp_dir:
        try:
            if version:
                print(f"✨ Cloning {git_url}@{version} to find commit ID")
                subprocess.run(
                    ["git", "clone", "--bare", "-b", version, git_url, tmp_dir],
                    check=True,
                )
            else:
                print(f"✨ Cloning {git_url} to find commit ID")
                subprocess.run(["git", "clone", "--bare", git_url, tmp_dir], check=True)
        except subprocess.CalledProcessError:
            # If cloning with a specific tag fails, fall back to default branch
            if version:
                print(
                    f"✨ Tag {version} not found. Cloning {git_url} default branch..."
                )
                subprocess.run(["git", "clone", "--bare", git_url, tmp_dir], check=True)

        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=tmp_dir,
                check=True,
                capture_output=True,
                text=True,
            )
            commit_id = result.stdout.strip()
            print(f"✨ Found commit ID: {commit_id}")
            return commit_id
        except subprocess.CalledProcessError:
            return None


def get_module_info(module_name):
    result = subprocess.run(
        ["go", "list", "-m", "-json", module_name],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def get_git_url(module_name):
    # Remove the version suffix, if present
    module_name = re.sub(r"/v\d+$", "", module_name)

    # Remove the subdirectory, if present (e.g. github.com/foo/bar/subdir -> github.com/foo/bar)
    if "gitlab.com" in module_name or "github.com" in module_name:
        url_parts = module_name.split("/")
        if len(url_parts) > 3:
            module_name = "/".join(url_parts[:3])

    if "gitlab.com" in module_name:
        return f"https://gitlab.com/{module_name.replace('gitlab.com/', '')}"
    elif "github.com" in module_name:
        return f"https://github.com/{module_name.replace('github.com/', '')}"
    elif "git.torproject.org" in module_name:
        return f"https://{module_name}"
    else:
        response = requests.get(f"https://{module_name}/?go-get=1")
        if response.status_code != 200:
            return None
        soup = BeautifulSoup(response.content, "html.parser")
        meta_tag = soup.find("meta", {"name": "go-import"})
        if meta_tag:
            url = meta_tag["content"].split()[2]
            r = requests.get(url, allow_redirects=True)
            if r.history:
                return r.url
            else:
                return url

        return None


def main(repo, repo_name, version, folder):
    """Flatpak Go Generator"""

    with tempfile.TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)

        try:
            if not folder:
                folder = "."
            print("✨ Cloning the target repository")
            subprocess.run(
                ["git", "clone", f"https://{repo}", f"src/{repo_name}"], check=True
            )
            os.chdir(f"src/{repo_name}/{folder}")

            if version:
                print(f"✨ Checking out version {version}")
                subprocess.run(["git", "checkout", version], check=True)

        except subprocess.CalledProcessError:
            print(f"✨ Error fetching {sys.argv[1]}")
            sys.exit(1)

        result = subprocess.run(
            ["go", "list", "-m", "all"],
            check=True,
            capture_output=True,
            text=True,
            cwd=f"{temp_dir}/src/{repo_name}/{folder}",
        )

        modules = result.stdout.strip().split("\n")
        modules = modules[1:]  # Skip the first module, which is the current module

        print(f"✨ Found {len(modules)} dependencies")

        sources = []

        for module in modules:
            module_name, module_version = module.split(" ", 1)
            print(f"✨ Module: {module}")

            short_commit_id = extract_commit_id(module_version)
            if short_commit_id:
                print(f"✨ Found short_commit_id: {short_commit_id}")

            info = get_module_info(module_name)
            path = info.get("Path")
            version = info.get("Version")
            if version.endswith("+incompatible"):
                version = version[:-13]
            if not version:
                continue

            git_url = get_git_url(module_name)
            if not git_url:
                git_url = f"https://{module_name}.git"

            print(f"✨ Git URL: {git_url}")

            commit_id = get_commit_id_from_git(git_url, version, short_commit_id)

            if not commit_id:
                print(
                    f"✨ Error: Could not retrieve commit ID for {module_name}@{version}."
                )
                continue

            sources.append(
                {
                    "type": "git",
                    "url": git_url,
                    "commit": commit_id,
                    "dest": f"src/{path.replace('.', '/')}",
                }
            )

        yaml_data = {
            "name": repo_name,
            "buildsystem": "simple",
            "build-options": {"env": {"GOBIN": "/app/bin/"}},
            "build-commands": [
                f". /usr/lib/sdk/golang/enable.sh; export GOPATH=$PWD; export GO111MODULE=off; go install {repo}/{os.path.basename(repo)}"
            ],
            "sources": sources,
        }

        print("✨ 🌟 ✨")
        print(yaml.dump(yaml_data))


if __name__ == "__main__":
    args = parse_args()
    main(args.url, args.name, args.version, args.folder)
