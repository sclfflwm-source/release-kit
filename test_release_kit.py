import tempfile
import unittest
from pathlib import Path

from release_kit import changelog, checksums, env_diff, json_files, local_links, verify


class ReleaseKitTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_manifest_detects_modified_artifact(self):
        artifact = self.root / "app.zip"
        artifact.write_bytes(b"release")
        manifest = self.root / "SHA256SUMS"
        manifest.write_text("\n".join(checksums(self.root, [Path("app.zip")])) + "\n")
        self.assertEqual(verify(self.root, manifest), [])
        artifact.write_bytes(b"changed")
        self.assertIn("checksum mismatch", verify(self.root, manifest)[0])

    def test_env_compares_names_without_exposing_values(self):
        example, actual = self.root / ".env.example", self.root / ".env"
        example.write_text("API_URL=\nTOKEN=\n")
        actual.write_text("API_URL=https://example.com\nEXTRA=secret\n")
        self.assertEqual(env_diff(example, actual), [
            "missing environment key: TOKEN", "undocumented environment key: EXTRA"])

    def test_changelog_requires_version(self):
        path = self.root / "CHANGELOG.md"
        path.write_text("## [1.2.0] - 2026-09-26\n")
        self.assertEqual(changelog(path, "1.2.0"), [])
        self.assertTrue(changelog(path, "1.3.0"))

    def test_links_report_missing_local_target(self):
        path = self.root / "README.md"
        path.write_text("[good](README.md) [bad](missing.md) [web](https://example.com)")
        self.assertEqual(local_links(path), ["missing local link: missing.md"])

    def test_json_reports_syntax_error(self):
        path = self.root / "data.json"
        path.write_text("{broken")
        self.assertEqual(len(json_files([path])), 1)


if __name__ == "__main__":
    unittest.main()
