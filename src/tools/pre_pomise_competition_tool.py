import json
import time
import requests


SERVICE_KEY = "nEmoa4/43u4WcWznQBC8b4Cd0x6Py+Pz20kqQs6G54f2+fK5gPX084Mv/ss5wMEU1noKUrOhMAxLEooMd69UDw=="
COMPETITION_URL = (
    "https://api.odcloud.kr/api/ApplyhomeInfoCmpetRtSvc/v1/getAPTLttotPblancCmpet"
)
DETAIL_URL = (
    "https://api.odcloud.kr/api/ApplyhomeInfoDetailSvc/v1/getAPTLttotPblancDetail"
)
COMMON_PARAMS = {"page": 1, "perPage": 1000, "serviceKey": SERVICE_KEY}


def _fetch_rows(url):
    response = requests.get(url, params=COMMON_PARAMS)
    data = response.json()
    rows = data.get("data")
    if rows is None:
        raise ValueError(f"API 응답에 data가 없습니다: {data}")
    return rows


def _clean_rate(raw_rate):
    rate = (raw_rate or "").replace("(", "").replace(")", "").replace("△", "")
    return f"{rate}:1" if rate else ""


def _build_dataset():
    competition_rows = _fetch_rows(COMPETITION_URL)
    detail_rows = _fetch_rows(DETAIL_URL)
    detail_map = {
        (item.get("HOUSE_MANAGE_NO"), item.get("PBLANC_NO")): item
        for item in detail_rows
    }

    dataset = []
    for item in competition_rows:
        key = (item.get("HOUSE_MANAGE_NO"), item.get("PBLANC_NO"))
        detail = detail_map.get(key)
        if detail is None:
            continue

        dataset.append(
            {
                "주소": detail.get("HSSPLY_ADRES", ""),
                "공고일": detail.get("RCRIT_PBLANC_DE", ""),
                "경쟁률": _clean_rate(item.get("CMPET_RATE", "")),
            }
        )

    return dataset


class PrePromiseCompetitionTool:
    dataset = []
    last_loaded = 0

    @classmethod
    def load(cls):
        cls.dataset = _build_dataset()
        cls.last_loaded = time.time()
        return cls.dataset

    @classmethod
    def search(cls, address: str, as_json: bool = False):
        if not cls.dataset:
            cls.load()

        trimmed = (address or "").strip()
        matched = [
            row for row in cls.dataset if trimmed and trimmed in row.get("주소", "")
        ]

        if as_json:
            return json.dumps(matched, ensure_ascii=False, indent=2)
        return matched


if __name__ == "__main__":
    tool = PrePromiseCompetitionTool()
    sample_result = tool.search("경기도 의정부시")
    print(json.dumps(sample_result, ensure_ascii=False, indent=2))

"""
  from src.tools.pre_pomise_competition_tool import PrePromiseCompetitionTool

  tool = PrePromiseCompetitionTool()
  results = tool.search("서울 강남구")
"""