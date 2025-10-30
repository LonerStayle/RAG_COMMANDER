import json
import requests


API_URL = "https://www.reb.or.kr/r-one/openapi/SttsApiTblData.do"

DEFAULT_PARAMS = {
    "STATBL_ID": "A_2024_00076",
    "KEY": "cc47bc2e1d1a4836b563bdd1226a9af8",
    "Type": "json",
    "DTACYCLE_CD": "MM",
    "WRTTIME_IDTFR_ID": "202410",
    "pIndex": 1,
    "pSize": 1000,
}


def fetch_trade_balance_rows():
    try:
        response = requests.get(API_URL, params=DEFAULT_PARAMS, timeout=10)
    except requests.RequestException:
        return []

    if response.status_code != 200:
        return []

    data = response.json()
    table = data.get("SttsApiTblData")
    if not table or len(table) < 2:
        return []

    rows = table[1].get("row")
    if not isinstance(rows, list):
        return []

    return rows


def get_trade_balance(address: str) -> str:
    trimmed = (address or "").strip()
    if not trimmed:
        return json.dumps([], ensure_ascii=False)

    rows = fetch_trade_balance_rows()

    results = [
        {
            "지역": item.get("CLS_FULLNM", ""),
            "날짜": item.get("WRTTIME_DESC", ""),
            "매매수급지수": item.get("DTA_VAL", ""),
        }
        for item in rows
        if trimmed.lower() in (item.get("CLS_FULLNM") or "").lower()
    ]

    return json.dumps(results, ensure_ascii=False)


if __name__ == "__main__":
    print(get_trade_balance("서울"))
