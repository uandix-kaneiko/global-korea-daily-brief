# Tech & Global News Daily

공개 금융·경제·은행·지급결제·IT 기술·AI·클라우드·사이버보안 뉴스를 다루는 경영진 브리핑입니다.

- [최신 브리핑](https://uandix-kaneiko.github.io/global-korea-daily-brief/latest.html)
- [지난 브리핑](https://uandix-kaneiko.github.io/global-korea-daily-brief/archive/index.html)
- [RSS](https://uandix-kaneiko.github.io/global-korea-daily-brief/feed.xml)

업로드된 블랙·골드 시안을 바탕으로 핵심 메시지, 3D TG 비주얼, 세 가지 판단 보드와 분야별 전체 기사를 제공합니다.

## 발행

공개 자료를 확인한 날짜별 데이터를 `data/briefing-YYYY-MM-DD.json`에 작성한 뒤 다음 명령으로 렌더링합니다.

```bash
python scripts/render_briefing.py --date YYYY-MM-DD
```

루트·최신·당일 페이지를 동일 본문으로 갱신하고 과거 파일을 보존합니다. RSS는 중복 없이 해당 날짜 항목을 맨 위에 유지하며 이전 항목을 보존합니다. 실제 공개사이트 반영을 확인한 후 완료를 보고합니다.

[편집·디자인·검증 기준](docs/editorial-design.md)

## 카카오 연동

기본 상태는 미개통입니다. 등록·설정과 실제 수신 확인을 완료한 뒤에만 발송 성공으로 표시합니다.

[설정·본인 테스트·운영 안내](docs/kakao-setup.md)
