"""한국은행 ECOS에서 최근 10년 일별 원화 환율(매매기준율)을 받아 rates.json으로 저장.

환율비교/index.html이 같은 폴더의 rates.json을 읽어서 화면에 보여준다. ECOS는 브라우저에서
직접 호출할 수 없어서(CORS 미지원) 이 스크립트로 미리 받아두는 구조다.

인증키: https://ecos.bok.or.kr/api/ 에서 무료 발급.
환경변수 ECOS_API_KEY 또는 이 스크립트 옆 ecos_key.txt(키 한 줄)에 넣어두면 된다.

    python fetch_rates.py
"""

import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta

STAT_CODE = "731Y001"  # 3.1.1.1. 주요국 통화의 대원화환율 (일별)

# (통화코드, ECOS 항목코드, 표시 단위) - 단위는 ECOS가 주는 기준 그대로 (엔/루피아/동은 100단위)
CURRENCIES = [
    ("USD", "0000001", 1),
    ("JPY", "0000002", 100),
    ("EUR", "0000003", 1),
    ("CNY", "0000053", 1),
    ("VND", "0000035", 100),
    ("HKD", "0000015", 1),
    ("TWD", "0000031", 1),
    ("THB", "0000028", 1),
    ("SGD", "0000024", 1),
    ("PHP", "0000034", 1),
    ("IDR", "0000029", 100),
    ("MYR", "0000025", 1),
    ("GBP", "0000012", 1),
    ("CAD", "0000013", 1),
    ("AUD", "0000017", 1),
    ("NZD", "0000026", 1),
    ("CHF", "0000014", 1),
]

YEARS = 10


def base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def load_key():
    key = os.environ.get("ECOS_API_KEY", "").strip()
    if key:
        return key
    # 탐색기가 확장자를 숨기는 설정이면 "ecos_key.txt"로 이름을 바꿔도 실제로는 .txt.txt가 됨
    for name in ("ecos_key.txt", "ecos_key.txt.txt"):
        path = os.path.join(base_dir(), name)
        if os.path.exists(path):
            # 메모장이 BOM을 붙여 저장하는 경우가 있어 utf-8-sig로 읽음
            with open(path, encoding="utf-8-sig") as f:
                key = f.read().strip()
            if key:
                return key
            sys.exit("{} 파일이 비어 있습니다. 인증키를 붙여넣고 저장해 주세요.".format(name))
    sys.exit("ECOS 인증키가 없습니다. 환경변수 ECOS_API_KEY 또는 ecos_key.txt에 넣어주세요.")


def fetch_item(key, item_code, start, end):
    # 공개 테스트키 "sample"은 최대 10건까지만 허용됨(동작 확인용)
    rows = 10 if key == "sample" else 100000
    url = "https://ecos.bok.or.kr/api/StatisticSearch/{}/json/kr/1/{}/{}/D/{}/{}/{}".format(
        urllib.parse.quote(key), rows, STAT_CODE, start, end, item_code)
    with urllib.request.urlopen(url, timeout=60) as res:
        data = json.load(res)
    if "StatisticSearch" not in data:
        # {"RESULT": {"CODE": "INFO-200", "MESSAGE": "해당하는 데이터가 없습니다."}} 형태
        result = data.get("RESULT", {})
        raise RuntimeError("{} {}".format(result.get("CODE"), result.get("MESSAGE")))
    out = {}
    for row in data["StatisticSearch"]["row"]:
        value = row.get("DATA_VALUE")
        if value in (None, "", "-"):
            continue
        t = row["TIME"]
        out["{}-{}-{}".format(t[:4], t[4:6], t[6:])] = float(value)
    return out


def main():
    key = load_key()
    end = date.today()
    start = end.replace(year=end.year - YEARS) if not (end.month == 2 and end.day == 29) \
        else end - timedelta(days=365 * YEARS)
    start_s, end_s = start.strftime("%Y%m%d"), end.strftime("%Y%m%d")

    by_code = {}
    for code, item, unit in CURRENCIES:
        rows = fetch_item(key, item, start_s, end_s)
        print("{}: {}일 ({} ~ {})".format(code, len(rows), min(rows), max(rows)))
        by_code[code] = (unit, rows)

    # 날짜 배열은 한 번만 두고 통화별 값은 그 순서에 맞춘 배열로 저장(파일 크기 절약)
    dates = sorted({d for _, rows in by_code.values() for d in rows})
    payload = {
        "source": "한국은행 ECOS 매매기준율",
        "updated": datetime.now().isoformat(timespec="minutes"),
        "dates": dates,
        "series": {
            code: {"unit": unit, "values": [rows.get(d) for d in dates]}
            for code, (unit, rows) in by_code.items()
        },
    }
    path = os.path.join(base_dir(), "rates.json")
    # 환율이 그대로면(주말/공휴일) 파일을 건드리지 않음 - GitHub Actions가 바뀐 날에만 커밋하도록
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                old = json.load(f)
            if old.get("dates") == payload["dates"] and old.get("series") == payload["series"]:
                print("변경 없음: 기존 rates.json 유지")
                return
        except ValueError:
            pass  # 깨진 파일이면 새로 씀
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, path)
    print("저장: {} ({:.0f} KB)".format(path, os.path.getsize(path) / 1024))


if __name__ == "__main__":
    main()
