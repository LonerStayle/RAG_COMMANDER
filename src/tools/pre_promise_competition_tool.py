"""
청약 경쟁률 조회 도구

이 도구는 공공데이터포털의 청약경쟁률 API를 사용하여
주소로 청약 경쟁률을 조회합니다.

데이터 출처: 공공데이터포털 (https://www.data.go.kr/)
- API: ApplyhomeInfoCmpetRtSvc (청약경쟁률 서비스)
- API: ApplyhomeInfoDetailSvc (청약 상세정보 서비스)
"""

import json
import requests
import pandas as pd
from langchain_core.tools import tool


# API 설정 (공공데이터포털 서비스키)
SERVICE_KEY = "nEmoa4/43u4WcWznQBC8b4Cd0x6Py+Pz20kqQs6G54f2+fK5gPX084Mv/ss5wMEU1noKUrOhMAxLEooMd69UDw=="

# API URL
COMPETITION_URL = (
    "https://api.odcloud.kr/api/ApplyhomeInfoCmpetRtSvc/v1/getAPTLttotPblancCmpet"
)
DETAIL_URL = (
    "https://api.odcloud.kr/api/ApplyhomeInfoDetailSvc/v1/getAPTLttotPblancDetail"
)


def get_all_data():
    """API에서 모든 경쟁률 데이터 가져오기"""
    params = {"page": 2, "perPage": 1000, "serviceKey": SERVICE_KEY}

    response = requests.get(COMPETITION_URL, params=params)
    competition_data = response.json()

    response_detail = requests.get(DETAIL_URL, params=params)
    detail_data = response_detail.json()

    df_competition = pd.DataFrame(competition_data.get("data", []))
    df_detail = pd.DataFrame(detail_data.get("data", []))

    print(df_competition)
    # 두 데이터 합치기
    df_merged = df_competition.merge(
        df_detail, on=["HOUSE_MANAGE_NO", "PBLANC_NO"], how="inner"
    )

    # 경쟁률 정리
    df_merged["경쟁률"] = (
        df_merged["CMPET_RATE"]
        .str.replace("(", "")
        .str.replace(")", "")
        .str.replace("△", "")
        + ":1"
    )

    # 필요한 컬럼만 선택
    df_result = df_merged[["HSSPLY_ADRES", "RCRIT_PBLANC_DE", "경쟁률"]].copy()
    df_result.columns = ["주소", "공고일", "경쟁률"]

    return df_result


def extract_gu_or_si(address):
    """주소에서 '구' 또는 '시' 단위 지역 추출 (시도 포함)"""
    # 주소를 공백으로 나누기
    parts = address.split()

    # '구' 또는 '시'로 끝나는 부분과 그 앞부분 찾기
    # 예: "경기도 양주시" → "경기도 양주시" 추출
    gu_or_si = ""
    found_idx = -1

    # '구' 또는 '시'로 끝나는 부분 찾기
    idx = 0
    while idx < len(parts):
        part = parts[idx]
        if part.endswith("구"):
            found_idx = idx
            break
        if part.endswith("시"):
            found_idx = idx
            break
        idx = idx + 1

    # 찾은 부분이 있으면 그 부분과 앞부분 결합
    if found_idx >= 0:
        gu_or_si = " ".join(parts[: found_idx + 1])

    return gu_or_si


def get_pre_promise_competition_rate(address: str) -> str:
    """
    주소로 청약 경쟁률을 조회합니다.

    이 도구는 공공데이터포털의 청약경쟁률 API를 사용하여
    입력한 주소의 '구' 또는 '시' 단위 지역 청약 경쟁률 정보를 반환합니다.

    데이터 출처: 공공데이터포털 (https://www.data.go.kr/)

    Args:
        address: 조회할 주소 (예: "경기도 의정부시 용현동")

    Returns:
        JSON 형식의 청약 경쟁률 정보 (주소, 공고일, 경쟁률)

    Examples:
        >>> get_pre_promise_competition_rate("경기도 의정부시 용현동")
    """
    # 주소에서 '구' 또는 '시' 단위 추출 (시도 포함)
    search_keyword = extract_gu_or_si(address)

    # 검색 키워드가 없으면 전체 주소 사용
    if search_keyword == "":
        search_keyword = address

    # 데이터 가져오기
    df_all = get_all_data()

    # 주소 검색: 추출한 지역이 포함된 주소만 찾기
    # 예: "경기도 양주시"가 포함된 주소만 찾기
    matched = df_all[df_all["주소"].str.contains(search_keyword, na=False)]

    # 최신순으로 정렬 (공고일 기준)
    matched_sorted = matched.sort_values("공고일", ascending=False)

    # DataFrame을 JSON 형식으로 변환
    result_dict = matched_sorted.to_dict(orient="records")

    return json.dumps(result_dict, ensure_ascii=False, indent=2)


# LangChain tool로 래핑
@tool
def get_pre_promise_competition_rate_tool(address: str) -> str:
    """
    주소로 청약 경쟁률을 조회합니다.

    이 도구는 공공데이터포털의 청약경쟁률 API를 사용하여
    입력한 주소의 '구' 또는 '시' 단위 지역 청약 경쟁률 정보를 반환합니다.

    데이터 출처: 공공데이터포털 (https://www.data.go.kr/)

    Args:
        address: 조회할 주소 (예: "경기도 의정부시 용현동")

    Returns:
        JSON 형식의 청약 경쟁률 정보 (주소, 공고일, 경쟁률)

    Examples:
        >>> get_pre_promise_competition_rate_tool("경기도 의정부시 용현동")
    """
    return get_pre_promise_competition_rate(address)


# 테스트용 코드
if __name__ == "__main__":
    result = get_pre_promise_competition_rate("인천")
    print(result)
