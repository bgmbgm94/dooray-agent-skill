"""Dooray messenger read and explicit-write operations.

The injected/default DoorayClient owns all transport and write-policy enforcement.
"""
from __future__ import annotations

import re

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


def _text(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("text must be nonempty")
    return value


def list_channels(*, client=None):
    """Return the current user's channels; no write capability required."""
    return _client(client).request("GET", "/messenger/v1/channels")


def direct_send(organization_member_id: str, text: str, *, apply: bool = False, client=None):
    """Send to a single organization member, with client-enforced write approval."""
    recipient = _id(organization_member_id, "organization member ID")
    message = _text(text)
    return _client(client).request("POST", "/messenger/v1/channels/direct-send",
                                   json_body={"text": message, "organizationMemberId": recipient},
                                   apply=apply, resource_id=recipient)


def send_channel_message(channel_id: str, text: str, *, apply: bool = False, client=None):
    """Post a channel log only when DoorayClient permits the explicit write."""
    channel = _id(channel_id, "channel ID")
    message = _text(text)
    return _client(client).request("POST", f"/messenger/v1/channels/{channel}/logs",
                                   json_body={"text": message}, apply=apply, resource_id=channel)
