"""Offline contract tests derived from public dooray-sdk calendar endpoints and model."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "dooray" / "scripts"))
import calendar_api as calendar


class RecordingClient:
    def __init__(self):
        self.calls = []

    def request(self, method, path, params=None, json_body=None, apply=False, resource_id=None):
        args = (method, path, params, json_body, apply, resource_id)
        self.calls.append(args)
        return {"recorded": args}


class CalendarTests(unittest.TestCase):
    def test_inclusive_whole_day_range_with_offset_and_calendar_rollover(self):
        self.assertEqual(calendar.whole_day_range("2026-12-31", "2027-01-01", timezone="-05:00"),
                         ("2026-12-31-05:00", "2027-01-02-05:00"))

    def test_whole_day_range_rejects_invalid_or_reversed_dates(self):
        for start, end in [("2026-02-30", "2026-03-01"), ("2026-04-02", "2026-04-01"),
                           ("2026-1-01", "2026-01-02")]:
            with self.subTest(start=start, end=end), self.assertRaises(ValueError):
                calendar.whole_day_range(start, end)

    def test_named_timezone_recalculates_offset_across_dst(self):
        self.assertEqual(calendar.whole_day_range("2026-03-07", "2026-03-08", timezone="America/New_York"),
                         ("2026-03-07-05:00", "2026-03-09-04:00"))

    def test_event_body_matches_public_sdk_model(self):
        body = calendar.event_body(subject="Holiday", body_markdown="Day off", started_at="2026-09-21",
                                   ended_at="2026-09-21", whole_day=True, location="Office",
                                   who_organization_member_ids=["member-1"])
        self.assertEqual(body, {
            "subject": "Holiday", "body": {"mimeType": "text/x-markdown", "content": "Day off"},
            "startedAt": "2026-09-21+09:00", "endedAt": "2026-09-22+09:00", "wholeDayFlag": True,
            "location": "Office", "users": {"to": [{"type": "member", "member": {"organizationMemberId": "member-1"}}]},
        })

    def test_timed_event_requires_aware_ordered_iso_datetimes(self):
        for start, end in [("2026-09-21T10:00:00", "2026-09-21T11:00:00+09:00"),
                           ("2026-09-21T11:00:00+09:00", "2026-09-21T10:00:00+09:00")]:
            with self.subTest(start=start), self.assertRaises(ValueError):
                calendar.event_body("Meeting", "Agenda", start, end)

    def test_create_event_forwards_apply_and_calendar_id_to_client(self):
        client = RecordingClient()
        result = calendar.create_event("calendar-1", subject="Meeting", body_markdown="Agenda",
                                       started_at="2026-09-21T10:00:00+09:00",
                                       ended_at="2026-09-21T11:00:00+09:00", apply=True, client=client)
        method, path, params, body, apply, resource_id = client.calls[0]
        self.assertEqual((method, path, params, apply, resource_id),
                         ("POST", "/calendar/v1/calendars/calendar-1/events", None, True, "calendar-1"))
        self.assertFalse(body["wholeDayFlag"])
        self.assertEqual(result["recorded"], client.calls[0])

    def test_calendar_read_endpoints(self):
        client = RecordingClient()
        calendar.list_calendars(client=client)
        calendar.list_events("2026-09-21T00:00:00+09:00", "2026-09-22T00:00:00+09:00",
                             calendars=["calendar-1", "calendar-2"], client=client)
        self.assertEqual(client.calls[0][:2], ("GET", "/calendar/v1/calendars"))
        self.assertEqual(client.calls[1][:3], ("GET", "/calendar/v1/calendars/*/events",
                                               {"timeMin": "2026-09-21T00:00:00+09:00",
                                                "timeMax": "2026-09-22T00:00:00+09:00",
                                                "calendars": "calendar-1,calendar-2"}))

    def test_update_whole_day_event_explicitly_preserves_flag(self):
        client = RecordingClient()
        calendar.update_event("calendar-1", "event-1", subject="Holiday updated",
                              body_markdown="Agenda", started_at="2026-09-21",
                              ended_at="2026-09-21", whole_day=True,
                              who_organization_member_ids=["member-1"],
                              apply=True, client=client)
        method, path, params, body, apply, resource_id = client.calls[0]
        self.assertEqual((method, path, apply, resource_id),
                         ("PUT", "/calendar/v1/calendars/calendar-1/events/event-1", True, "calendar-1"))
        self.assertTrue(body["wholeDayFlag"])
        self.assertEqual(body["endedAt"], "2026-09-22+09:00")

    def test_update_event_without_apply_never_sends(self):
        from client import DoorayClient, DoorayError
        from unittest import mock
        client = DoorayClient("dummy", write_policy="allow")
        with mock.patch.object(client._opener, "open") as network:
            with self.assertRaisesRegex(DoorayError, "apply"):
                calendar.update_event("calendar-1", "event-1", subject="Holiday",
                                      body_markdown="", started_at="2026-09-21",
                                      ended_at="2026-09-21", whole_day=True, client=client)
            network.assert_not_called()

    def test_rejects_unsafe_path_id(self):
        with self.assertRaises(ValueError):
            calendar.create_event("a/b", subject="Meeting", body_markdown="x", started_at="2026-09-21",
                                  ended_at="2026-09-21", whole_day=True, client=RecordingClient())


if __name__ == "__main__":
    unittest.main()
