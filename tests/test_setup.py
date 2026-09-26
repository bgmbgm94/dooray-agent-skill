from __future__ import annotations

import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "dooray" / "scripts" / "setup.sh"
BASH = str(Path("C:/Program Files/Git/bin/bash.exe")) if os.name == "nt" else shutil.which("bash")
sys.path.insert(0, str(SCRIPT.parent))
from client import DoorayClient, DoorayError


class SetupTests(unittest.TestCase):
    def test_setup_saves_hidden_token_and_allowlist_outside_repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = dict(os.environ, HOME=tmp, USERPROFILE=tmp)
            proc = subprocess.run([BASH, "scripts/setup.sh"], input="id:example-secret\nproject123\ndrive456\n\n",
                                  text=True, capture_output=True, env=env, check=False, cwd=ROOT / "skills" / "dooray")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertNotIn("example-secret", proc.stdout + proc.stderr)
            self.assertEqual((Path(tmp) / ".dooray-token").read_text(), "id:example-secret\n")
            self.assertEqual((Path(tmp) / ".dooray-whitelist").read_text(), "project123\ndrive456\n")
            if os.name != "nt":
                self.assertEqual(stat.S_IMODE((Path(tmp) / ".dooray-token").stat().st_mode), 0o600)
                self.assertEqual(stat.S_IMODE((Path(tmp) / ".dooray-whitelist").stat().st_mode), 0o600)

    def test_whitelist_only_does_not_rewrite_token(self):
        with tempfile.TemporaryDirectory() as tmp:
            token = Path(tmp) / ".dooray-token"
            token.write_text("existing-secret\n")
            proc = subprocess.run([BASH, "scripts/setup.sh", "--whitelist"], input="drive456\n\n",
                                  text=True, capture_output=True,
                                  env=dict(os.environ, HOME=tmp, USERPROFILE=tmp), check=False,
                                  cwd=ROOT / "skills" / "dooray")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(token.read_text(), "existing-secret\n")
            self.assertEqual((Path(tmp) / ".dooray-whitelist").read_text(), "drive456\n")

    def test_file_allowlist_is_used_only_when_explicit_allowlist_policy_selected(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, ".dooray-whitelist").write_text("project123\n")
            with mock.patch("client.Path.home", return_value=Path(tmp)), mock.patch.dict(
                    os.environ, {"DOORAY_WRITE_POLICY": "allowlist"}, clear=True):
                client = DoorayClient("dummy-token")
            self.assertEqual(client.allowlist, {"project123"})
            with self.assertRaisesRegex(DoorayError, "WRITE_ALLOWLIST"):
                client.request("POST", "/project/v1/projects/other/posts", json_body={}, apply=True, resource_id="other")

    def test_explicit_empty_env_allowlist_overrides_saved_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, ".dooray-whitelist").write_text("project123\n")
            for value in ("", "  "):
                with self.subTest(value=value), mock.patch("client.Path.home", return_value=Path(tmp)), mock.patch.dict(
                        os.environ, {"DOORAY_WRITE_POLICY": "allowlist", "DOORAY_WRITE_ALLOWLIST": value}):
                    client = DoorayClient("dummy-token")
                self.assertEqual(client.allowlist, set())
                with self.assertRaisesRegex(DoorayError, "WRITE_ALLOWLIST"):
                    client.request("POST", "/project/v1/projects/project123/posts",
                                   json_body={}, apply=True, resource_id="project123")

    def test_empty_file_allowlist_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, ".dooray-whitelist").write_text("")
            with mock.patch("client.Path.home", return_value=Path(tmp)), mock.patch.dict(
                    os.environ, {"DOORAY_WRITE_POLICY": "allowlist"}, clear=True):
                client = DoorayClient("dummy-token")
            self.assertEqual(client.allowlist, set())
            with self.assertRaises(DoorayError):
                client.request("POST", "/project/v1/projects/a/posts", json_body={}, apply=True, resource_id="a")


if __name__ == "__main__":
    unittest.main()
