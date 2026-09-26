"""Dooray Drive operations for standard-user tokens."""
from __future__ import annotations

from datetime import datetime
import json
import mimetypes
from pathlib import Path
import re
import shutil
import urllib.error
import urllib.parse
import urllib.request
import uuid
from client import DoorayError, path_id


def _files(drive_id):
    return f"/drive/v1/drives/{path_id(drive_id)}/files"


def _file(drive_id, file_id):
    return f"{_files(drive_id)}/{path_id(file_id)}"


def list_drives(client):
    return client.request("GET", "/drive/v1/drives")


def get_drive(client, drive_id):
    return client.request("GET", f"/drive/v1/drives/{path_id(drive_id)}")


def get_changes(client, drive_id):
    return client.request("GET", f"/drive/v2/drives/{path_id(drive_id)}/changes")


def list_files(client, drive_id, *, parent_id=None, folder_id=None, size=100, page=0):
    if parent_id is not None and folder_id is not None:
        raise DoorayError("Specify only one parent folder")
    parent = parent_id if parent_id is not None else folder_id
    params = {"size": size, "page": page}
    if parent is not None:
        params["parentId"] = path_id(parent)
    return client.request("GET", _files(drive_id), params=params)


def get_file_meta(client, drive_id, file_id):
    return client.request("GET", _file(drive_id, file_id), params={"media": "meta"})


def get_file(client, drive_id, file_id):
    return get_file_meta(client, drive_id, file_id)


def get_file_meta_global(client, file_id):
    return client.request("GET", f"/drive/v1/files/{path_id(file_id)}", params={"media": "meta"})


def download_file(client, drive_id, file_id, out_dir):
    """Stream a raw file into a newly created local file; never follow redirects."""
    meta = get_file_meta(client, drive_id, file_id)
    name = meta.get("name") if isinstance(meta, dict) else None
    if (not isinstance(name, str) or name in {"", ".", ".."}
            or any(c in name for c in '/\\:\x00\r\n<>|?*') or name != name.strip()
            or name.endswith(".")
            or re.match(r"^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)", name, re.I)
            or any(ord(c) < 32 for c in name)):
        raise DoorayError("Unsafe download filename")
    directory = Path(out_dir)
    directory.mkdir(parents=True, exist_ok=True)
    dest = directory / name
    if dest.exists() or dest.is_symlink():
        raise DoorayError("Download destination already exists")
    url = client.api_base + _file(drive_id, file_id) + "?media=raw"
    req = urllib.request.Request(url, headers={"Authorization": "dooray-api " + client.token}, method="GET")
    created = False
    try:
        with client._opener.open(req, timeout=client.timeout) as response:
            with dest.open("xb") as output:
                created = True
                shutil.copyfileobj(response, output, length=1024 * 1024)
    except (OSError, urllib.error.URLError) as exc:
        if created:
            dest.unlink(missing_ok=True)
        raise DoorayError("Drive download failed or destination already exists") from None
    except Exception:
        if created:
            dest.unlink(missing_ok=True)
        raise
    return dest


class _BlockRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _upload_opener():
    return urllib.request.build_opener(_BlockRedirect())


def _multipart_chunks(source, head, tail):
    yield head
    with source.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            yield chunk
    yield tail


def _upload_result(response):
    try:
        document = json.loads(response.read())
    except (ValueError, UnicodeDecodeError):
        raise DoorayError("Drive upload returned invalid JSON") from None
    if (not isinstance(document, dict) or not isinstance(document.get("header"), dict)
            or document["header"].get("isSuccessful") is not True):
        raise DoorayError("Drive upload failed")
    return document.get("result")


def upload_file(client, drive_id, file_path, *, parent_id=None, apply=False):
    """Upload via the sole trusted Dooray file API redirect, streaming local content."""
    path = _files(drive_id)
    if parent_id is not None:
        parent_id = path_id(parent_id)
    if not apply:
        raise DoorayError("Write not sent: --apply is required")
    if client.write_policy == "deny":
        raise DoorayError("Writes disabled by default; set DOORAY_WRITE_POLICY")
    if client.write_policy == "allowlist" and drive_id not in client.allowlist:
        raise DoorayError("Destination is not in DOORAY_WRITE_ALLOWLIST")
    source = Path(file_path)
    name = source.name
    if not name or any(c in name for c in '\"\\\r\n\x00') or any(ord(c) < 32 for c in name):
        raise DoorayError("Unsafe upload filename")
    try:
        length = source.stat().st_size
        if not source.is_file():
            raise OSError("not a regular file")
    except OSError:
        raise DoorayError("Upload source must be a readable file") from None
    query = "?" + urllib.parse.urlencode({"parentId": parent_id}) if parent_id else ""
    boundary = "----dooray-" + uuid.uuid4().hex
    head = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{name}\"\r\n"
            f"Content-Type: {mimetypes.guess_type(name)[0] or 'application/octet-stream'}\r\n\r\n").encode("utf-8")
    tail = f"\r\n--{boundary}--\r\n".encode("ascii")
    opener = _upload_opener()

    def post(url):
        request = urllib.request.Request(url, data=_multipart_chunks(source, head, tail), method="POST",
                                         headers={"Authorization": "dooray-api " + client.token,
                                                  "Content-Type": f"multipart/form-data; boundary={boundary}",
                                                  "Content-Length": str(length + len(head) + len(tail)),
                                                  "Accept": "application/json"})
        return opener.open(request, timeout=client.timeout)

    try:
        try:
            with post(client.api_base + path + query) as response:
                return _upload_result(response)
        except urllib.error.HTTPError as exc:
            try:
                if exc.code not in (307, 308):
                    raise DoorayError(f"Drive upload returned HTTP {exc.code}") from None
                location = exc.headers.get("Location")
            finally:
                exc.close()
            # Compare the entire URL, not just hostname: no ports, credentials,
            # alternate path/query, fragments, or encoded-path ambiguities.
            expected = "https://file-api.dooray.com/uploads" + path + query
            if location != expected:
                raise DoorayError("Untrusted Drive upload redirect")
        try:
            with post(expected) as response:
                return _upload_result(response)
        except urllib.error.HTTPError as exc:
            code = exc.code
            exc.close()
            raise DoorayError(f"Drive upload returned HTTP {code}") from None
    except urllib.error.URLError:
        raise DoorayError("Drive upload network failure") from None
    except OSError:
        raise DoorayError("Drive upload source read failure") from None


def create_folder(client, drive_id, folder_id, *, name, apply=False):
    if not isinstance(name, str) or not name.strip():
        raise DoorayError("Folder name is required")
    return client.request("POST", _file(drive_id, folder_id) + "/create-folder",
                          json_body={"name": name}, apply=apply, resource_id=drive_id)


def list_shared_links(client, drive_id, file_id):
    return client.request("GET", _file(drive_id, file_id) + "/shared-links")


def create_shared_link(client, drive_id, file_id, *, expired_at, scope="member", apply=False):
    if scope != "member":
        raise DoorayError("Only member-scope links are supported")
    try:
        parsed = datetime.fromisoformat(expired_at.replace("Z", "+00:00"))
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError("timezone required")
    except (ValueError, TypeError):
        raise DoorayError("Valid timezone-aware expired_at is required") from None
    return client.request("POST", _file(drive_id, file_id) + "/shared-links",
                          json_body={"scope": "member", "expiredAt": expired_at},
                          apply=apply, resource_id=drive_id)
