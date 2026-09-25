---
name: dooray
description: Dooray 개인 API 토큰으로 프로젝트 업무·위키·캘린더·메신저를 조회하거나 사용자 승인 후 변경할 때 사용합니다. 기본 읽기 전용이며 쓰기에는 별도 정책과 적용 옵션이 필요합니다.
---
# Dooray Agent Skill

이 스킬 디렉터리에서 `python scripts/dooray.py --help`로 지원 명령을 확인하세요. Python 3.10+와 개인 API 토큰(`DOORAY_TOKEN` 또는 홈 디렉터리의 `~/.dooray-token`)이 필요합니다. 토큰을 채팅·로그·저장소에 노출하지 마세요. 기본 API 주소는 `https://api.dooray.com`입니다.

계정·업무·위키·캘린더·메신저 중 필요한 항목의 `references/*.md`만 읽으세요. **Drive·연락처·관리자 API는 구현하지 않았습니다.** 토큰에 따른 실제 접근 권한과 이 저장소의 구현 범위는 다릅니다.

## 안전한 작업 순서

1. 조회 명령으로 대상과 ID를 확인합니다. 예시 ID를 실제 대상으로 간주하지 않습니다.
2. 쓰기 전에 대상·전송 본문·예상 영향을 사용자에게 보여 주고 명시적으로 승인을 받습니다.
3. 기본 쓰기 정책은 `deny`입니다. 승인된 쓰기만 `DOORAY_WRITE_POLICY=allow` 또는 `allowlist` + `DOORAY_WRITE_ALLOWLIST`를 설정하고 `--apply`를 전달합니다. 둘 중 하나라도 빠지면 쓰기 요청을 보내지 않습니다.
4. 삭제·메시지 전송·일정 수정은 되돌릴 수 있다고 가정하지 않습니다. 수정할 일정은 최종 상태를 확인하고, `--whole-day` 또는 `--timed`를 명시합니다. 쓰기 후에는 다시 조회합니다.
5. 검증 목적으로 실제 메시지를 보내거나 일정을 생성하지 않습니다. 단위 테스트는 네트워크를 모의 처리합니다.

## 로컬 실행

```bash
python scripts/dooray.py me
python scripts/dooray.py project list
python scripts/dooray.py calendar list
```

Claude Code·Codex 설치 경로와 초기 토큰 설정은 저장소 루트 [`README.md`](../../README.md)를 참고하세요. 별도 Python 패키지 설치는 필요하지 않습니다.
