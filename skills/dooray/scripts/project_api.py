"""Standard-user project listing."""
from __future__ import annotations


def list_projects(client, *, project_type: str | None = None,
                  scope: str | None = None, state: str | None = None,
                  size: int = 100):
    """List projects accessible to the current member."""
    if not isinstance(size, int) or isinstance(size, bool) or not 1 <= size <= 100:
        raise ValueError("size must be between 1 and 100")
    params = {"member": "me", "size": size}
    for name, value in (("type", project_type), ("scope", scope), ("state", state)):
        if value is not None:
            params[name] = value
    return client.request("GET", "/project/v1/projects", params=params)
