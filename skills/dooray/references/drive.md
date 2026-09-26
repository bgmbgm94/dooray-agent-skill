# Drive — 개인 토큰으로 접근 가능한 범위

이 경로는 원본 스킬의 과거 라이브 호출 기록을 바탕으로 다시 구현했습니다. **현재 공개본은 모의 HTTP로 요청 형태·안전장치만 테스트**했으며, 실제 개인 토큰 호출 성공은 새로 확인하지 않았습니다. 프로젝트/드라이브 권한에 따라 결과는 다릅니다.

| 메서드·경로 | 원본 기록 | 공개본 CLI |
|---|---|---|
| `GET /drive/v1/drives` | 성공 | `drive list` |
| `GET /drive/v1/drives/{drive-id}` | 성공 | `drive get <drive-id>` |
| `GET /drive/v2/drives/{drive-id}/changes` | 성공 | `drive changes <drive-id>` |
| `GET /drive/v1/drives/{drive-id}/files?parentId=...` | 성공 | `drive files <drive-id> [--parent-id <folder-id>]` |
| `GET /drive/v1/drives/{drive-id}/files/{file-id}?media=meta` | 성공 | `drive meta <drive-id> <file-id>` |
| `GET /drive/v1/files/{file-id}?media=meta` | 성공 | `drive meta-global <file-id>` |
| `GET /drive/v1/drives/{drive-id}/files/{file-id}?media=raw` | 원본 파일 다운로드 성공 | `drive download <drive-id> <file-id> --out <directory>` |
| `POST /drive/v1/drives/{drive-id}/files` | multipart 업로드 성공(307→파일 전용 호스트) | `drive upload <drive-id> <local-file> [--parent-id <folder-id>] --apply` |
| `POST /drive/v1/drives/{drive-id}/files/{folder-id}/create-folder` | 성공 | `drive create-folder <drive-id> <folder-id> --name <name> --apply` |
| `GET /drive/v1/drives/{drive-id}/files/{file-id}/shared-links` | 성공 | `drive shared-links <drive-id> <file-id>` |
| `POST /drive/v1/drives/{drive-id}/files/{file-id}/shared-links` | `member` 범위·만료 시각으로 성공 | `drive share-create <drive-id> <file-id> --expired-at <ISO8601> --apply` |

쓰기를 하려면 **먼저 사용자 승인**, 드라이브 ID가 포함된 허용 목록, `DOORAY_WRITE_POLICY=allowlist`, 명시적인 `--apply`가 필요합니다. `share-create`는 `member` 범위만 지원하며 타임존이 포함된 만료 시각이 필수입니다. `--apply` 없이 호출하면 미리보기가 아니라 요청 자체가 거부됩니다.

다운로드는 API 메타의 파일명을 검증하고, 지정한 로컬 폴더에 동일한 이름의 파일이 이미 있으면 **덮어쓰지 않고 중단**합니다. 업로드는 원본 기록에서 관측된 정확한 `https://file-api.dooray.com/uploads/...` 목적지만 허용합니다. 파일·공유 링크의 삭제, 복사, 이동, 메타/본문 변경은 현재 CLI에 없습니다. 원본에서 개인 토큰 삭제는 권한 거부, 복사·이동은 서버 오류로 기록됐으나, 모든 계정의 제한이라고 단정하지 않습니다.

자세한 전체 검증 구분은 [검증 현황](verification.md)을 참고하세요.
