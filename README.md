# Global · Korea Daily Brief

새 통합 브리핑 전용 GitHub Pages 사이트입니다.

구성:
- `index.html` : 항상 최신 브리핑
- `archive/YYYY-MM-DD.html` : 날짜별 보관
- `archive/index.html` : 지난 브리핑 목록
- `.nojekyll` : GitHub Pages 정적 배포용

현재 최초 기준일: 2026-10-14
내용: 글로벌·테크 5건 + 국내 디지털·IT·보안 5건 + Watch Board

이 패키지는 과거 `global_news` 뉴스데일리 콘텐츠를 재사용하지 않았습니다.

## 자동 발행

ChatGPT의 통합 브리핑 예약에서 오전 8시경(Asia/Seoul) 실행합니다.
- `archive/YYYY-MM-DD.html`: 해당 날짜 브리핑을 보관합니다.
- `archive/index.html`: 이전 날짜 목록을 보존하고 새 날짜를 추가합니다.
- `index.html`: 최신 날짜의 보관 HTML과 동일하게 갱신합니다.
- 업로드·배포 확인 후 최신 링크와 오늘자 보관 링크를 안내합니다.
- 업로드 실패 시 갱신 성공으로 표시하지 않고 오류와 HTML 파일을 제공합니다.

발행 대상은 공개 뉴스 브리핑이며, 개인 일정·메일·내부 문서·인증정보를 게시하지 않습니다.

## 카카오 자동발송 연동

당일 GitHub Pages와 RSS 게시본을 검증한 후 카카오 브랜드 메시지 API로 발송하는
워크플로를 추가했습니다. 날짜별 중복발송 방지와 실제 수신 결과 조회를 포함합니다.
기본 상태는 미개통이며, 외부 서비스 등록과 Secrets 설정 후 활성화해야 합니다.

[설정·본인 테스트·운영 안내](docs/kakao-setup.md)
