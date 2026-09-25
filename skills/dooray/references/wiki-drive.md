# 위키·Drive 제한

위키 경로의 공개 근거: [Dooray Go SDK 위키](https://github.com/dooray-go/dooray-sdk/tree/develop/openapi/wiki). 조회로 대상과 권한을 확인한 뒤, 수정에는 사용자 승인을 받으세요. 현재 CLI에는 위키 목록만 있으며, 페이지 조회·생성·수정은 Python 모듈 함수로 제공됩니다.

**Drive는 미지원입니다.** 공개 자료에서 정확한 Drive API 경로를 확인하고 모의 테스트를 갖추기 전에는 임의의 경로로 요청하지 않습니다. 위키 파일 업로드가 Drive API 근거가 되는 것은 아닙니다. 향후 다운로드에는 파일명·경로 검증, 업로드에는 리디렉션 대상에 인증 헤더가 전달되지 않는 검사가 필요합니다.
