from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "dooray" / "scripts"))
import drive_api as drive
from client import DoorayClient, DoorayError


class Response:
    def __init__(self, body=b"", status=200):
        self.body = io.BytesIO(body)
        self.status = status

    def read(self, size=-1):
        return self.body.read(size)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def envelope(result):
    return Response(json.dumps({"header": {"isSuccessful": True}, "result": result}).encode())


class DriveTests(unittest.TestCase):
    def setUp(self):
        self.client = DoorayClient("test-token", write_policy="allowlist", allowlist={"d1"})

    def test_list_drives_uses_client_json_endpoint(self):
        with mock.patch.object(self.client, "request", return_value=[{"id": "d1"}]) as req:
            self.assertEqual(drive.list_drives(self.client), [{"id": "d1"}])
        req.assert_called_once_with("GET", "/drive/v1/drives")

    def test_get_drive(self):
        with mock.patch.object(self.client, "request", return_value={"id": "d1"}) as req:
            self.assertEqual(drive.get_drive(self.client, "d1"), {"id": "d1"})
        req.assert_called_once_with("GET", "/drive/v1/drives/d1")

    def test_changes_use_v2(self):
        with mock.patch.object(self.client, "request", return_value=[]) as req:
            drive.get_changes(self.client, "d1")
        req.assert_called_once_with("GET", "/drive/v2/drives/d1/changes")

    def test_files_pagination_and_parent(self):
        with mock.patch.object(self.client, "request", return_value=[]) as req:
            drive.list_files(self.client, "d1", parent_id="folder", size=25, page=2)
        req.assert_called_once_with("GET", "/drive/v1/drives/d1/files",
                                    params={"size": 25, "page": 2, "parentId": "folder"})

    def test_meta_scoped_and_global(self):
        with mock.patch.object(self.client, "request", return_value={}) as req:
            drive.get_file_meta(self.client, "d1", "f1")
            drive.get_file_meta_global(self.client, "f1")
        self.assertEqual(req.call_args_list, [
            mock.call("GET", "/drive/v1/drives/d1/files/f1", params={"media": "meta"}),
            mock.call("GET", "/drive/v1/files/f1", params={"media": "meta"}),
        ])

    def test_bad_identifiers_never_reach_http(self):
        with mock.patch.object(self.client, "request") as req:
            with self.assertRaises(DoorayError):
                drive.get_file_meta(self.client, "d1", "../outside")
            with self.assertRaises(DoorayError):
                drive.list_files(self.client, "d1", parent_id="bad/slash")
        req.assert_not_called()

    def test_create_folder_respects_write_policy(self):
        denied = DoorayClient("test-token")
        with mock.patch.object(denied, "request", wraps=denied.request) as req:
            with self.assertRaisesRegex(DoorayError, "apply"):
                drive.create_folder(denied, "d1", "folder", name="new")
            with self.assertRaisesRegex(DoorayError, "disabled"):
                drive.create_folder(denied, "d1", "folder", name="new", apply=True)
        req.assert_called()

    def test_create_folder_sends_scoped_write(self):
        with mock.patch.object(self.client, "request", return_value={}) as req:
            drive.create_folder(self.client, "d1", "folder", name="new", apply=True)
        req.assert_called_once_with("POST", "/drive/v1/drives/d1/files/folder/create-folder",
                                    json_body={"name": "new"}, apply=True, resource_id="d1")

    def test_shared_links_listing(self):
        with mock.patch.object(self.client, "request", return_value=[]) as req:
            drive.list_shared_links(self.client, "d1", "f1")
        req.assert_called_once_with("GET", "/drive/v1/drives/d1/files/f1/shared-links")

    def test_shared_link_requires_member_and_expiry(self):
        with mock.patch.object(self.client, "request") as req:
            with self.assertRaises(DoorayError):
                drive.create_shared_link(self.client, "d1", "f1", expired_at="")
            with self.assertRaises(DoorayError):
                drive.create_shared_link(self.client, "d1", "f1", expired_at="2027-01-01T00:00:00Z", scope="public")
        req.assert_not_called()

    def test_download_streams_raw_to_safe_new_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(self.client, "request", return_value={"name": "report.txt"}):
                with mock.patch.object(self.client._opener, "open", return_value=Response(b"hello")) as opening:
                    dest = drive.download_file(self.client, "d1", "f1", Path(tmp))
                    self.assertEqual(dest.read_bytes(), b"hello")
                    request = opening.call_args.args[0]
                    self.assertEqual(request.full_url, "https://api.dooray.com/drive/v1/drives/d1/files/f1?media=raw")
                    self.assertEqual(request.get_header("Authorization"), "dooray-api test-token")

    def test_download_rejects_traversal_and_existing_destination(self):
        with tempfile.TemporaryDirectory() as tmp:
            for name in ("../escape", "..", "sub/file", "sub\\\\file", "C:drive", ".", "",
                         "CON", "aux.txt", "report."):
                with self.subTest(name=name), mock.patch.object(self.client, "request", return_value={"name": name}):
                    with mock.patch.object(self.client._opener, "open") as opening:
                        with self.assertRaises(DoorayError):
                            drive.download_file(self.client, "d1", "f1", Path(tmp))
                        opening.assert_not_called()
            target = Path(tmp) / "report.txt"
            target.write_bytes(b"old")
            with mock.patch.object(self.client, "request", return_value={"name": "report.txt"}):
                with mock.patch.object(self.client._opener, "open") as opening:
                    with self.assertRaises(DoorayError):
                        drive.download_file(self.client, "d1", "f1", Path(tmp))
                    opening.assert_not_called()
            self.assertEqual(target.read_bytes(), b"old")

    def test_download_cleans_partial_file_on_read_error(self):
        class Broken(Response):
            def read(self, size=-1):
                raise OSError("connection lost")
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(self.client, "request", return_value={"name": "report.txt"}):
                with mock.patch.object(self.client._opener, "open", return_value=Broken()):
                    with self.assertRaises(DoorayError):
                        drive.download_file(self.client, "d1", "f1", Path(tmp))
            self.assertFalse((Path(tmp) / "report.txt").exists())

    def test_upload_requires_apply_and_allowlisted_drive_before_io(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "file.txt"
            source.write_bytes(b"payload")
            with mock.patch("drive_api._upload_opener") as opener:
                with self.assertRaisesRegex(DoorayError, "apply"):
                    drive.upload_file(self.client, "d1", source)
                with self.assertRaisesRegex(DoorayError, "WRITE_ALLOWLIST"):
                    drive.upload_file(self.client, "d2", source, apply=True)
                opener.assert_not_called()

    def test_upload_reposts_only_to_exact_file_api_path_without_buffering(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "file.txt"
            source.write_bytes(b"payload")
            target = "https://file-api.dooray.com/uploads/drive/v1/drives/d1/files?parentId=folder"
            redirect = urllib.error.HTTPError("https://api.dooray.com/drive/v1/drives/d1/files", 307,
                                              "redirect", {"Location": target}, None)
            with mock.patch("drive_api._upload_opener") as factory:
                opener = factory.return_value
                def send(req, **kwargs):
                    self.assertEqual(req.get_header("Authorization"), "dooray-api test-token")
                    self.assertEqual(req.get_method(), "POST")
                    self.assertNotIsInstance(req.data, bytes)
                    self.assertIn(b"payload", b"".join(req.data))
                    if opener.open.call_count == 1:
                        raise redirect
                    return envelope({"id": "f1"})
                opener.open.side_effect = send
                result = drive.upload_file(self.client, "d1", source, parent_id="folder", apply=True)
            self.assertEqual(result, {"id": "f1"})
            self.assertEqual(opener.open.call_count, 2)
            self.assertEqual(opener.open.call_args.args[0].full_url, target)

    def test_upload_rejects_untrusted_redirect_without_leaking_token(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "file.txt"
            source.write_bytes(b"payload")
            valid = "https://file-api.dooray.com/uploads/drive/v1/drives/d1/files"
            for bad in ("https://evil.test/uploads/drive/v1/drives/d1/files",
                        "http://file-api.dooray.com/uploads/drive/v1/drives/d1/files",
                        "https://file-api.dooray.com:443/uploads/drive/v1/drives/d1/files",
                        "https://user@file-api.dooray.com/uploads/drive/v1/drives/d1/files",
                        valid + "/other", valid + "?parentId=other", valid + "#fragment",
                        valid.replace("/uploads/", "/uploads//")):
                with self.subTest(url=bad), mock.patch("drive_api._upload_opener") as factory:
                    factory.return_value.open.side_effect = urllib.error.HTTPError(
                        "https://api.dooray.com", 307, "redirect", {"Location": bad}, None)
                    with self.assertRaises(DoorayError):
                        drive.upload_file(self.client, "d1", source, apply=True)
                    self.assertEqual(factory.return_value.open.call_count, 1)

    def test_upload_rejects_failed_envelope_and_second_redirect(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "file.txt"
            source.write_bytes(b"payload")
            with mock.patch("drive_api._upload_opener") as factory:
                factory.return_value.open.return_value = Response(b'{"header":{"isSuccessful":false},"result":{}}')
                with self.assertRaises(DoorayError):
                    drive.upload_file(self.client, "d1", source, apply=True)

    def test_shared_link_scoped_write(self):
        with mock.patch.object(self.client, "request", return_value={"id": "link"}) as req:
            drive.create_shared_link(self.client, "d1", "f1", expired_at="2027-01-01T00:00:00Z", apply=True)
        req.assert_called_once_with("POST", "/drive/v1/drives/d1/files/f1/shared-links",
                                    json_body={"scope": "member", "expiredAt": "2027-01-01T00:00:00Z"},
                                    apply=True, resource_id="d1")


if __name__ == "__main__":
    unittest.main()
