# Dooray Agent Skill

Dooray 개인 API 토큰으로 **Claude Code·Codex 등에서** 프로젝트 업무·위키·캘린더·메신저를 다루는 공용 Agent Skill입니다. 원본 Dooray 스킬 README의 설치→설정→실행→안전 수칙 구성을 일반 사용자용 독립 저장소에 맞게 정리했습니다.

- 개인 API 토큰으로 접근 가능한 항목을 조회합니다. **모든 도메인에 접근할 수 있다는 뜻은 아닙니다.** 실제 권한은 계정·프로젝트 설정에 따릅니다.
- 쓰기는 기본 차단됩니다. 사용자 승인 후 정책 허용과 `--apply`를 모두 지정해야 요청합니다.
- Python 3.10+ 표준 라이브러리만 사용합니다. 별도 패키지 설치는 필요하지 않습니다.
- **Drive·연락처·관리자 기능은 현재 지원하지 않습니다.** 확인되지 않은 API 경로를 임의로 호출하지 않습니다.

> 에이전트 동작 규칙은 [`skills/dooray/SKILL.md`](skills/dooray/SKILL.md), API 근거와 주의사항은 [`references/`](skills/dooray/references/README.md)를 참고하세요. 원본 README의 설명 가운데 새 구현과 일치하지 않는 기능·설치 명령은 가져오지 않았습니다.

## 선결 조건

- Claude Code 또는 Codex 등 Agent Skills를 읽을 수 있는 도구. CLI만 사용한다면 에이전트 설치는 필요하지 않습니다.
- Python 3.10 이상
- **Dooray 개인 API 토큰**: Dooray 웹의 서비스 설정 → API에서 발급합니다. 토큰의 접근 권한은 사용자마다 다릅니다.

## 설치

저장소를 클론한 뒤 스킬 폴더인 `skills/dooray`를 사용하는 도구의 스킬 경로에 복사하거나 링크합니다. **저장소를 클론하기만 해도 모든 프로젝트에서 자동 발견되는 것은 아닙니다.**

| 도구 | 스킬 경로 예시 |
|---|---|
| Claude Code | `~/.claude/skills/dooray` 또는 프로젝트 `.claude/skills/dooray` |
| Codex | `~/.agents/skills/dooray` 또는 프로젝트 `.agents/skills/dooray` |

Claude Code에서 로컬 플러그인으로 설치할 수도 있습니다. `.claude-plugin/plugin.json`과 `skills/dooray/SKILL.md`가 함께 들어 있습니다. 각 도구의 설치 경로와 지원 버전은 해당 도구 문서를 확인하세요.

## 초기 설정

토큰은 **채팅창에 붙여넣거나 저장소에 커밋하지 마세요.** CLI는 환경변수 `DOORAY_TOKEN`을 먼저 읽고, 없다면 홈 디렉터리의 `~/.dooray-token` 파일을 읽습니다. 터미널에 토큰 값을 그대로 적으면 셸 기록에 남을 수 있으므로 입력 방식과 파일 접근 권한에 주의하세요.

```bash
# Bash 예시: 입력값을 화면에 표시하지 않고 이번 터미널 세션에만 보관
read -rs -p 'Dooray token: ' DOORAY_TOKEN; printf '\n'
export DOORAY_TOKEN
python skills/dooray/scripts/dooray.py me
```

쓰기 정책은 기본 `deny`입니다. **실제 변경을 승인받은 경우에만** 다음 중 하나를 선택합니다.

- `DOORAY_WRITE_POLICY=allowlist`: `DOORAY_WRITE_ALLOWLIST`에 콤마로 구분한 대상 ID를 지정합니다. 목록이 비어 있으면 쓰기를 거부합니다.
- `DOORAY_WRITE_POLICY=allow`: 대상 ID 제한 없이 쓰기를 허용합니다. 신중하게 사용하세요.
- 어느 경우든 쓰기 명령에는 `--apply`가 별도로 필요합니다. 이 옵션이 없다고 미리보기 결과가 출력되는 것은 아닙니다. **요청 자체를 차단**합니다.

설정 파일 자동 생성 스크립트는 제공하지 않습니다. 파일을 사용할 경우 `~/.dooray-token`을 저장소 밖에 두고 OS에 맞는 접근 권한을 직접 제한하세요.

## 실행 방법

저장소 루트에서 직접 실행하는 예시입니다. 에이전트가 스킬을 사용할 때는 `skills/dooray`를 기준으로 `scripts/dooray.py`를 찾습니다.

```bash
python skills/dooray/scripts/dooray.py --help
python skills/dooray/scripts/dooray.py me
python skills/dooray/scripts/dooray.py project list
python skills/dooray/scripts/dooray.py calendar list
python skills/dooray/scripts/dooray.py messenger channels
```

지원 범위: 계정 조회, 프로젝트 목록, 업무 목록·상세·생성, 위키 목록(모듈에는 페이지 조회·생성·수정 함수 제공), 캘린더 목록·일정 조회·생성·수정, 메신저 채널 조회·DM·채널 메시지 전송. **CLI에 없는 모듈 기능까지 CLI 명령으로 지원한다고 해석하지 마세요.** 명령별 인자와 필수 옵션은 `--help`로 확인할 수 있습니다.

종일 일정 입력의 종료일은 **포함일**입니다. API 요청 시에는 다음 날의 **미포함 종료일**로 변환합니다. 일정 수정에는 `--whole-day` 또는 `--timed`를 명시적으로 선택해야 하며, 본문·참석자 등 원하는 최종 상태를 모두 제공해야 합니다. 실제 일정 또는 메시지를 시험용으로 생성하지 마세요.

## 안전 수칙

1. 조회로 대상 ID와 권한을 확인하고, 쓰기 전에 **대상·전송 내용·영향**을 사용자에게 보여 승인받습니다.
2. 허용 목록을 쓰는 경우 변경할 대상의 ID를 확인합니다. 환경변수만 설정해도 자동으로 쓰기가 이뤄지지는 않습니다.
3. `--apply`와 쓰기 정책은 **로컬 안전장치**입니다. Dooray의 실제 접근 권한을 우회하지 않습니다.
4. 외부로 인증 헤더가 넘어갈 수 있는 HTTP 리디렉션은 공통 클라이언트에서 차단합니다.
5. 실제 서비스 응답·개인 토큰·대상 ID를 공개 이슈나 예제에 넣지 마세요.

## 검증 상태 및 개발

```bash
python -m unittest discover -s tests -v
```

테스트는 네트워크를 모의 처리하여 요청 형태와 쓰기 차단 동작을 검사합니다. **각 기능의 실제 Dooray API 성공까지 입증한 것은 아닙니다.** Drive는 공개 근거가 확인될 때까지 비활성화했습니다. 참조한 공개 자료와 라이선스 정보는 [`THIRD-PARTY-NOTICES.md`](THIRD-PARTY-NOTICES.md)에 있습니다.
