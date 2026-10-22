# 카카오 데일리 브리핑 자동발송

## 현재 상태와 발송 방식

GitHub Actions와 네이버클라우드 SENS 브랜드 메시지 API 연동 코드입니다.
서비스 계약·과금 동의·비즈니스 채널 등록·비밀키·수신자 등록은 별도이며,
이 코드 등록 자체가 카카오 채널 자동발송 개통을 의미하지 않습니다.
기존 일반 채널만으로 API 발송이 가능하다고 가정하지 않습니다.

- 한국시간 매일 08:10/08:40/09:10/09:40/10:10/10:40에 확인합니다.
- GitHub 스케줄은 지연될 수 있으므로 정확한 정시 발송을 보장하지 않습니다.
- 매일 당일자 브리핑을 처음 확인했을 때 한 번만 발송을 요청합니다.
- **브리핑을 새로 작성하는 기능은 아닙니다.** 기존 브리핑 발행 작업이 계속 필요합니다.
- 메인 페이지가 현재 main의 HTML과 같고, RSS 첫 게시물 및 연결 페이지가 당일자여야 합니다.
- 메시지: 날짜, 상위 기사 제목 3개, `오늘 브리핑 보기` 웹 링크 버튼.
- SENS의 `I` 타겟: 등록한 수신 동의 대상과 채널 친구의 교집합으로 발송합니다.
  채널 친구 전체를 자동으로 조회·수집하는 기능은 없습니다.
- 대상은 처음 50명 이내, 향후 200명까지 설정할 수 있습니다.
- 자동 문자 대체 발송은 사용하지 않습니다.

## 1. 외부 서비스 준비

1. 네이버클라우드 계정 및 SENS Biz Message/브랜드 메시지 이용을 신청합니다.
   계약·결제·단가는 계정 소유자가 확인합니다. 비용은 가입 상품의 실제 단가에 따릅니다.
2. 카카오 비즈니스 인증 채널을 등록하고 SENS 채널 등록 절차를 마칩니다.
3. SENS 프로젝트의 Service ID와 API Access Key/Secret Key를 발급합니다.
4. 사용할 채널 ID(`@`로 시작)를 확인합니다.
5. 발송에 동의했고 채널을 추가한 수신자의 전화번호 목록을 준비합니다.
   기존 채널 친구가 있다는 것만으로 전화번호를 자동 확보할 수는 없습니다.
6. 본문 표기·수신거부 표시 등 상품별 발송 요건을 서비스 콘솔에서 확인합니다.

## 2. GitHub 보안 설정 등록

저장소 → Settings → Secrets and variables → Actions → Secrets에서 아래 5개를 등록합니다.
**키와 실제 전화번호를 공개 파일·Issue·대화창에 붙여넣지 마세요.**

| Secret | 내용 |
|---|---|
| `SENS_ACCESS_KEY` | Ncloud API Access Key |
| `SENS_SECRET_KEY` | Ncloud API Secret Key |
| `SENS_SERVICE_ID` | SENS 브랜드 메시지 서비스 ID |
| `KAKAO_CHANNEL_ID` | SENS에 등록한 `@채널ID` |
| `KAKAO_RECIPIENTS_JSON` | 아래 형식의 수신 동의 대상 목록 |

형식 예시(가상 번호):

```json
[{"countryCode":"82","to":"01000000000","consent":true}]
```

국가코드와 번호는 서비스가 요구하는 형식으로 등록하고 해외번호는 실제 지원 여부를 확인합니다.
수신 동의 철회자는 이 목록에서도 제거합니다.

Variables 탭:

| Variable | 값 |
|---|---|
| `KAKAO_MAX_RECIPIENTS` | `50` (필요 시 최대 `200`) |
| `KAKAO_ENABLED` | 최초 테스트 준비 전에는 미설정 또는 `false` |

Actions가 활성화되어 있어야 합니다. 발송 job은 날짜 잠금을 기록하기 위해
`contents: write` 권한을 사용합니다. 조직 정책에서 차단하면 관리자가 허용 범위를 확인해야 합니다.

## 3. 미리보기 → 본인 1명 테스트 → 운영

1. Actions → **Kakao daily briefing** → Run workflow → `preview`.
   당일 게시물의 실사이트 검증과 메시지 미리보기만 실행하며 외부 발송은 하지 않습니다.
2. `KAKAO_RECIPIENTS_JSON`에는 먼저 본인 번호 1개만 등록합니다.
3. 자동 스케줄 시간대 밖에서 `KAKAO_ENABLED=true`를 등록하고 곧바로
   Run workflow → `send`를 실행합니다(한국시간 08:00~20:49).
4. 실제 카카오톡 수신·버튼 링크·SENS 발송 결과를 확인합니다.
5. 검증 후 동의한 나머지 대상 번호를 등록합니다. **같은 날짜에는 대상이 늘어도 재발송하지 않습니다.**
   전체 운영 발송은 다음 날짜의 브리핑부터 시작합니다.

## 4. 중복발송과 장애 처리

- 저장소의 별도 `kakao-delivery-state` 브랜치에 날짜별 잠금을 먼저 기록합니다.
- 발송 POST는 자동 재시도하지 않습니다. 타임아웃 후 수신 여부가 모호하면 날짜를 잠근 채 중지합니다.
- API 접수(`accepted`)와 실제 수신 성공(`delivered`)을 구분합니다.
- 이후 스케줄은 이미 접수한 요청의 수신 결과만 조회합니다. 새로 발송하지 않습니다.
- 일부 실패는 건수만 기록하고 실패 처리합니다. 실패 번호는 SENS 콘솔에서 확인합니다.
- 날짜 잠금에는 전화번호·메시지 전문·API 키를 기록하지 않습니다.
  공개 저장소이므로 발송 날짜·건수·요청 ID·결과 통계는 공개됩니다.
- `pending` 상태에서 멈췄으면 SENS 콘솔에서 실제 접수·수신 여부를 확인합니다.
  확인 전 날짜 잠금을 삭제하거나 강제로 재발송하지 않습니다.
- 자동 발송 중지: `KAKAO_ENABLED=false`. 이미 접수된 발송을 취소하는 기능은 아닙니다.
- 해당 날짜의 최종 스케줄 이후 발행된 게시물은 자동발송되지 않습니다.
  필요한 경우 같은 워크플로를 `send`로 실행하면 같은 검증·중복 방지 절차를 적용합니다.

## 공식 API 근거

- [SENS 브랜드 메시지 발송](https://api.ncloud-docs.com/docs/sens-brandmessage-send)
- [SENS 발송 결과 목록](https://api.ncloud-docs.com/docs/sens-brandmessage-list)
- [SENS 인증 헤더](https://api.ncloud-docs.com/docs/sens-overview)
- [카카오 브랜드 메시지 시작 조건](https://kakaobusiness.gitbook.io/main/ad/brandmessage)

로컬 검증: `python -m unittest discover -s tests -v`

미리보기: `python scripts/kakao_daily.py`
