# 계정·프로젝트·업무

공개 근거: [Dooray Go SDK 계정](https://github.com/dooray-go/dooray-sdk/tree/develop/openapi/account), [프로젝트](https://github.com/dooray-go/dooray-sdk/tree/develop/openapi/project).

- `GET /common/v1/members/me`: 현재 토큰의 계정 정보를 확인합니다. 토큰 값은 노출하지 않습니다.
- `GET /project/v1/projects`: 접근 가능한 프로젝트 목록입니다.
- `GET /project/v1/projects/{projectId}/posts`: 프로젝트 업무 목록입니다. 페이지네이션이 있으므로 한 페이지만으로 전체라고 단정하지 마세요.
- `GET /project/v1/projects/{projectId}/posts/{postId}`: 업무 상세입니다.
- 업무 생성은 실제 쓰기입니다. 사용자 승인, `DOORAY_WRITE_POLICY`, `--apply`(Python API에서는 `apply=True`)가 모두 필요합니다. 실 프로젝트 대신 모의 HTTP로 검증합니다.

사용자 토큰은 프로젝트별로 접근 범위가 다를 수 있습니다. 쓰기 전에 조회로 대상 ID를 확인하세요.
