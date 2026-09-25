#!/usr/bin/env python3
"""Portable Dooray command-line entry point, standard-user API only."""
from __future__ import annotations

import argparse
import json
import sys

from client import DoorayClient, DoorayError, path_id

DOMAINS = ("me", "project", "post", "wiki", "calendar", "messenger")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Dooray personal API skill (read-only by default)")
    sub = parser.add_subparsers(dest="domain", required=True)
    sub.add_parser("me", help="Get current account member")
    project = sub.add_parser("project", help="Project queries")
    p_sub = project.add_subparsers(dest="action", required=True)
    p_sub.add_parser("list")
    post = sub.add_parser("post", help="Project post queries")
    po_sub = post.add_subparsers(dest="action", required=True)
    p = po_sub.add_parser("list")
    p.add_argument("project_id")
    p = po_sub.add_parser("get")
    p.add_argument("project_id")
    p.add_argument("post_id")
    p = po_sub.add_parser("create", help="Create a post; disabled unless policy allows and --apply is set")
    p.add_argument("project_id")
    p.add_argument("--subject", required=True)
    p.add_argument("--body", required=True)
    p.add_argument("--apply", action="store_true")
    wiki = sub.add_parser("wiki", help="Wiki queries")
    w_sub = wiki.add_subparsers(dest="action", required=True)
    w_sub.add_parser("list")
    cal = sub.add_parser("calendar", help="Calendar queries")
    c_sub = cal.add_subparsers(dest="action", required=True)
    c_sub.add_parser("list")
    e = c_sub.add_parser("events")
    e.add_argument("calendar_id")
    e.add_argument("--from", dest="time_min", required=True)
    e.add_argument("--to", dest="time_max", required=True)
    for action in ("event-create", "event-update"):
        e = c_sub.add_parser(action, help="Write event; requires policy and --apply. Update sends the complete event state.")
        e.add_argument("calendar_id")
        if action == "event-update":
            e.add_argument("event_id")
        e.add_argument("--subject", required=True)
        e.add_argument("--body", default="")
        e.add_argument("--started-at", required=True)
        e.add_argument("--ended-at", required=True, help="inclusive date when --whole-day")
        if action == "event-update":
            mode = e.add_mutually_exclusive_group(required=True)
            mode.add_argument("--whole-day", action="store_true")
            mode.add_argument("--timed", action="store_true", help="explicitly mark a timed event")
        else:
            e.add_argument("--whole-day", action="store_true")
        e.add_argument("--timezone", default="+09:00", help="UTC offset or IANA timezone")
        e.add_argument("--to", required=True, dest="to_member_ids", help="comma-separated member IDs")
        e.add_argument("--apply", action="store_true")
    messenger = sub.add_parser("messenger", help="Messenger queries")
    m_sub = messenger.add_subparsers(dest="action", required=True)
    m_sub.add_parser("channels")
    m = m_sub.add_parser("direct-send", help="Send a DM; requires write policy and --apply")
    m.add_argument("--to", required=True, dest="member_id")
    m.add_argument("--text", required=True)
    m.add_argument("--apply", action="store_true")
    m = m_sub.add_parser("post", help="Send a channel message; requires write policy and --apply")
    m.add_argument("channel_id")
    m.add_argument("--text", required=True)
    m.add_argument("--apply", action="store_true")
    return parser


def run(args: argparse.Namespace, client: DoorayClient) -> object:
    if args.domain == "me":
        return client.request("GET", "/common/v1/members/me")
    if args.domain == "project":
        return client.request("GET", "/project/v1/projects")
    if args.domain == "post":
        if args.action == "create":
            from post_api import create_post
            return create_post(client, args.project_id, subject=args.subject,
                               content=args.body, apply=args.apply)
        path = f"/project/v1/projects/{path_id(args.project_id)}/posts"
        if args.action == "get":
            path += "/" + path_id(args.post_id)
        return client.request("GET", path)
    if args.domain == "wiki":
        return client.request("GET", "/wiki/v1/wikis")
    if args.domain == "calendar":
        if args.action == "list":
            return client.request("GET", "/calendar/v1/calendars")
        if args.action in ("event-create", "event-update"):
            from calendar_api import create_event, update_event
            members = [item.strip() for item in args.to_member_ids.split(",") if item.strip()]
            if not members:
                raise DoorayError("At least one attendee is required")
            common = dict(subject=args.subject, body_markdown=args.body,
                          started_at=args.started_at, ended_at=args.ended_at,
                          whole_day=args.whole_day, timezone=args.timezone,
                          who_organization_member_ids=members,
                          apply=args.apply, client=client)
            if args.action == "event-update":
                return update_event(args.calendar_id, args.event_id, **common)
            return create_event(args.calendar_id, **common)
        from calendar_api import list_events
        return list_events(args.time_min, args.time_max, calendars=[path_id(args.calendar_id)], client=client)
    if args.domain == "messenger":
        if args.action == "direct-send":
            from messenger import direct_send
            return direct_send(args.member_id, args.text, apply=args.apply, client=client)
        if args.action == "post":
            from messenger import send_channel_message
            return send_channel_message(args.channel_id, args.text, apply=args.apply, client=client)
        return client.request("GET", "/messenger/v1/channels")
    raise DoorayError("Unsupported command")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = run(args, DoorayClient())
    except (DoorayError, ValueError) as exc:
        print(f"Dooray error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
