# 위키·Drive

위키 경로의 공개 구현 근거: [Dooray Go SDK 위키](https://github.com/dooray-go/dooray-sdk/tree/develop/openapi/wiki). 현재 CLI는 위키 목록 조회를 제공하며 페이지 조회·생성·수정은 Python 모듈 함수로만 제공합니다. 쓰기에는 사용자 승인과 정책 허용·`--apply`가 필요합니다.

Drive는 **현재 공개본에 구현돼 있습니다**. 목록·메타·원본 다운로드와, 승인된 업로드·폴더 생성·멤버 공유 링크 발급 등을 지원합니다. 엔드포인트와 과거 검증/현재 테스트의 구분은 [Drive 문서](drive.md), [검증 현황](verification.md)에서 확인하세요. 실제 새 구현의 라이브 검증은 아직 하지 않았습니다.
