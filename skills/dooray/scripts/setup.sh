#!/usr/bin/env bash
# Interactive personal-token setup; never put credentials in shell arguments/history.
set -euo pipefail
umask 077

# Git Bash may assign a different HOME than native Windows Python Path.home().
if command -v cygpath >/dev/null 2>&1 && [[ -n ${USERPROFILE:-} ]]; then
  config_home=$(cygpath -u "$USERPROFILE")
else
  config_home=$HOME
fi

if [[ $# -gt 1 || ( $# -eq 1 && $1 != --whitelist ) ]]; then
  printf 'Usage: bash scripts/setup.sh [--whitelist]\n' >&2
  exit 2
fi

save_private() {
  local destination=$1 value=$2 tmp
  tmp=$(mktemp "${destination}.tmp.XXXXXXXX")
  chmod 600 "$tmp"
  if ! printf '%s' "$value" > "$tmp"; then
    rm -f "$tmp"
    return 1
  fi
  if ! mv -f "$tmp" "$destination"; then
    rm -f "$tmp"
    return 1
  fi
}

if [[ ${1:-} != --whitelist ]]; then
  printf 'Dooray 개인 API 토큰 입력 (화면에 표시되지 않습니다): ' >&2
  IFS= read -rs token || { printf '\n입력이 취소되었습니다.\n' >&2; exit 1; }
  printf '\n' >&2
  token=${token%$'\r'}
  if [[ -z $token ]]; then
    printf '빈 토큰은 저장할 수 없습니다.\n' >&2
    exit 1
  fi
  save_private "$config_home/.dooray-token" "$token"$'\n'
  unset token
  printf '개인 토큰을 홈 디렉터리에 저장했습니다.\n' >&2
fi

printf '쓰기 허용 대상 ID를 한 줄에 하나씩 입력하세요 (빈 줄로 종료).\n' >&2
printf '모두 비워 두면 쓰기가 거부됩니다.\n' >&2
ids=''
while IFS= read -r id; do
  id=${id%$'\r'}
  [[ -z $id ]] && break
  if [[ ! $id =~ ^[A-Za-z0-9_.*:-]+$ || $id == '.' || $id == '..' ]]; then
    printf '잘못된 대상 ID입니다. 저장하지 않았습니다.\n' >&2
    exit 1
  fi
  ids+="$id"$'\n'
done
save_private "$config_home/.dooray-whitelist" "$ids"
printf '허용 목록을 홈 디렉터리에 저장했습니다. 실제 쓰기에는 DOORAY_WRITE_POLICY=allowlist와 --apply가 모두 필요합니다.\n' >&2
