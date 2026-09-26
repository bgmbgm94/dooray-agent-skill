# Dooray 개인 API 검증 현황

이 문서는 **원본 스킬의 과거 라이브 호출 기록** 중 일반 사용자 기능만 선별합니다. 현재 공개본은 독립적으로 작성했으며, **모의 HTTP 단위 테스트만 실행**했습니다. 원본의 성공 ≠ 현재 공개본의 실서비스 성공 ≠ 모든 개인 토큰의 권한 보장. 실제 접근 권한은 프로젝트·드라이브·계정마다 다릅니다.

| 분야 | API 또는 작업 | 원본의 과거 라이브 기록 | 현재 공개본 |
|---|---|---|---|
| 본인 정보 | `GET /common/v1/members/me` | 성공 | CLI 조회·오프라인 테스트 |
| 프로젝트 | `GET /project/v1/projects` | 성공 | CLI 조회·오프라인 테스트 |
| 업무 | 프로젝트별 `GET /posts`, `GET /posts/{id}` | 성공 | CLI 조회·오프라인 테스트 |
| 업무 | 프로젝트별 `POST /posts` | 생성 성공 | CLI 쓰기·오프라인 테스트 |
| 업무 | 수정·완료·이동·댓글 | 일부 성공, `move` 실패 | CLI 미제공 |
| 위키 | `GET /wiki/v1/wikis` | 성공 | CLI 조회·오프라인 테스트 |
| 위키 페이지 | 목록·조회·생성·수정 | 원본의 해당 작업 성공 기록 | Python 모듈 함수 제공, CLI 미제공·오프라인 테스트 |
| 캘린더 | `GET /calendar/v1/calendars`, `GET /calendars/*/events` | 성공 | CLI 조회·오프라인 테스트 |
| 캘린더 | `POST/PUT /calendars/{id}/events` | 생성·수정 성공 | CLI 쓰기·오프라인 테스트 |
| 메신저 | `GET /messenger/v1/channels` | 성공 | CLI 조회·오프라인 테스트 |
| 메신저 | DM·채널 메시지 전송 | 원본에 함수만, 전송 성공 확인되지 않음 | CLI 쓰기·오프라인 테스트; 실제 전송 미검증 |
| Drive | 목록·단건·변경 내역 | 성공 | CLI 조회·오프라인 테스트 |
| Drive | 파일 목록·메타·원본 다운로드 | 성공 | CLI 조회/다운로드·오프라인 테스트 |
| Drive | multipart 업로드·폴더 생성·멤버 공유 링크 조회/발급 | 성공 | CLI 제공·오프라인 테스트, 실제 쓰기 미검증 |
| Drive | 파일 삭제·복사·이동 | 각각 권한 거부·서버 오류·내용 오류 기록 | 미제공 |
| Drive | 파일 메타/내용 변경, 공유 링크 수정/삭제 | 원본에서 라이브 미검증 | 미제공 |
| 연락처 | 개인 주소록 조회 | 원본에 성공 기록 | 미제공 |

## Drive 경로와 CLI 대응

아래 원본 기록은 **과거 환경에서 관측한 결과**이며, 공개본의 새 개인 토큰 라이브 호출을 뜻하지 않습니다.

| 메서드·경로 | 원본 기록 | 현재 공개본 CLI |
|---|---|---|
| `GET /drive/v1/drives` | 성공 | `drive list` |
| `GET /drive/v1/drives/{drive-id}` | 성공 | `drive get <drive-id>` |
| `GET /drive/v2/drives/{drive-id}/changes` | 성공 | `drive changes <drive-id>` |
| `GET /drive/v1/drives/{drive-id}/files?parentId=...` | 성공 | `drive files <drive-id> [--parent-id <folder-id>]` |
| `GET /drive/v1/drives/{drive-id}/files/{file-id}?media=meta` | 성공 | `drive meta <drive-id> <file-id>` |
| `GET /drive/v1/files/{file-id}?media=meta` | 성공 | `drive meta-global <file-id>` |
| `GET /drive/v1/drives/{drive-id}/files/{file-id}?media=raw` | 파일 다운로드 성공 | `drive download <drive-id> <file-id> --out <directory>` |
| `POST /drive/v1/drives/{drive-id}/files` | multipart 업로드 성공(307→파일 전용 호스트) | `drive upload <drive-id> <local-file> [--parent-id <folder-id>] --apply` |
| `POST /drive/v1/drives/{drive-id}/files/{folder-id}/create-folder` | 성공 | `drive create-folder <drive-id> <folder-id> --name <name> --apply` |
| `GET /drive/v1/drives/{drive-id}/files/{file-id}/shared-links` | 성공 | `drive shared-links <drive-id> <file-id>` |
| `POST /drive/v1/drives/{drive-id}/files/{file-id}/shared-links` | `member` 범위·만료 시각으로 성공 | `drive share-create <drive-id> <file-id> --expired-at <ISO8601> --apply` |

쓰기는 **사용자의 명시적 승인**을 받은 뒤에만 실행하세요. 권장 정책은 드라이브 ID가 포함된 허용 목록과 `DOORAY_WRITE_POLICY=allowlist`이며, 명령마다 `--apply`가 별도로 필요합니다. `--apply`가 없으면 미리보기가 아닌 요청 차단입니다. `share-create`는 `member` 범위만 지원하고 타임존이 포함된 만료 시각이 필수입니다.

원본 업로드는 `api.dooray.com`의 307 응답 뒤 `file-api.dooray.com`으로 재전송해 성공한 기록이 있습니다. 공개본은 **정확히 허용된 HTTPS 업로드 주소**로만 인증 헤더를 보내도록 설계해 오프라인 테스트했습니다. 다운로드는 API 메타의 파일명을 검증하고, 지정한 폴더에 같은 이름의 파일이 이미 있으면 **덮어쓰지 않고 중단**합니다. 파일·공유 링크 삭제, 파일 복사·이동, 메타/본문 변경, 공유 링크 수정은 CLI에 없습니다. 원본의 삭제 권한 거부와 복사·이동 오류가 모든 개인 계정에서 동일하다고 단정하지 않습니다.

## 기타 사용 시 주의

- 업무 목록은 페이지네이션이 있으므로 한 페이지만으로 전체라고 판단하지 않습니다. 업무 생성 전에는 조회로 실제 프로젝트 ID를 확인합니다.
- 일정 목록은 `timeMin`, `timeMax`와 대상 캘린더 ID를 확인합니다. 종일 일정은 입력 종료 **포함일**을 API의 다음 날 **미포함일**로 변환합니다. 일정 수정 시 최종 상태 전체와 `--whole-day` 또는 `--timed`를 명시합니다.
- 위키 페이지 기능은 현재 Python 모듈 함수이며 CLI에 없습니다. 메신저 전송은 실제 수신자·본문을 승인받기 전까지 시험 발송하지 않습니다.

원본의 전체 API 카탈로그 숫자와 관리자 API는 옮기지 않았습니다. 현재 CLI 명령과 인자 확인에는 스킬 디렉터리에서 `python scripts/dooray.py --help` 및 `python scripts/dooray.py drive --help`를 사용하세요.
