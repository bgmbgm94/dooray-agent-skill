"""Drive API placeholder: explicitly unavailable pending public endpoint evidence.

The public SDK's complete ``openapi`` tree has no Drive module:
https://github.com/dooray-go/dooray-sdk/tree/develop/openapi

Do not guess routes from the web UI or from another product's Drive API. In
particular, do not expose upload/download until cross-origin redirect behavior
has been credential-leak tested. Wiki attachments are a separate API.
"""
from __future__ import annotations


class UnsupportedDriveAPI(NotImplementedError):
    """No verified public Dooray Drive API contract is available here."""


def list_drives(client):
    raise UnsupportedDriveAPI("Drive list endpoint is not verified by permitted public sources")


def list_files(client, drive_id: str, *, folder_id: str | None = None):
    raise UnsupportedDriveAPI("Drive file list endpoint is not verified by permitted public sources")


def get_file(client, drive_id: str, file_id: str):
    raise UnsupportedDriveAPI("Drive file detail endpoint is not verified by permitted public sources")
