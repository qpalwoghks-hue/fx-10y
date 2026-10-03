# 환율 10년 비교

17개 통화의 현재 원화 환율을 최근 10년 평균·중앙값과 비교해 보여주는 모바일 웹앱입니다.
통화 버튼은 매일 "10년 중 지금이 싼 순서"로 정렬됩니다.

- `index.html` — 앱 화면. 같은 폴더의 `rates.json`을 읽습니다(없으면 Frankfurter API로 15개 통화만 표시).
- `fetch_rates.py` — 한국은행 ECOS에서 최근 10년 일별 매매기준율을 받아 `rates.json`으로 저장합니다.
  환율이 그대로인 날(주말/공휴일)에는 파일을 건드리지 않습니다.
- `.github/workflows/update.yml` — GitHub Actions가 매일 한국시간 09:00, 18:00에 `fetch_rates.py`를 실행하고,
  바뀐 데이터를 커밋한 뒤 GitHub Pages로 배포합니다.

## 인증키

ECOS 인증키(https://ecos.bok.or.kr/api/)는 저장소에 올리지 않습니다.

- GitHub: 저장소 Settings > Secrets and variables > Actions에 `ECOS_API_KEY`로 등록
- 로컬 실행: 환경변수 `ECOS_API_KEY` 또는 이 폴더의 `ecos_key.txt`(키 한 줄)

```bash
python fetch_rates.py
```
