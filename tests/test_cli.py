from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "dooray" / "scripts"))
from dooray import DOMAINS, build_parser, run


class CliTests(unittest.TestCase):
    def test_command_surface_contains_no_administrative_domain(self):
        self.assertEqual(set(DOMAINS), {"me", "project", "post", "wiki", "calendar", "messenger"})
        self.assertNotIn("admin", build_parser().format_help().lower())

    def test_project_query_does_not_write(self):
        args = build_parser().parse_args(["project", "list"])
        client = mock.Mock()
        client.request.return_value = []
        self.assertEqual(run(args, client), [])
        client.request.assert_called_once_with("GET", "/project/v1/projects")

    def test_post_path_rejects_injected_id(self):
        args = build_parser().parse_args(["post", "get", "../other", "p-1"])
        with self.assertRaisesRegex(Exception, "Invalid resource ID"):
            run(args, mock.Mock())

    def test_calendar_whole_day_create_is_not_sent_without_apply(self):
        from client import DoorayClient, DoorayError
        args = build_parser().parse_args([
            "calendar", "event-create", "calendar-1", "--subject", "Holiday",
            "--started-at", "2026-09-21", "--ended-at", "2026-09-21",
            "--whole-day", "--to", "member-1",
        ])
        client = DoorayClient("dummy-token", write_policy="allow")
        with mock.patch.object(client._opener, "open") as network:
            with self.assertRaisesRegex(DoorayError, "apply"):
                run(args, client)
            network.assert_not_called()

    def test_messenger_send_is_not_sent_without_apply(self):
        from client import DoorayClient, DoorayError
        args = build_parser().parse_args(["messenger", "direct-send", "--to", "member-1", "--text", "Hello"])
        client = DoorayClient("dummy-token", write_policy="allow")
        with mock.patch.object(client._opener, "open") as network:
            with self.assertRaisesRegex(DoorayError, "apply"):
                run(args, client)
            network.assert_not_called()


if __name__ == "__main__":
    unittest.main()
