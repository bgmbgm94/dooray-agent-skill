from __future__ import annotations

import io
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "dooray" / "scripts"))
from client import DoorayClient, DoorayError, path_id


class _Response:
    def __init__(self, data: bytes):
        self.data = data

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.data


class ClientTests(unittest.TestCase):
    def test_default_deny_and_explicit_apply(self):
        client = DoorayClient("dummy-token")
        with self.assertRaisesRegex(DoorayError, "apply"):
            client.request("POST", "/project/v1/projects/123/posts", json_body={}, resource_id="123")
        with self.assertRaisesRegex(DoorayError, "disabled"):
            client.request("POST", "/project/v1/projects/123/posts", json_body={}, apply=True, resource_id="123")

    def test_allowlist_applies_to_destination(self):
        client = DoorayClient("dummy-token", write_policy="allowlist", allowlist={"123"})
        with self.assertRaisesRegex(DoorayError, "WRITE_ALLOWLIST"):
            client.request("POST", "/project/v1/projects/other/posts", json_body={}, apply=True, resource_id="other")

    def test_successful_envelope_and_authorization_scheme(self):
        client = DoorayClient("dummy-token")
        response = _Response(b'{"header":{"isSuccessful":true},"result":[{"id":"p1"}]}')
        with mock.patch.object(client._opener, "open", return_value=response) as opening:
            self.assertEqual(client.request("GET", "/project/v1/projects"), [{"id": "p1"}])
        request = opening.call_args.args[0]
        self.assertEqual(request.get_header("Authorization"), "dooray-api dummy-token")

    def test_bad_envelope_is_error(self):
        client = DoorayClient("dummy-token")
        response = _Response(b'{"header":{"isSuccessful":false},"result":null}')
        with mock.patch.object(client._opener, "open", return_value=response):
            with self.assertRaises(DoorayError):
                client.request("GET", "/account/v1/me")

    def test_unsafe_paths_and_insecure_base_are_rejected(self):
        with self.assertRaises(DoorayError):
            DoorayClient("dummy-token", api_base="http://api.dooray.com")
        client = DoorayClient("dummy-token")
        for path in ("//external.invalid/path", "/project/../account", "https://external.invalid/path"):
            with self.subTest(path=path), self.assertRaises(DoorayError):
                client.request("GET", path)
        with self.assertRaises(DoorayError):
            path_id("../path")


if __name__ == "__main__":
    unittest.main()
