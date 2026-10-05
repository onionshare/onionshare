import os
import shutil
import tempfile

import pytest

from onionshare_cli.common import Common
from onionshare_cli.web import Web
from onionshare_cli.settings import Settings
from onionshare_cli.mode_settings import ModeSettings


class TestSymlinkProtection:
    """Tests for symlink vulnerabilities"""

    @pytest.fixture
    def symlink_test_setup(self, temp_dir):
        """
        Create a test environment with:
        - A shared directory containing normal files and symlinks
        - A secret file outside the shared directory
        - Symlinks pointing to the secret file
        """
        # Create a unique temp directory for this test setup
        test_temp_dir = tempfile.TemporaryDirectory(dir=temp_dir.name)

        # Create the secret file outside the shared directory
        outside_secret = os.path.join(test_temp_dir.name, "outside-secret.txt")
        with open(outside_secret, "w") as f:
            f.write("OUTSIDE_SECRET_MARKER")

        # Create the shared directory
        site_dir = os.path.join(test_temp_dir.name, "site")
        os.mkdir(site_dir)

        # Create a normal file in the shared directory
        normal_file = os.path.join(site_dir, "normal.txt")
        with open(normal_file, "w") as f:
            f.write("NORMAL_FILE_CONTENT")

        # Create a symlink to the secret inside the shared directory
        symlink_path = os.path.join(site_dir, "link.txt")
        os.symlink(outside_secret, symlink_path)

        # Create a nested directory with files and symlinks
        nested_dir = os.path.join(site_dir, "nested")
        os.mkdir(nested_dir)

        nested_file = os.path.join(nested_dir, "nested.txt")
        with open(nested_file, "w") as f:
            f.write("NESTED_FILE_CONTENT")

        nested_symlink = os.path.join(nested_dir, "nested-link.txt")
        os.symlink(outside_secret, nested_symlink)

        return {
            "temp_dir": test_temp_dir,
            "outside_secret": outside_secret,
            "site_dir": site_dir,
            "normal_file": normal_file,
            "symlink_path": symlink_path,
            "nested_dir": nested_dir,
            "nested_file": nested_file,
            "nested_symlink": nested_symlink,
        }

    def test_symlink_excluded_from_file_inventory_website_mode(
        self, symlink_test_setup, common_obj
    ):
        """Test that symlinks are excluded from file inventory in website mode"""
        web = Web(common_obj, False, ModeSettings(common_obj), "website")
        web.website_mode.set_file_info([symlink_test_setup["site_dir"]])

        # Symlinks should not be in the files dictionary
        assert "link.txt" not in web.website_mode.files
        assert "nested/nested-link.txt" not in web.website_mode.files

        # Normal files should be in the files dictionary
        assert "normal.txt" in web.website_mode.files
        assert "nested/nested.txt" in web.website_mode.files

    def test_symlink_excluded_from_file_inventory_share_mode(
        self, symlink_test_setup, common_obj
    ):
        """Test that symlinks are excluded from file inventory in share mode"""
        web = Web(common_obj, False, ModeSettings(common_obj), "share")
        web.share_mode.set_file_info([symlink_test_setup["site_dir"]])

        # Symlinks should not be in the files dictionary
        assert "link.txt" not in web.share_mode.files
        assert "nested/nested-link.txt" not in web.share_mode.files

        # Normal files should be in the files dictionary
        assert "normal.txt" in web.share_mode.files
        assert "nested/nested.txt" in web.share_mode.files

    def test_is_path_contained_normal_files(self, symlink_test_setup, common_obj):
        """Test that normal files are correctly identified as contained"""
        web = Web(common_obj, False, ModeSettings(common_obj), "website")
        web.website_mode.set_file_info([symlink_test_setup["site_dir"]])

        # Normal files should be contained
        assert web.website_mode._is_path_contained(symlink_test_setup["normal_file"])
        assert web.website_mode._is_path_contained(symlink_test_setup["nested_file"])

    def test_is_path_contained_symlinks(self, symlink_test_setup, common_obj):
        """Test that symlinks to outside are correctly identified as NOT contained"""
        web = Web(common_obj, False, ModeSettings(common_obj), "website")
        web.website_mode.set_file_info([symlink_test_setup["site_dir"]])

        # Symlinks to outside should NOT be contained
        assert not web.website_mode._is_path_contained(
            symlink_test_setup["symlink_path"]
        )
        assert not web.website_mode._is_path_contained(
            symlink_test_setup["nested_symlink"]
        )

    def test_symlink_rejected_in_website_mode_request(
        self, symlink_test_setup, common_obj
    ):
        """Test that requesting a symlink returns 404 in website mode"""
        web = Web(common_obj, False, ModeSettings(common_obj), "website")
        web.app.testing = True
        web.website_mode.set_file_info([symlink_test_setup["site_dir"]])

        with web.app.test_client() as c:
            # Requesting symlink should return 404
            res = c.get("/link.txt")
            assert res.status_code == 404

            # Normal file should return 200
            res = c.get("/normal.txt")
            assert res.status_code == 200
            assert b"NORMAL_FILE_CONTENT" in res.get_data()

    def test_symlink_rejected_in_share_mode_individual_download(
        self, symlink_test_setup, common_obj
    ):
        """Test that individual file downloads reject symlinks in share mode"""
        web = Web(common_obj, False, ModeSettings(common_obj), "share")
        web.app.testing = True
        web.settings.set("share", "autostop_sharing", False)
        web.share_mode.set_file_info([symlink_test_setup["site_dir"]])

        with web.app.test_client() as c:
            # Requesting symlink should return 404
            res = c.get("/link.txt")
            assert res.status_code == 404

            # Normal file should return 200
            res = c.get("/normal.txt")
            assert res.status_code == 200
            assert b"NORMAL_FILE_CONTENT" in res.get_data()

    def test_symlink_excluded_from_zip_archive(self, symlink_test_setup, common_obj):
        """Test that symlinks are excluded from ZIP archives"""
        import zipfile
        from io import BytesIO

        web = Web(common_obj, False, ModeSettings(common_obj), "share")
        web.app.testing = True
        web.share_mode.set_file_info([symlink_test_setup["site_dir"]])

        with web.app.test_client() as c:
            res = c.get("/download")
            assert res.status_code == 200

            # Check ZIP contents
            zip_data = BytesIO(res.get_data())
            with zipfile.ZipFile(zip_data, "r") as zf:
                zip_contents = zf.namelist()

                # Symlinks should not be in the ZIP
                assert "link.txt" not in zip_contents
                assert "nested/nested-link.txt" not in zip_contents

                # Normal files should be in the ZIP
                assert "normal.txt" in zip_contents
                assert "nested/nested.txt" in zip_contents

    def test_root_level_symlink_handling(self, temp_dir, common_obj):
        """Test that root-level symlinks (not in subdirectory) are handled correctly"""
        # Create a directory with only a symlink (no normal files)
        site_dir = os.path.join(temp_dir.name, "site-only-symlink")
        os.mkdir(site_dir)

        outside_secret = os.path.join(temp_dir.name, "secret.txt")
        with open(outside_secret, "w") as f:
            f.write("SECRET")

        symlink_path = os.path.join(site_dir, "link.txt")
        os.symlink(outside_secret, symlink_path)

        web = Web(common_obj, False, ModeSettings(common_obj), "website")
        web.website_mode.set_file_info([site_dir])

        # The symlink should not be in the file inventory
        assert "link.txt" not in web.website_mode.files

    def test_nested_symlink_chain_handling(self, temp_dir, common_obj):
        """Test that nested symlinks (symlinks within subdirectories) are handled"""
        site_dir = os.path.join(temp_dir.name, "site")
        os.mkdir(site_dir)

        outside_secret = os.path.join(temp_dir.name, "secret.txt")
        with open(outside_secret, "w") as f:
            f.write("SECRET")

        # Create nested directory structure with symlinks at various levels
        level1 = os.path.join(site_dir, "level1")
        os.mkdir(level1)

        level2 = os.path.join(level1, "level2")
        os.mkdir(level2)

        # Symlink in level1
        symlink1 = os.path.join(level1, "link1.txt")
        os.symlink(outside_secret, symlink1)

        # Symlink in level2
        symlink2 = os.path.join(level2, "link2.txt")
        os.symlink(outside_secret, symlink2)

        # Normal file in level2
        normal_file = os.path.join(level2, "normal.txt")
        with open(normal_file, "w") as f:
            f.write("NORMAL")

        web = Web(common_obj, False, ModeSettings(common_obj), "website")
        web.website_mode.set_file_info([site_dir])

        # Symlinks should not be in the file inventory
        assert "level1/link1.txt" not in web.website_mode.files
        assert "level1/level2/link2.txt" not in web.website_mode.files

        # Normal file should be in the file inventory
        assert "level1/level2/normal.txt" in web.website_mode.files

    def test_directory_symlink_handling(self, temp_dir, common_obj):
        """Test that symlinks to directories are handled correctly"""
        # Create a unique temp directory for this test
        test_temp_dir = tempfile.TemporaryDirectory(dir=temp_dir.name)

        site_dir = os.path.join(test_temp_dir.name, "site")
        os.mkdir(site_dir)

        outside_dir = os.path.join(temp_dir.name, "outside-dir")
        os.mkdir(outside_dir)

        outside_file = os.path.join(outside_dir, "outside-file.txt")
        with open(outside_file, "w") as f:
            f.write("OUTSIDE")

        # Create a symlink to a directory
        dir_symlink = os.path.join(site_dir, "link-dir")
        os.symlink(outside_dir, dir_symlink)

        # Create a normal file
        normal_file = os.path.join(site_dir, "normal.txt")
        with open(normal_file, "w") as f:
            f.write("NORMAL")

        web = Web(common_obj, False, ModeSettings(common_obj), "website")
        web.website_mode.set_file_info([site_dir])

        # The directory symlink should not be in root_files
        assert "link-dir" not in web.website_mode.root_files

        # Normal file should be in root_files
        assert "normal.txt" in web.website_mode.root_files

    def test_symlink_filtered_from_directory_listing(
        self, symlink_test_setup, common_obj
    ):
        """Test that symlinks are filtered from directory listings (not just file inventory)"""
        web = Web(common_obj, False, ModeSettings(common_obj), "website")
        web.app.testing = True
        web.website_mode.set_file_info([symlink_test_setup["site_dir"]])

        with web.app.test_client() as c:
            # Request root directory listing
            res = c.get("/")
            assert res.status_code == 200
            data = res.get_data(as_text=True)

            # Symlinks should not appear in directory listing
            assert "link.txt" not in data or "nested-link.txt" not in data

            # Normal files should appear in directory listing
            assert "normal.txt" in data

    def test_nested_symlink_filtered_from_directory_listing(
        self, symlink_test_setup, common_obj
    ):
        """Test that nested symlinks are filtered from nested directory listings"""
        web = Web(common_obj, False, ModeSettings(common_obj), "website")
        web.app.testing = True
        web.website_mode.set_file_info([symlink_test_setup["site_dir"]])

        with web.app.test_client() as c:
            # Request nested directory listing
            res = c.get("/nested/")
            assert res.status_code == 200
            data = res.get_data(as_text=True)

            # Nested symlink should not appear in directory listing
            assert "nested-link.txt" not in data

            # Normal nested file should appear in directory listing
            assert "nested.txt" in data
