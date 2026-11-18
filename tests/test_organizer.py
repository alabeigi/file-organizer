import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from organizer import move_file, plan_moves


SCRIPT = Path(__file__).resolve().parents[1] / "organizer.py"


class OrganizerTests(unittest.TestCase):
    def setUp(self):
        temporary_directory = TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        self.folder = Path(temporary_directory.name)

    def run_cli(self, *options, folder=None):
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(folder or self.folder), *options],
            capture_output=True,
            text=True,
        )

    def test_dry_run_previews_collision_without_creating_folders(self):
        (self.folder / "Documents").mkdir()
        (self.folder / "Documents/report.pdf").write_text("existing")
        (self.folder / "report.pdf").write_text("incoming")
        (self.folder / "photo.JPG").touch()

        result = self.run_cli("--dry-run")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("report.pdf -> Documents/report_1.pdf", result.stdout)
        self.assertIn("photo.JPG -> Images/photo.JPG", result.stdout)
        self.assertTrue((self.folder / "report.pdf").is_file())
        self.assertTrue((self.folder / "photo.JPG").is_file())
        self.assertFalse((self.folder / "Documents/report_1.pdf").exists())
        self.assertFalse((self.folder / "Images").exists())

    def test_moves_files_and_preserves_existing_files(self):
        (self.folder / "Documents").mkdir()
        (self.folder / "Documents/report.pdf").write_text("existing")
        (self.folder / "Documents/report_1.pdf").write_text("also existing")
        (self.folder / "report.pdf").write_text("incoming")
        (self.folder / "photo.JPG").touch()
        (self.folder / "backup.tar.gz").touch()
        (self.folder / "no-extension").touch()

        result = self.run_cli()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.folder / "Documents/report.pdf").read_text(), "existing")
        self.assertEqual((self.folder / "Documents/report_1.pdf").read_text(), "also existing")
        self.assertEqual((self.folder / "Documents/report_2.pdf").read_text(), "incoming")
        self.assertTrue((self.folder / "Images/photo.JPG").is_file())
        self.assertTrue((self.folder / "Archives/backup.tar.gz").is_file())
        self.assertTrue((self.folder / "Others/no-extension").is_file())
        self.assertFalse((self.folder / "report.pdf").exists())

        second_run = self.run_cli()
        self.assertEqual(second_run.returncode, 0, second_run.stderr)
        self.assertEqual(second_run.stdout.strip(), "No files to organize.")

    def test_skips_dotfiles_symlinks_and_nested_files(self):
        (self.folder / ".hidden.pdf").touch()
        (self.folder / "nested").mkdir()
        target = self.folder / "nested/image.png"
        target.touch()
        link = self.folder / "linked.png"
        try:
            link.symlink_to(target)
        except OSError as error:
            self.skipTest(f"Cannot create a symlink: {error}")

        result = self.run_cli()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "No files to organize.")
        self.assertTrue((self.folder / ".hidden.pdf").is_file())
        self.assertTrue(link.is_symlink())
        self.assertTrue(target.is_file())

    def test_refuses_symlinked_category(self):
        (self.folder / "elsewhere").mkdir()
        try:
            (self.folder / "Images").symlink_to(self.folder / "elsewhere", target_is_directory=True)
        except OSError as error:
            self.skipTest(f"Cannot create a symlink: {error}")
        (self.folder / "photo.jpg").touch()

        result = self.run_cli()

        self.assertEqual(result.returncode, 1)
        self.assertIn("Cannot use", result.stderr)
        self.assertTrue((self.folder / "photo.jpg").is_file())
        self.assertEqual(list((self.folder / "elsewhere").iterdir()), [])

    def test_missing_folder_has_a_nonzero_exit_status(self):
        result = self.run_cli(folder=self.folder / "missing")

        self.assertEqual(result.returncode, 1)
        self.assertIn("missing", result.stderr)

    def test_file_appearing_after_planning_is_preserved(self):
        (self.folder / "report.pdf").write_text("incoming")
        [(source, destination)] = plan_moves(self.folder)
        destination.parent.mkdir()
        destination.write_text("created after planning")

        with self.assertRaises(FileExistsError):
            move_file(source, destination)

        self.assertEqual(destination.read_text(), "created after planning")
        self.assertEqual(source.read_text(), "incoming")

    def test_failed_replace_removes_the_reserved_file(self):
        (self.folder / "report.pdf").write_text("incoming")
        [(source, destination)] = plan_moves(self.folder)

        with patch.object(Path, "replace", side_effect=PermissionError("move denied")):
            with self.assertRaises(PermissionError):
                move_file(source, destination)

        self.assertFalse(destination.exists())
        self.assertEqual(source.read_text(), "incoming")


if __name__ == "__main__":
    unittest.main()
