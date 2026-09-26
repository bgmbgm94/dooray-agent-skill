---
name: dooray
description: 사용자가 "두레이", "Dooray", "dooray api", "두레이 업무/위키/캘린더/메신저/드라이브", "dooray drive"라고 말하거나 Dooray 개인 API로 업무·파일·일정 조회/수정을 요청할 때 사용합니다. 개인 토큰을 쓰며 변경 작업은 사용자 승인·쓰기 정책·--apply가 모두 필요합니다.
---
# Dooray Agent Skill

Dooray 개인 토큰으로 업무·위키·캘린더·메신저·Drive를 다룹니다. **키워드는 에이전트의 자연어 스킬 발견을 돕는 힌트이지, 완전 일치 명령어가 아닙니다.** 설치와 활성화 여부를 먼저 확인하세요. 연락처·관리자 기능은 이 공개본에 없습니다.

## 시작

1. `python scripts/dooray.py --help`로 실제 CLI 지원 범위를 확인합니다. Python 3.10+ 표준 라이브러리만 필요합니다.
2. 토큰이 없으면 채팅으로 값을 요구하지 말고, **실제로 설치된 스킬 디렉터리**에서 `bash scripts/setup.sh`를 실행하도록 안내합니다. 플러그인 캐시의 경로는 고정값으로 추측하지 마세요. 스크립트 없이 설정할 때는 아래의 숨김 입력 방법을 안내합니다.
3. API별 과거 기록과 현재 구현을 비교해야 할 때만 [`references/verification.md`](references/verification.md)를 읽습니다. 원본의 라이브 검증과 공개본의 오프라인 테스트를 혼동하지 않습니다.

### 스크립트 없이 수동 설정 (Bash)

```bash
umask 077
read -rs -p 'Dooray token: ' token; printf '\n'
printf '%s\n' "$token" > "$HOME/.dooray-token"
unset token
printf '%s\n' '<project-id>' '<drive-id>' > "$HOME/.dooray-whitelist"
chmod 600 "$HOME/.dooray-token" "$HOME/.dooray-whitelist"
```

예시 ID는 승인된 실제 대상 ID로 바꿉니다. 쓰지 않는다면 허용 목록은 비워 두거나 생략합니다. Windows Git Bash에서는 `$HOME`과 Python의 사용자 홈 `%USERPROFILE%`이 다를 수 있으므로 `bash scripts/setup.sh`를 권장합니다. 파일만 만들어도 쓰기는 켜지지 않으며 아래 승인·정책·`--apply`가 필요합니다.

## 안전한 작업 순서

1. 먼저 읽기로 리소스 ID와 실제 접근 권한을 확인합니다. 입력 예시의 ID는 실제 대상이 아닙니다.
2. 쓰기 전에 대상·내용·예상 영향을 사용자에게 보여 명시적으로 승인받습니다. **실서비스에 시험 메시지나 시험 파일을 만들지 않습니다.**
3. 기본 정책 `deny`에서는 어떤 쓰기도 보내지 않습니다. 승인된 대상 ID만 `~/.dooray-whitelist`(프로젝트/Drive 등) 또는 `DOORAY_WRITE_ALLOWLIST`에 넣고, 필요한 세션에서만 `DOORAY_WRITE_POLICY=allowlist`를 사용합니다. 쓰기 명령의 `--apply`도 별도로 필요합니다. 파일만 등록해도 쓰기는 활성화되지 않습니다.
4. Drive 업로드는 정확한 파일 전용 호스트로의 리디렉션만 허용합니다. 다운로드는 안전한 파일명·기존 파일 덮어쓰기 금지를 지킵니다. 파일 삭제·복사·이동은 현재 지원하지 않습니다. 공유 링크는 `member` 범위만 제공하며, 발급 전 대상과 만료 시각을 확인합니다.
5. 일정 수정은 전체 최종 상태와 `--whole-day` 또는 `--timed`를 명시합니다. 전송·업로드·수정 후에는 다시 조회해 결과를 확인합니다.

## 자주 쓰는 조회 예시 (스킬 디렉터리 기준)

```bash
python scripts/dooray.py me
python scripts/dooray.py project list
python scripts/dooray.py calendar list
python scripts/dooray.py drive list
python scripts/dooray.py drive files '<drive-id>'
```

CLI에 없는 모듈 함수까지 자동 명령으로 제공한다고 가정하지 않습니다. 토큰은 `DOORAY_TOKEN` 환경변수 또는 사용자 홈의 `~/.dooray-token`에서 읽으며, 채팅·로그·저장소에 노출하지 않습니다.
