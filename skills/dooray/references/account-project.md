# Account, projects, posts

Public evidence: [Dooray Go SDK account](https://github.com/dooray-go/dooray-sdk/tree/develop/openapi/account), [project](https://github.com/dooray-go/dooray-sdk/tree/develop/openapi/project).

- `GET /common/v1/members/me`: current member; use to confirm which personal token is active without exposing it.
- `GET /project/v1/projects`: project listing.
- `GET /project/v1/projects/{projectId}/posts`: post listing. Lists can be paginated; do not assume a single page is complete.
- `GET /project/v1/projects/{projectId}/posts/{postId}`: post detail.
- Creating a post is a write that requires user authorization, `DOORAY_WRITE_POLICY`, and `--apply` or the Python client's `apply=True`. Test using mocked HTTP, not a real project.

The user/token may have access to some but not all projects. Validate destination IDs from read-only queries before writes.
