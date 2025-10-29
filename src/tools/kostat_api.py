import os
import time
import requests


class SgisAPI:
    access_token = None
    token_expire = 0  # timestamp

    @classmethod
    def get_access_token(cls):
        """토큰이 만료되었으면 새로 발급받고, 아니면 캐시된 토큰을 반환"""
        if cls.access_token and time.time() < cls.token_expire:
            return cls.access_token

        AUTH_URL = "https://sgisapi.kostat.go.kr/OpenAPI3/auth/authentication.json"
        KOSIS_CONSUMER_KEY = os.getenv("KOSIS_CONSUMER_KEY")
        KOSIS_CONSUMER_SECRET_KEY = os.getenv("KOSIS_CONSUMER_SECRET_KEY")

        params = {
            "consumer_key": KOSIS_CONSUMER_KEY,
            "consumer_secret": KOSIS_CONSUMER_SECRET_KEY,
        }

        response = requests.get(AUTH_URL, params=params)
        data = response.json()

        if data.get("errCd") == 0:
            cls.access_token = data["result"]["accessToken"]
            cls.token_expire = time.time() + 3500  # 1시간(3600초) - 안전하게 3500초
            return cls.access_token
        else:
            raise Exception(f"❌ 토큰 발급 실패: {data}")

    @classmethod
    def request_api(cls, url: str, params: dict):
        token = cls.get_access_token()
        params["accessToken"] = token
        res = requests.get(url, params=params)
        data = res.json()

        if (
            data.get("errCd") == -100
            and "accessToken" in str(data.get("errMsg", "")).lower()
        ):
            print("⚠️ accessToken 만료됨 → 재발급 중...")
            cls.access_token = None
            token = cls.get_access_token()
            params["accessToken"] = token
            res = requests.get(url, params=params)
            data = res.json()

        return data


adm_dict = {
    "종로구": "11010",
    "중구": "11020",
    "용산구": "11030",
    "성동구": "11040",
    "광진구": "11050",
    "동대문구": "11060",
    "중랑구": "11070",
    "성북구": "11080",
    "강북구": "11090",
    "도봉구": "11100",
    "노원구": "11110",
    "은평구": "11120",
    "서대문구": "11130",
    "마포구": "11140",
    "양천구": "11150",
    "강서구": "11160",
    "구로구": "11170",
    "금천구": "11180",
    "영등포구": "11190",
    "동작구": "11200",
    "관악구": "11210",
    "서초구": "11220",
    "강남구": "11230",
    "송파구": "11240",
    "강동구": "11250",
}


# 10년 이상 노후도
def get_10_year_after_house(gu_address: str):
    HOUSE_URL = "https://sgisapi.kostat.go.kr/OpenAPI3/stats/house.json"
    params = {
        "year": "2020",  # 기준연도 (2015~2023)
        "adm_cd": [adm_dict[gu_address]],  # 행정구역 코드 (서울특별시)
        "low_search": "0",
        # 10년 이상들 조회
        "const_year": ["06", "07", "08", "09", "10", "11"],
    }
    response = SgisAPI.request_api(HOUSE_URL, params)
    return response["result"]


# 1인당 GDP 조회
def get_one_people_gdp():
    # https://spot.wooribank.com/pot/Dream?withyou=FXXRT0016
    # 우리은행 외환센터 연도별 기준 (송금 수신, 발신의 중간값)
    exchange_rate = {
        "2018": 1100,
        "2019": 1160,
        "2020": 1180,
        "2021": 1140,
        "2022": 1290,
        "2023": 1310,
        "2024": 1360,
    }

    one_people_gdp_dollar = {
        "2018": 33447,
        "2019": 31902,
        "2020": 31721,
        "2021": 35125,
        "2022": 32394,
        "2023": 33121,
        "2024": 36624,
    }

    def get_krw(exchange_rate, dollar):
        return exchange_rate * dollar

    one_people_gdp_dollar = {
        "2018": get_krw(exchange_rate["2018"], one_people_gdp_dollar["2018"]),
        "2019": get_krw(exchange_rate["2019"], one_people_gdp_dollar["2019"]),
        "2020": get_krw(exchange_rate["2020"], one_people_gdp_dollar["2020"]),
        "2021": get_krw(exchange_rate["2021"], one_people_gdp_dollar["2021"]),
        "2022": get_krw(exchange_rate["2022"], one_people_gdp_dollar["2022"]),
        "2023": get_krw(exchange_rate["2023"], one_people_gdp_dollar["2023"]),
        "2024": get_krw(exchange_rate["2024"], one_people_gdp_dollar["2024"]),
    }

    return one_people_gdp_dollar


# 각 csv 리턴 
import pandas as pd
from utils.util import get_project_root


def get_age_population():
    return pd.read_csv(
        get_project_root()
        / "src"
        / "data"
        / "202504_202509_연령별인구현황_월간 - 최종.csv",
        index_col=0,
    )


def get_move_people2025():
    return pd.read_excel(
        get_project_root()
        / "src"
        / "data"
        / "인구이동_전출입_2025년_1~8월_합산.xlsx"
    )

def get_move_people2024():
    return pd.read_excel(
        get_project_root()
        / "src"
        / "data"
        / "인구이동_전출입_2024년(연간) - 최종.xlsx"
    )


