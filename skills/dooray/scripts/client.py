"""Small, dependency-free Dooray standard-user HTTP client."""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

API_BASE = "https://api.dooray.com"
METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE"}
_ID = re.compile(r"^[A-Za-z0-9_.*:-]+$")


class DoorayError(RuntimeError):
    """An API or local safety-policy failure; never includes credentials."""


def path_id(value: str) -> str:
    """Validate an opaque resource identifier before placing it in a URL."""
    if not value or not _ID.fullmatch(str(value)) or value in {".", ".."}:
        raise DoorayError("Invalid resource ID")
    return urllib.parse.quote(str(value), safe="*")


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise DoorayError("Redirect blocked; Authorization must not be forwarded")


class DoorayClient:
    def __init__(self, token: str | None = None, *, api_base: str = API_BASE,
                 write_policy: str | None = None, allowlist: set[str] | None = None,
                 timeout: int = 30):
        self.token = token or os.environ.get("DOORAY_TOKEN", "").strip()
        if not self.token:
            token_file = Path.home() / ".dooray-token"
            if token_file.exists():
                self.token = token_file.read_text(encoding="utf-8").strip()
        if not self.token:
            raise DoorayError("DOORAY_TOKEN is required")
        parsed = urllib.parse.urlsplit(api_base)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise DoorayError("API base must be an HTTPS origin")
        self.api_base = api_base.rstrip("/")
        self.write_policy = (write_policy or os.environ.get("DOORAY_WRITE_POLICY", "deny")).lower()
        if self.write_policy not in {"deny", "allow", "allowlist"}:
            raise DoorayError("Invalid write policy")
        raw = os.environ.get("DOORAY_WRITE_ALLOWLIST")
        if allowlist is not None:
            self.allowlist = allowlist
        elif raw is not None:
            # Explicitly empty overrides the saved list; never re-enable stale IDs.
            self.allowlist = {x.strip() for x in raw.split(",") if x.strip()}
        else:
            allowlist_file = Path.home() / ".dooray-whitelist"
            self.allowlist = ({line.strip() for line in allowlist_file.read_text(encoding="utf-8").splitlines()
                               if line.strip()} if allowlist_file.exists() else set())
        self.timeout = timeout
        self._opener = urllib.request.build_opener(_NoRedirect())

    def request(self, method: str, path: str, *, params: dict[str, Any] | None = None,
                json_body: Any = None, apply: bool = False,
                resource_id: str | None = None) -> Any:
        method = method.upper()
        if method not in METHODS:
            raise DoorayError("Unsupported HTTP method")
        if not path.startswith("/") or path.startswith("//") or ".." in path or "?" in path or "#" in path or "\\" in path:
            raise DoorayError("Unsafe API path")
        if method != "GET":
            if not apply:
                raise DoorayError("Write not sent: --apply is required")
            if self.write_policy == "deny":
                raise DoorayError("Writes disabled by default; set DOORAY_WRITE_POLICY")
            if self.write_policy == "allowlist" and (not resource_id or resource_id not in self.allowlist):
                raise DoorayError("Destination is not in DOORAY_WRITE_ALLOWLIST")
        if json_body is not None and method == "GET":
            raise DoorayError("GET does not accept JSON body")
        url = self.api_base + path
        if params:
            url += "?" + urllib.parse.urlencode(params, doseq=True)
        headers = {"Authorization": "dooray-api " + self.token, "Accept": "application/json"}
        payload = None
        if json_body is not None:
            payload = json.dumps(json_body, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json; charset=utf-8"
        req = urllib.request.Request(url, data=payload, headers=headers, method=method)
        try:
            with self._opener.open(req, timeout=self.timeout) as response:
                raw = response.read()
        except urllib.error.HTTPError as exc:
            # Error bodies can echo submitted credentials or content: never print them.
            raise DoorayError(f"Dooray returned HTTP {exc.code} for {method} {path}") from None
        except urllib.error.URLError as exc:
            raise DoorayError(f"Dooray request failed for {method} {path}") from None
        if not raw:
            return None
        try:
            document = json.loads(raw)
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise DoorayError("Dooray returned invalid JSON") from None
        if not isinstance(document, dict) or document.get("header", {}).get("isSuccessful") is not True:
            raise DoorayError(f"Dooray reported an unsuccessful response for {method} {path}")
        # Listing endpoints may additionally return totalCount/metadata. The API result
        # is the common payload while callers can request pagination explicitly.
        return document.get("result")
