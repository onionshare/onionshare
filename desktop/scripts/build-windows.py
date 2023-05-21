#!/usr/bin/env python3
from distutils.command.build import build
import sys
import os
import inspect
import click
import shutil
import subprocess
import uuid
import xml.etree.ElementTree as ET
from glob import glob

root = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    )
)
desktop_dir = os.path.join(root, "desktop")


def get_size(dir):
    size = 0
    for path, dirs, files in os.walk(dir):
        for f in files:
            fp = os.path.join(path, f)
            size += os.path.getsize(fp)
    return size


def run(cmd, cwd=None, error_ok=False):
    print(cmd)
    try:
        subprocess.run(cmd, cwd=cwd, check=True)
    except subprocess.CalledProcessError as e:
        if not error_ok:
            raise subprocess.CalledProcessError(e)


def sign(filename):
    click.echo(f"> Signing {filename}")
    run(
        [
            shutil.which("signtool"),
            "sign",
            "/v",
            "/d",
            "OnionShare",
            "/sha1",
            "1a0345732140749bdaa03efe8591b2c2a036884c",
            "/fd",
            "SHA256",
            "/td",
            "SHA256",
            "/tr",
            "http://timestamp.digicert.com",
            filename,
        ]
    )


def wix_build_data(dirname, dir_prefix, id_, name):
    data = {
        "id": id_,
        "name": name,
        "files": [],
        "dirs": [],
    }

    for basename in os.listdir(dirname):
        filename = os.path.join(dirname, basename)
        if os.path.isfile(filename):
            data["files"].append(os.path.join(dir_prefix, basename))
        elif os.path.isdir(filename):
            if id_ == "INSTALLDIR":
                id_prefix = "Folder"
            else:
                id_prefix = id_

            # Skip lib/Pyside2/Examples folder
            if "\\lib\\PySide2\\examples" in dirname:
                continue

            id_value = f"{id_prefix}{basename.capitalize().replace('-', '_')}"
            data["dirs"].append(
                wix_build_data(
                    os.path.join(dirname, basename),
                    os.path.join(dir_prefix, basename),
                    id_value,
                    basename,
                )
            )

    if len(data["files"]) > 0:
        if id_ == "INSTALLDIR":
            data["component_id"] = "ApplicationFiles"
        else:
            data["component_id"] = "FolderComponent" + id_[len("Folder") :]
        data["component_guid"] = str(uuid.uuid4())

    return data


def wix_build_dir_xml(root, data):
    attrs = {}
    if "id" in data:
        attrs["Id"] = data["id"]
    if "name" in data:
        attrs["Name"] = data["name"]
    el = ET.SubElement(root, "Directory", attrs)
    for subdata in data["dirs"]:
        wix_build_dir_xml(el, subdata)

    # If this is the ProgramMenuFolder, add the menu component
    if "id" in data and data["id"] == "ProgramMenuFolder":
        component_el = ET.SubElement(
            el,
            "Component",
            Id="ApplicationShortcuts",
            Guid="539e7de8-a124-4c09-aa55-0dd516aad7bc",
        )
        ET.SubElement(
            component_el,
            "Shortcut",
            Id="ApplicationShortcut1",
            Name="OnionShare",
            Description="OnionShare",
            Target="[INSTALLDIR]onionshare.exe",
            WorkingDirectory="INSTALLDIR",
        )
        ET.SubElement(
            component_el,
            "RegistryValue",
            Root="HKCU",
            Key="Software\OnionShare",
            Name="installed",
            Type="integer",
            Value="1",
            KeyPath="yes",
        )


def wix_build_components_xml(root, data):
    component_ids = []
    if "component_id" in data:
        component_ids.append(data["component_id"])

    for subdata in data["dirs"]:
        if "component_guid" in subdata:
            dir_ref_el = ET.SubElement(root, "DirectoryRef", Id=subdata["id"])
            component_el = ET.SubElement(
                dir_ref_el,
                "Component",
                Id=subdata["component_id"],
                Guid=subdata["component_guid"],
            )
            for filename in subdata["files"]:
                file_el = ET.SubElement(
                    component_el, "File", Source=filename, Id="file_" + uuid.uuid4().hex
                )

        component_ids += wix_build_components_xml(root, subdata)

    return component_ids


def msi_package(build_path, msi_path, product_update_code):
    print(f"> Build the WiX file")
    version_filename = os.path.join(
        build_path, "lib", "onionshare_cli", "resources", "version.txt"
    )
    with open(version_filename) as f:
        version = f.read().strip()
        # change a version like 2.6.dev1 to just 2.6, for cx_Freeze's sake
        last_digit = version[-1]
        if version.endswith(f".dev{last_digit}"):
            version = version[0:-5]

    data = {
        "id": "TARGETDIR",
        "name": "SourceDir",
        "dirs": [
            {
                "id": "ProgramFilesFolder",
                "dirs": [],
            },
            {
                "id": "ProgramMenuFolder",
                "dirs": [],
            },
        ],
    }

    data["dirs"][0]["dirs"].append(
        wix_build_data(
            build_path,
            ".",
            "INSTALLDIR",
            "OnionShare",
        )
    )

    root_el = ET.Element("Wix", xmlns="http://schemas.microsoft.com/wix/2006/wi")
    product_el = ET.SubElement(
        root_el,
        "Product",
        Name="OnionShare",
        Manufacturer="Micah Lee, et al.",
        Id="*",
        UpgradeCode="$(var.ProductUpgradeCode)",
        Language="1033",
        Codepage="1252",
        Version="$(var.ProductVersion)",
    )
    ET.SubElement(
        product_el,
        "Package",
        Id="*",
        Keywords="Installer",
        Description="OnionShare $(var.ProductVersion) Installer",
        Manufacturer="Micah Lee, et al.",
        InstallerVersion="100",
        Languages="1033",
        Compressed="yes",
        SummaryCodepage="1252",
    )
    ET.SubElement(product_el, "Media", Id="1", Cabinet="product.cab", EmbedCab="yes")
    ET.SubElement(
        product_el,
        "Icon",
        Id="ProductIcon",
        SourceFile=os.path.join(
            desktop_dir, "onionshare", "resources", "onionshare.ico"
        ),
    )
    ET.SubElement(product_el, "Property", Id="ARPPRODUCTICON", Value="ProductIcon")
    ET.SubElement(
        product_el,
        "Property",
        Id="ARPHELPLINK",
        Value="https://docs.onionshare.org",
    )
    ET.SubElement(
        product_el,
        "Property",
        Id="ARPURLINFOABOUT",
        Value="https://onionshare.org",
    )
    ET.SubElement(product_el, "UIRef", Id="WixUI_Minimal")
    ET.SubElement(product_el, "UIRef", Id="WixUI_ErrorProgressText")
    ET.SubElement(
        product_el,
        "WixVariable",
        Id="WixUILicenseRtf",
        Value=os.path.join(desktop_dir, "package", "license.rtf"),
    )
    ET.SubElement(
        product_el,
        "WixVariable",
        Id="WixUIDialogBmp",
        Value=os.path.join(desktop_dir, "package", "dialog.bmp"),
    )
    ET.SubElement(
        product_el,
        "MajorUpgrade",
        AllowSameVersionUpgrades="yes",
        DowngradeErrorMessage="A newer version of [ProductName] is already installed. If you are sure you want to downgrade, remove the existing installation via Programs and Features.",
    )

    wix_build_dir_xml(product_el, data)
    component_ids = wix_build_components_xml(product_el, data)

    feature_el = ET.SubElement(product_el, "Feature", Id="DefaultFeature", Level="1")
    for component_id in component_ids:
        ET.SubElement(feature_el, "ComponentRef", Id=component_id)
    ET.SubElement(feature_el, "ComponentRef", Id="ApplicationShortcuts")

    with open(os.path.join(build_path, "OnionShare.wxs"), "w") as f:
        f.write('<?xml version="1.0" encoding="windows-1252"?>\n')
        f.write(f'<?define ProductVersion = "{version}"?>\n')
        f.write(f'<?define ProductUpgradeCode = "{product_update_code}"?>\n')

        ET.indent(root_el)
        f.write(ET.tostring(root_el).decode())

    print(f"> Build the MSI")
    run(
        [shutil.which("candle.exe"), "OnionShare.wxs"],
        build_path,
    )
    run(
        [shutil.which("light.exe"), "-ext", "WixUIExtension", "OnionShare.wixobj"],
        build_path,
    )

    print(f"> Prepare OnionShare.msi for signing")
    run(
        [
            shutil.which("insignia.exe"),
            "-im",
            os.path.join(build_path, "OnionShare.msi"),
        ],
        error_ok=True,
    )
    sign(os.path.join(build_path, "OnionShare.msi"))

    print(f"> Final MSI: {msi_path}")
    os.makedirs(os.path.join(desktop_dir, "dist"), exist_ok=True)
    os.rename(
        os.path.join(build_path, "OnionShare.msi"),
        msi_path,
    )


@click.group()
def main():
    """
    Windows build tasks
    """


@main.command()
def cleanup_build():
    """Delete unused PySide6 stuff to save space"""
    build_path = os.path.join(desktop_dir, "build", "exe.win-amd64-3.10")
    before_size = get_size(build_path)

    for dirname in ["qml"]:
        shutil.rmtree(os.path.join(build_path, "lib", "PySide6", dirname))
    for dirname in [
        "assetimporters",
        "designer",
        "generic",
        "geometryloaders",
        "platforminputcontexts",
        "position",
        "qmltooling",
        "renderers",
        "renderplugins",
        "sceneparsers",
        "scxmldatamodel",
        "sensors",
        "sqldrivers",
        "styles",
    ]:
        shutil.rmtree(os.path.join(build_path, "lib", "PySide6", "plugins", dirname))
    for filename in (
        glob(os.path.join(build_path, "lib", "PySide6", "*.exe"))
        + glob(os.path.join(build_path, "lib", "PySide6", "Qt3D*"))
        + glob(os.path.join(build_path, "lib", "PySide6", "Qt63D*"))
        + glob(os.path.join(build_path, "lib", "PySide6", "Qt6Bluetooth.*"))
        + glob(os.path.join(build_path, "lib", "PySide6", "Qt6Charts*"))
        + glob(os.path.join(build_path, "lib", "PySide6", "Qt6Concurrent.*"))
        + glob(os.path.join(build_path, "lib", "PySide6", "Qt6DataVisualization*"))
        + glob(os.path.join(build_path, "lib", "PySide6", "Qt6Bus.dll"))
        + glob(os.path.join(build_path, "lib", "PySide6", "Qt6Designer*"))
        + glob(os.path.join(build_path, "lib", "PySide6", "Qt6Help.dll"))
        + glob(os.path.join(build_path, "lib", "PySide6", "Qt6Labs*"))
        + glob(os.path.join(build_path, "lib", "PySide6", "Qt6Multimedia*"))
        + glob(os.path.join(build_path, "lib", "PySide6", "Qt6Nfc.dll"))
        + glob(os.path.join(build_path, "lib", "PySide6", "Qt6OpenGL*"))
        + glob(os.path.join(build_path, "lib", "PySide6", "Qt6Qml*"))
        + glob(os.path.join(build_path, "lib", "PySide6", "Qt6Quick*"))
        + glob(os.path.join(build_path, "lib", "PySide6", "Qt6RemoteObjects*"))
        + glob(os.path.join(build_path, "lib", "PySide6", "Qt6Scxml*"))
        + glob(os.path.join(build_path, "lib", "PySide6", "Qt6Sensors*"))
        + glob(os.path.join(build_path, "lib", "PySide6", "Qt6SerialPort.*"))
        + glob(os.path.join(build_path, "lib", "PySide6", "Qt6ShaderTools.*"))
        + glob(os.path.join(build_path, "lib", "PySide6", "Qt6Sql.*"))
        + glob(os.path.join(build_path, "lib", "PySide6", "Qt6StateMachine*"))
        + glob(os.path.join(build_path, "lib", "PySide6", "Qt6Test.*"))
        + glob(os.path.join(build_path, "lib", "PySide6", "Qt6VirtualKeyboard.*"))
        + glob(os.path.join(build_path, "lib", "PySide6", "Qt6Web*"))
    ):
        os.remove(filename)

    after_size = get_size(build_path)
    freed_bytes = before_size - after_size
    freed_mb = int(freed_bytes / 1024 / 1024)
    print(f"Freed {freed_mb} mb")


@main.command()
@click.argument("path")
def codesign(path):
    """Sign Windows binaries before packaging"""
    if not os.path.isdir(path):
        click.echo("Invalid build path")
        return

    sign(os.path.join(path, "onionshare.exe"))
    sign(os.path.join(path, "onionshare-cli.exe"))
    sign(
        os.path.join(
            path,
            "lib",
            "onionshare",
            "resources",
            "tor",
            "meek-client.exe",
        )
    )
    sign(
        os.path.join(
            path,
            "lib",
            "onionshare",
            "resources",
            "tor",
            "obfs4proxy.exe",
        )
    )
    sign(
        os.path.join(
            path,
            "lib",
            "onionshare",
            "resources",
            "tor",
            "snowflake-client.exe",
        )
    )


@main.command()
@click.argument("path")
def package(path):
    """Build the MSI package"""
    version_filename = os.path.join(
        root, "cli", "onionshare_cli", "resources", "version.txt"
    )
    with open(version_filename) as f:
        version = f.read().strip()

    msi_package(
        path,
        os.path.join(desktop_dir, "dist", f"OnionShare-win64-{version}.msi"),
        "ed7f9243-3528-4b4a-b85c-9943982e75eb",
    )


if __name__ == "__main__":
    main()
