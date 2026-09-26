# 개인 토큰 및 쓰기 허용 목록 설정

설치된 `skills/dooray` 디렉터리에서 `bash scripts/setup.sh`를 실행하세요. 스크립트는 개인 토큰을 화면에 표시하지 않고 사용자 홈의 `.dooray-token`에, 허용 리소스 ID를 한 줄에 하나씩 `.dooray-whitelist`에 저장합니다. `--whitelist`는 기존 토큰을 그대로 두고 ID 목록만 다시 입력합니다. 관리자 토큰은 지원하지 않습니다.

스크립트 없이 수동으로 설정하려면 Bash에서 아래와 같이 **대화형 숨김 입력**을 사용하세요. 명령 인자·채팅·저장소에 비밀값을 남기지 마세요.

```bash
umask 077
read -rs -p 'Dooray token: ' token; printf '\n'
printf '%s\n' "$token" > "$HOME/.dooray-token"
unset token
printf '%s\n' '<project-id>' '<drive-id>' > "$HOME/.dooray-whitelist"
chmod 600 "$HOME/.dooray-token" "$HOME/.dooray-whitelist"
```

예시 ID는 실제 허용할 대상 ID로 교체하세요. Windows Git Bash에서는 `$HOME`과 Python의 사용자 홈 `%USERPROFILE%`이 다를 수 있으므로 **설정 스크립트 사용을 권장**합니다. Windows 파일 접근 제어는 ACL에도 좌우됩니다.

허용 목록 파일만으로는 쓰기가 활성화되지 않습니다. 승인받은 작업에서만 `DOORAY_WRITE_POLICY=allowlist`로 설정하고 `--apply`를 함께 사용합니다. `DOORAY_WRITE_ALLOWLIST`가 **존재하면 파일보다 우선**하며, 명시적으로 빈 값으로 설정하면 빈 목록이 적용되어 모두 거부됩니다. 변수를 아예 설정하지 않았을 때만 홈의 파일을 사용합니다. 쓰기 기본 정책은 `deny`입니다.
