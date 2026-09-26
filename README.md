# Dooray Agent Skill

Dooray 개인 API 토큰으로 업무·위키·캘린더·메신저·Drive를 다루는 Claude Code·Codex 공용 Agent Skill입니다. 원본 스킬의 설치→초기 설정→실행→안전 수칙 구성을 **현재 공개본의 실제 기능**에 맞춰 정리했습니다. Python 3.10+ 표준 라이브러리만 필요합니다.

- `두레이`, `Dooray`, `dooray drive`, `두레이 업무` 같은 자연어 요청에서 에이전트가 스킬을 발견하도록 [`SKILL.md`](skills/dooray/SKILL.md)에 용도를 기술했습니다. **키워드 완전 일치 트리거는 아니며**, 설치·활성화 후에도 에이전트 판단에 따라 로드됩니다.
- 쓰기는 기본 차단입니다. 대상·내용을 확인해 사용자가 승인한 뒤, 쓰기 정책과 `--apply`를 **모두** 지정해야 합니다.
- 현재 CLI는 프로젝트/업무, 위키 목록, 캘린더, 메신저, Drive를 지원합니다. 연락처·관리자 API는 지원하지 않습니다. 실제 접근 권한은 계정·프로젝트마다 다릅니다.

## 설치

### Claude Code — 마켓플레이스

Claude Code 안에서 다음 명령을 실행합니다. **이 공개 저장소 전용 카탈로그**이며, 이전 플러그인의 설치 명령과 별개입니다.

```text
/plugin marketplace add bgmbgm94/dooray-agent-skill
/plugin install dooray@dooray-agent-skill
```

저장소의 `.claude-plugin/marketplace.json`과 플러그인 정의는 `claude plugin validate . --strict`로 검증했습니다. 별도 임시 Claude 설정에서 **공개 GitHub 주소로 마켓플레이스 추가 → `dooray@dooray-agent-skill` 설치·활성화 → 스킬·설정 문서 포함**까지 확인했습니다. 자연어 요청에서의 자동 선택과 실제 Dooray API 호출은 별도로 검증하지 않았습니다. 설치 시 스킬은 플러그인 캐시에 복사될 수 있어 경로가 **고정되지 않습니다**. `scripts/setup.sh`를 실행하려면 설치된 `skills/dooray` 디렉터리를 찾아 그 안에서 실행하세요. 관리자/엔터프라이즈 정책이 개인 마켓플레이스를 제한하면 설치가 거절될 수 있습니다.

### Codex·기타 Agent Skills 도구

저장소를 클론한 뒤 `skills/dooray` 디렉터리를 도구의 스킬 위치에 복사하거나 링크합니다. 예: Codex 사용자 스킬 경로 `~/.agents/skills/dooray`, Claude Code 스킬 경로 `~/.claude/skills/dooray`. **클론만으로 전역 자동 발견되지는 않습니다.** CLI만 쓰는 경우 스킬 설치 없이 저장소 루트에서 `python skills/dooray/scripts/dooray.py --help`를 실행할 수 있습니다.

## 초기 설정

Dooray 웹 서비스 설정 → API에서 **개인 API 토큰**을 발급받으세요. 토큰은 AI 채팅창·명령행 인자·저장소에 넣지 마세요. CLI는 `DOORAY_TOKEN` 환경변수를 우선 읽고, 없으면 사용자 홈의 `~/.dooray-token`을 읽습니다. 토큰 값은 Dooray에서 발급된 `id:secret` 한 줄 형식입니다.

### (a) 번들 스크립트 — 권장

설치된 스킬 디렉터리(`skills/dooray/`)에서 **Bash**로 실행합니다. 클론한 저장소라면 `cd skills/dooray` 후 다음 명령을 실행하세요.

```bash
bash scripts/setup.sh              # 개인 토큰 + 쓰기 허용 대상 ID
bash scripts/setup.sh --whitelist  # 허용 대상 ID만 다시 설정 (토큰은 유지)
```

스크립트는 토큰 입력을 화면에 표시하지 않으며, `~/.dooray-token`과 `~/.dooray-whitelist`를 **저장소 밖의 사용자 홈**에 만듭니다. 허용 목록에는 프로젝트 ID 또는 Drive ID를 **한 줄에 하나씩** 입력하고 빈 줄로 종료합니다. 비어 있으면 `allowlist` 정책에서는 모든 쓰기가 거부됩니다. Linux/macOS에서는 파일 모드를 `600`으로 설정합니다. Windows Git Bash에서는 Python CLI와 동일한 `%USERPROFILE%`을 사용하며, **실제 접근 제어는 Windows 파일 ACL에도 좌우**됩니다. 관리자 토큰 설정은 지원하지 않습니다.

### (b) 수동 설정 — 스크립트 없이

Bash에서 비밀값을 명령에 직접 쓰지 않고 입력하는 예입니다. 먼저 토큰을 숨겨서 받고 파일에 저장한 뒤, 필요한 허용 ID만 기록합니다. CLI가 찾는 사용자 홈과 셸의 `$HOME`이 다른 Windows 환경에서는 `%USERPROFILE%` 아래에 파일을 만들어 주세요.

```bash
umask 077
read -rs -p 'Dooray token: ' token; printf '\n'
printf '%s\n' "$token" > "$HOME/.dooray-token"
unset token
printf '%s\n' '<project-id>' '<drive-id>' > "$HOME/.dooray-whitelist"
chmod 600 "$HOME/.dooray-token" "$HOME/.dooray-whitelist"
```

`<project-id>`·`<drive-id>`는 예시이므로 실제 허용할 **리소스 ID**로 바꾸세요. 쓰기를 사용하지 않으면 허용 목록을 비워 두거나 생략하세요. 토큰·허용 목록 모두 저장소에 커밋하면 안 됩니다. Windows에서는 Git Bash의 `$HOME`이 Python 홈과 다른 경우가 있으므로 **(a) 스크립트 사용을 권장**합니다.

### 쓰기 활성화 — 필요한 세션에서만

파일에 허용 ID를 넣는 것만으로 쓰기가 켜지지 않습니다. 승인받은 작업을 실행할 때만 정책을 선택합니다. 환경변수 `DOORAY_WRITE_ALLOWLIST`가 **설정돼 있으면** 콤마로 분리한 ID가 파일보다 우선하며, 빈 값으로 설정하면 허용 목록도 빈 값이 됩니다. 변수가 아예 없을 때만 파일을 읽습니다. 기본 정책은 `deny`이며, 권장 정책은 대상 ID를 제한하는 `allowlist`입니다.

```bash
export DOORAY_WRITE_POLICY=allowlist
python scripts/dooray.py drive files '<drive-id>'
# 대상·파일·영향을 확인하고 사용자 승인 후에만:
python scripts/dooray.py drive upload '<drive-id>' ./example.txt --apply
```

위 예시의 작업 디렉터리는 `skills/dooray`입니다. `--apply`를 생략하면 미리보기가 아니라 요청 자체가 차단됩니다. `DOORAY_WRITE_POLICY=allow`는 모든 대상 ID에 쓰기를 허용하므로 사용하지 않는 것을 권장합니다. 이 안전장치는 Dooray 서비스 권한을 우회하지 않습니다.

## 실행 예시

스킬 디렉터리에서:

```bash
python scripts/dooray.py --help
python scripts/dooray.py me
python scripts/dooray.py project list
python scripts/dooray.py calendar list
python scripts/dooray.py messenger channels
python scripts/dooray.py drive list
python scripts/dooray.py drive files '<drive-id>' --parent-id '<folder-id>'
python scripts/dooray.py drive download '<drive-id>' '<file-id>' --out ./downloads
```

Drive는 목록·메타·변경내역·다운로드, 승인된 파일 업로드·폴더 생성·**멤버 범위** 공유 링크 발급/조회를 지원합니다. 다운로드 시 서버 제공 파일명을 검사하고 기존 파일을 덮어쓰지 않습니다. 업로드는 확인된 형태의 `file-api.dooray.com` 리디렉션만 허용합니다. **삭제·복사·이동은 제공하지 않습니다.** 상세 명령은 `python scripts/dooray.py drive --help`와 [Drive 참고 문서](skills/dooray/references/drive.md)를 보세요.

업무는 조회·생성, 위키는 CLI 목록(페이지 기능은 Python 모듈), 일정은 조회·생성·전체 상태 수정, 메신저는 채널 목록·DM/채널 전송을 제공합니다. 종일 일정의 입력 종료일은 포함일이며 API 요청에서는 다음 날의 미포함 종료일로 변환합니다. 실제 메시지 전송 성공은 이 공개본에서 확인하지 않았습니다.

## 검증 상태와 안전 수칙

[API 검증 현황 표](skills/dooray/references/verification.md)는 **원본 스킬에 남은 과거 라이브 검증**과 **이 공개본의 모의 HTTP 단위 테스트**를 분리해 기록합니다. 원본에서 Drive 업로드를 사용했던 기록은 있지만, 이 독립 구현을 실제 Dooray 계정에서 새로 검증한 것은 아닙니다. 임의의 실서비스 업로드·메시지 전송을 테스트 목적으로 하지 마세요.

```bash
python -m unittest discover -s tests -v
```

쓰기 전 조회로 대상과 권한을 확인하고 사용자에게 전송 본문·영향을 설명해 승인받으세요. 자격증명, 실제 조직/프로젝트 ID, 응답 원문을 공개 이슈·예제·테스트에 넣지 마세요. 참고한 공개 프로젝트는 [출처 고지](THIRD-PARTY-NOTICES.md)에 정리했습니다.
