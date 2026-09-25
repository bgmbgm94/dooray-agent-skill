# 캘린더·메신저

공개 근거: [Dooray Go SDK 캘린더](https://github.com/dooray-go/dooray-sdk/tree/develop/openapi/calendar), [메신저](https://github.com/dooray-go/dooray-sdk/tree/develop/openapi/messenger).

- `GET /calendar/v1/calendars`: 접근 가능한 캘린더를 조회합니다.
- 일정 목록 조회에는 `timeMin`, `timeMax`와 캘린더 ID가 필요합니다. CLI는 공개 SDK 형식인 `/calendar/v1/calendars/*/events`에 `calendars` 필터를 보냅니다.
- 종일 일정은 `wholeDayFlag: true`이며, 사람이 지정한 **종료 포함일**을 API의 **종료 미포함일**(다음 날)로 변환합니다. 대상 캘린더의 시간대를 확인하세요.
- 일정 수정(`event-update`)에는 원하는 최종 상태를 모두 전달하고 `--whole-day` 또는 `--timed`를 명시합니다. 변경 요청에 `wholeDayFlag`를 반드시 포함합니다. 근거: [수정 엔드포인트](https://github.com/dooray-go/dooray-sdk/blob/develop/openapi/calendar/updateevents.go)와 [요청 모델](https://github.com/dooray-go/dooray-sdk/blob/develop/openapi/model/calendar/updateevent_request.go).
- `GET /messenger/v1/channels`: 채널 목록을 조회합니다.
- `POST /messenger/v1/channels/direct-send`: 실제 DM을 보냅니다. 시험용 전송을 하지 말고 수신자 ID와 본문을 사용자에게 확인받은 뒤 정책과 `--apply`를 적용하세요.

이 Python 구현의 테스트는 네트워크 모의 호출입니다. 이 토큰으로 위 모든 기능의 실제 전송이 성공했다고 주장하지 않습니다.
