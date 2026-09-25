"""Project posts: documented standard-user list/detail/create endpoints.

Evidence: https://github.com/dooray-go/dooray-sdk/tree/develop/openapi/project
"""
from __future__ import annotations

from client import path_id

# Public SDK GetPostsOptions, limited to documented member-level filters.
_FILTERS = frozenset({
    "fromEmailAddress", "fromMemberIds", "toMemberIds", "toMemberSize",
    "ccMemberIds", "tagIds", "parentPostId", "postNumber",
    "postWorkflowClasses", "postWorkflowIds", "milestoneIds", "subjects",
    "createdAt", "updatedAt", "dueAt", "order",
})


def list_posts(client, project_id: str, *, page: int = 0, size: int = 20,
               **filters):
    """List posts in a project using SDK-supported filters."""
    if not isinstance(page, int) or isinstance(page, bool) or page < 0:
        raise ValueError("page must be a nonnegative integer")
    if not isinstance(size, int) or isinstance(size, bool) or not 1 <= size <= 100:
        raise ValueError("size must be between 1 and 100")
    unknown = set(filters) - _FILTERS
    if unknown:
        raise ValueError("Unsupported post filters: " + ", ".join(sorted(unknown)))
    params = {"page": page, "size": size}
    params.update({k: v for k, v in filters.items() if v is not None})
    return client.request("GET", f"/project/v1/projects/{path_id(project_id)}/posts", params=params)


def get_post(client, project_id: str, post_id: str):
    """Fetch one post."""
    return client.request("GET", f"/project/v1/projects/{path_id(project_id)}/posts/{path_id(post_id)}")


def create_post(client, project_id: str, *, subject: str, content: str,
                mime_type: str = "text/x-markdown", apply: bool = False,
                **fields):
    """Create a post; both explicit apply and client's write policy must permit it."""
    if not apply:
        raise ValueError("Write not sent: apply=True is required")
    if not isinstance(subject, str) or not subject.strip() or not isinstance(content, str):
        raise ValueError("subject and content are required")
    allowed = {"users", "dueDate", "priority", "milestoneId", "tagIds", "parentPostId", "workflowId"}
    if set(fields) - allowed:
        raise ValueError("Unsupported create fields: " + ", ".join(sorted(set(fields) - allowed)))
    body = {"subject": subject, "body": {"mimeType": mime_type, "content": content}}
    body.update({k: v for k, v in fields.items() if v is not None})
    project = path_id(project_id)
    return client.request("POST", f"/project/v1/projects/{project}/posts",
                          json_body=body, apply=True, resource_id=project_id)
