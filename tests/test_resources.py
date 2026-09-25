"""Public-resource contract tests; no credentials or real Dooray requests."""
from __future__ import annotations

import importlib
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock

SCRIPTS = Path(__file__).resolve().parents[1] / "skills" / "dooray" / "scripts"
sys.path.insert(0, str(SCRIPTS))
client_mod = importlib.import_module("client")
project = importlib.import_module("project_api")
post = importlib.import_module("post_api")
wiki = importlib.import_module("wiki_api")
drive = importlib.import_module("drive_api")


class MockResponse:
    def __init__(self, result):
        self.raw = json.dumps({"header": {"isSuccessful": True}, "result": result}).encode()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.raw


class ResourceTests(unittest.TestCase):
    def setUp(self):
        self.client = client_mod.DoorayClient(token="dummy-test-only", write_policy="allow")
        self.requests = []

        def fake_open(request, timeout):
            self.requests.append(request)
            return MockResponse({"id": "test-result"})

        self.client._opener = Mock(open=fake_open)

    def test_project_list_member_me_and_filters(self):
        self.assertEqual(project.list_projects(self.client, state="active"), {"id": "test-result"})
        req = self.requests[0]
        self.assertEqual(req.get_method(), "GET")
        self.assertIn("/project/v1/projects?member=me&size=100&state=active", req.full_url)
        with self.assertRaises(ValueError):
            project.list_projects(self.client, size=101)

    def test_posts_listing_detail_and_filter_whitelist(self):
        post.list_posts(self.client, "p1", toMemberIds="me", postWorkflowClasses="working")
        self.assertIn("/projects/p1/posts?page=0&size=20&toMemberIds=me&postWorkflowClasses=working", self.requests[0].full_url)
        post.get_post(self.client, "p1", "task2")
        self.assertTrue(self.requests[1].full_url.endswith("/projects/p1/posts/task2"))
        with self.assertRaises(ValueError):
            post.list_posts(self.client, "p1", unsupported="x")
        with self.assertRaises(client_mod.DoorayError):
            post.get_post(self.client, "../elsewhere", "task2")

    def test_create_post_requires_apply_and_client_policy(self):
        with self.assertRaises(ValueError):
            post.create_post(self.client, "p1", subject="Title", content="Body")
        self.assertEqual(self.requests, [])
        post.create_post(self.client, "p1", subject="Title", content="Body", apply=True)
        req = self.requests[0]
        self.assertEqual(req.get_method(), "POST")
        self.assertEqual(json.loads(req.data), {"subject": "Title", "body": {"mimeType": "text/x-markdown", "content": "Body"}})
        denied = client_mod.DoorayClient(token="dummy-test-only", write_policy="deny")
        denied._opener = self.client._opener
        with self.assertRaises(client_mod.DoorayError):
            post.create_post(denied, "p1", subject="Title", content="Body", apply=True)
        self.assertEqual(len(self.requests), 1)

    def test_wiki_read_and_write(self):
        wiki.list_wikis(self.client, page=0, size=10)
        wiki.list_pages(self.client, "w1", parent_page_id="root")
        wiki.get_page(self.client, "w1", "page2")
        self.assertTrue(self.requests[0].full_url.endswith("/wiki/v1/wikis?page=0&size=10"))
        self.assertTrue(self.requests[1].full_url.endswith("/wiki/v1/wikis/w1/pages?parentPageId=root"))
        self.assertTrue(self.requests[2].full_url.endswith("/wiki/v1/wikis/w1/pages/page2"))
        with self.assertRaises(ValueError):
            wiki.create_page(self.client, "w1", subject="S", content="C")
        with self.assertRaises(ValueError):
            wiki.update_page(self.client, "w1", "page2", subject="S", content="C")
        self.assertEqual(len(self.requests), 3)
        wiki.create_page(self.client, "w1", subject="S", content="C", parent_page_id="root", apply=True)
        wiki.update_page(self.client, "w1", "page2", subject="S2", content="C2", apply=True)
        self.assertEqual([r.get_method() for r in self.requests[3:]], ["POST", "PUT"])
        self.assertEqual(json.loads(self.requests[3].data)["parentPageId"], "root")
        self.assertEqual(json.loads(self.requests[4].data), {"subject": "S2", "body": {"mimeType": "text/x-markdown", "content": "C2"}})

    def test_drive_fails_closed_without_documented_endpoint(self):
        for action, args in ((drive.list_drives, ()), (drive.list_files, ("d",)), (drive.get_file, ("d", "f"))):
            with self.assertRaises(drive.UnsupportedDriveAPI):
                action(self.client, *args)
        self.assertEqual(self.requests, [])


if __name__ == "__main__":
    unittest.main()
