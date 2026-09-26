"""Standard-user wiki page operations (no file upload or redirect handling)."""
from __future__ import annotations

from client import path_id


def _body(content: str, mime_type: str) -> dict:
    if not isinstance(content, str) or not isinstance(mime_type, str) or not mime_type:
        raise ValueError("content and mime_type are required")
    return {"mimeType": mime_type, "content": content}


def _write_allowed(apply: bool) -> None:
    if not apply:
        raise ValueError("Write not sent: apply=True is required")


def list_wikis(client, *, page: int | None = None, size: int | None = None):
    params = {}
    for key, val in (("page", page), ("size", size)):
        if val is not None:
            if not isinstance(val, int) or isinstance(val, bool) or val < (1 if key == "size" else 0):
                raise ValueError(f"Invalid {key}")
            params[key] = val
    return client.request("GET", "/wiki/v1/wikis", params=params or None)


def list_pages(client, wiki_id: str, *, parent_page_id: str | None = None):
    params = {"parentPageId": path_id(parent_page_id)} if parent_page_id is not None else None
    return client.request("GET", f"/wiki/v1/wikis/{path_id(wiki_id)}/pages", params=params)


def get_page(client, wiki_id: str, page_id: str):
    return client.request("GET", f"/wiki/v1/wikis/{path_id(wiki_id)}/pages/{path_id(page_id)}")


def create_page(client, wiki_id: str, *, subject: str, content: str,
                mime_type: str = "text/x-markdown", parent_page_id: str | None = None,
                apply: bool = False):
    _write_allowed(apply)
    if not isinstance(subject, str) or not subject.strip():
        raise ValueError("subject is required")
    payload = {"subject": subject, "body": _body(content, mime_type)}
    if parent_page_id is not None:
        payload["parentPageId"] = path_id(parent_page_id)
    return client.request("POST", f"/wiki/v1/wikis/{path_id(wiki_id)}/pages",
                          json_body=payload, apply=True, resource_id=wiki_id)


def update_page(client, wiki_id: str, page_id: str, *, subject: str, content: str,
                mime_type: str = "text/x-markdown", apply: bool = False):
    """PUT complete title+body, not an undocumented partial-update PATCH."""
    _write_allowed(apply)
    if not isinstance(subject, str) or not subject.strip():
        raise ValueError("subject is required")
    return client.request("PUT", f"/wiki/v1/wikis/{path_id(wiki_id)}/pages/{path_id(page_id)}",
                          json_body={"subject": subject, "body": _body(content, mime_type)},
                          apply=True, resource_id=wiki_id)
