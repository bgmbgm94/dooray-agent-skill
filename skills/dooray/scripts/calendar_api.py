"""Small Dooray calendar adapter. Endpoint and payload evidence:
https://github.com/dooray-go/dooray-sdk/blob/v0.9.0/openapi/calendar/getevents.go
https://github.com/dooray-go/dooray-sdk/blob/v0.9.0/openapi/calendar/postevents.go
https://github.com/dooray-go/dooray-sdk/blob/v0.9.0/openapi/model/calendar/postevent_request.go
https://github.com/dooray-go/dooray-sdk/blob/v0.9.0/utils/dateutils.go

Date-only input is a user-inclusive range; Dooray receives a next-day exclusive end.
Writes are never sent directly: DoorayClient.request enforces apply/write policy.
"""
from __future__ import annotations

import re
from datetime import date, datetime, time, timedelta, timezone as fixed_timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


_DATE = re.compile(r"\d{4}-\d{2}-\d{2}\Z")
_OFFSET = re.compile(r"([+-])(\d{2}):(\d{2})\Z")
_PATH_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*\Z")


def _client(client):
    if client is not None:
        return client
    from client import DoorayClient
    return DoorayClient()


def _id(value, label):
    if not isinstance(value, str) or not _PATH_ID.fullmatch(value):
        raise ValueError(f"{label} must be a nonempty path-safe ID")
    return value


def _date(value):
    if not isinstance(value, str) or not _DATE.fullmatch(value):
        raise ValueError("date must be YYYY-MM-DD")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("invalid calendar date") from exc


def _zone(value):
    if not isinstance(value, str):
        raise ValueError("timezone must be a UTC offset or IANA zone")
    match = _OFFSET.fullmatch(value)
    if match:
        hours, minutes = int(match[2]), int(match[3])
        if hours > 23 or minutes > 59:
            raise ValueError("invalid UTC offset")
        delta = timedelta(hours=hours, minutes=minutes)
        return fixed_timezone(delta if match[1] == "+" else -delta)
    try:
        return ZoneInfo(value)
    except (ZoneInfoNotFoundError, ValueError, KeyError) as exc:
        raise ValueError("unknown timezone") from exc


def whole_day_range(started_at: str, ended_at: str, *, timezone: str = "+09:00") -> tuple[str, str]:
    """Convert user-inclusive dates into SDK date-only-with-offset boundaries."""
    start, end = _date(started_at), _date(ended_at)
    if end < start:
        raise ValueError("ended_at must not precede started_at")
    zone = _zone(timezone)
    try:
        after_end = end + timedelta(days=1)
    except OverflowError as exc:
        raise ValueError("ended_at is out of range") from exc

    def fmt(day):
        midnight = datetime.combine(day, time.min, tzinfo=zone)
        offset = midnight.strftime("%z")
        return f"{day.isoformat()}{offset[:3]}:{offset[3:]}"

    return fmt(start), fmt(after_end)


def _aware_timestamp(value: str) -> datetime:
    if not isinstance(value, str) or "T" not in value:
        raise ValueError("timestamp must be an ISO 8601 datetime with offset")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("invalid ISO 8601 timestamp") from exc
    if parsed.utcoffset() is None:
        raise ValueError("timestamp must include a timezone offset")
    return parsed


def event_body(subject: str, body_markdown: str, started_at: str, ended_at: str,
               *, whole_day: bool = False, timezone: str = "+09:00", location: str = "",
               who_organization_member_ids=None) -> dict:
    """Create a payload using public SDK EventRequest fields."""
    if not isinstance(subject, str) or not subject.strip():
        raise ValueError("subject is required")
    if not isinstance(body_markdown, str) or not isinstance(location, str):
        raise ValueError("body_markdown and location must be strings")
    if whole_day:
        start, end = whole_day_range(started_at, ended_at, timezone=timezone)
    else:
        first, last = _aware_timestamp(started_at), _aware_timestamp(ended_at)
        if last <= first:
            raise ValueError("ended_at must follow started_at")
        start, end = started_at, ended_at
    member_ids = [] if who_organization_member_ids is None else who_organization_member_ids
    if not isinstance(member_ids, (list, tuple)):
        raise ValueError("member IDs must be a list")
    for member_id in member_ids:
        _id(member_id, "organization member ID")
    return {"users": {"to": [{"type": "member", "member": {"organizationMemberId": member_id}}
                            for member_id in member_ids]},
            "subject": subject, "body": {"mimeType": "text/x-markdown", "content": body_markdown},
            "startedAt": start, "endedAt": end, "wholeDayFlag": whole_day, "location": location}


def list_calendars(*, client=None):
    return _client(client).request("GET", "/calendar/v1/calendars")


def list_events(time_min: str, time_max: str, *, calendars=None, client=None):
    if _aware_timestamp(time_max) <= _aware_timestamp(time_min):
        raise ValueError("time_max must follow time_min")
    params = {"timeMin": time_min, "timeMax": time_max}
    if calendars is not None:
        if not isinstance(calendars, (list, tuple)) or not calendars:
            raise ValueError("calendars must be a nonempty list")
        params["calendars"] = ",".join(_id(item, "calendar ID") for item in calendars)
    return _client(client).request("GET", "/calendar/v1/calendars/*/events", params=params)


def create_event(calendar_id: str, *, subject: str, body_markdown: str, started_at: str,
                 ended_at: str, whole_day: bool = False, timezone: str = "+09:00",
                 location: str = "", who_organization_member_ids=None,
                 apply: bool = False, client=None):
    calendar_id = _id(calendar_id, "calendar ID")
    payload = event_body(subject, body_markdown, started_at, ended_at, whole_day=whole_day,
                         timezone=timezone, location=location,
                         who_organization_member_ids=who_organization_member_ids)
    return _client(client).request("POST", f"/calendar/v1/calendars/{calendar_id}/events",
                                   json_body=payload, apply=apply, resource_id=calendar_id)
