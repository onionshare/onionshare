#!/usr/bin/env python3
import os
import subprocess
import yaml
import shutil
import tempfile

# Define the repositories, tags, and subfolders
repos = [
    {"url": "https://gitlab.torproject.org/tpo/anti-censorship/pluggable-transports/meek.git", "tag": "v0.38.0", "subfolder": "meek-client"},
    {"url": "https://gitlab.torproject.org/tpo/anti-censorship/pluggable-transports/snowflake.git", "tag": "v2.10.0", "subfolder": "snowflake"},
    {"url": "https://gitlab.com/yawning/obfs4.git", "tag": "obfs4proxy-0.0.14", "subfolder": "obfs4proxy"},
]

# Folder to store flatpak files
flatpak_folder = os.path.join(os.getcwd(), 'flatpak')

# Create the flatpak folder and subfolders
if not os.path.exists(flatpak_folder):
    raise RuntimeError("You do not appear to be in the onionshare repository. Please cd into it first")

# Function to run a shell command and get the output
def run_command(command, path):
    result = subprocess.run(command, shell=True, check=True, text=True, capture_output=True, cwd=path)
    return result.stdout

# Process each repository
for repo in repos:
    repo_url = repo["url"]
    tag = repo["tag"]
    subfolder = repo["subfolder"]
    
    # Clone the repository
    repo_name = repo_url.split('/')[-1].replace('.git', '')

    with tempfile.TemporaryDirectory() as td:
        print(f"Cloning {repo_url} to {td}/{subfolder}")
        run_command(f"git clone {repo_url} {subfolder}", td)
    
        # Checkout the specific tag
        print(f"Checking out {tag}")
        run_command(f"git checkout {tag}", f"{td}/{subfolder}")
    
        # Run the go command
        print(f"Running the dennwc/flatpak-go-mod to generate sources")
        run_command("go run github.com/dennwc/flatpak-go-mod@latest .", f"{td}/{subfolder}")
    
        # Copy go.mod.yml and modules.txt to the appropriate subfolder
        os.makedirs(os.path.join(flatpak_folder, subfolder), exist_ok=True)
        print(f"Copying go.mod.yml and modules.txt to {flatpak_folder}/{subfolder}")
        shutil.copy(f"{td}/{subfolder}/go.mod.yml", os.path.join(flatpak_folder, subfolder, "go.mod.yml"))
        shutil.copy(f"{td}/{subfolder}/modules.txt", os.path.join(flatpak_folder, subfolder, "modules.txt"))
    
        # Edit the go.mod.yml to change the path to include the subfolder
        go_mod_path = os.path.join(flatpak_folder, subfolder, "go.mod.yml")
        with open(go_mod_path, 'r') as f:
            go_mod_data = yaml.safe_load(f)
    
        # Traverse the YAML data to find the path: modules.txt and update it
        for item in go_mod_data:
            if isinstance(item, dict) and item.get('path') == 'modules.txt':
                print(f"Renaming the reference to modules.txt in {flatpak_folder}/{subfolder}/go.mod.yml to include the subfolder path {subfolder}")
                item['path'] = f'{subfolder}/modules.txt'
    
        # Save the edited go.mod.yml
        with open(go_mod_path, 'w') as f:
            yaml.safe_dump(go_mod_data, f)

print("Process completed.")

