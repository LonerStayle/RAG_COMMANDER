import requests
import pandas as pd


url = "https://kosis.kr/openapi/Param/statisticsParameterData.do"
params = {
    "method": "getList",
    "apiKey": "MzlmNWY2OTczMzRmYmQ5NDQwZTIyNWU5YTVhNWIwZWQ=",
    "itmId": "13103114441T1",  # 거래건수만
    "objL1": "ALL",  # 전체 지역
    "format": "json",
    "jsonVD": "Y",
    "prdSe": "M",
    "startPrdDe": "202401",
    "endPrdDe": "202509",
    "orgId": "408",
    "tblId": "DT_408_2006_S0057",
}

headers = {"User-Agent": "Mozilla/5.0"}
response = requests.get(url, params=params, headers=headers)
data = response.json()
df = pd.DataFrame(data)
# 주요 컬럼
# PRD_DE: 기간 (예: 202507)
# C1_NM: 지역명 (예: 종로구, 강남구)
# ITM_NM: 항목명 (동(호)수, 면적)
# DT: 데이터 값
# ## 주요컬럼럼
# 'C1_NM'
# 'PRD_DE' = '날짜'
# 'UNIT_NM'='동(호)수'='거래량'


def get_trade_volume(address):
    """주소에서 구 단위 거래량 조회"""
    # 주소를 공백으로 나눠서 "구"로 끝나는 단어 찾기
    for word in address.split():
        if word.endswith("구"):
            district = word
            break

    # 해당 구가 포함된 데이터 필터링 (contains 사용)
    result = (
        df[df["C1_NM"].str.contains(district)]
        .pivot_table(
            index="PRD_DE",  # 행을 날짜로로
            columns="ITM_NM",  # 열을 항목명(ITM_NM)
            values="DT",  # 값을 DT로(거래량, 면적 숫자)
            aggfunc="first",  # 값이 여러개면 첫번째만만
        )
        .reset_index()
    )

    # 구 이름 추가
    result.insert(
        1, "행정구역", district
    )  # 1번째 위치(두번째 컬럼) 'C1_NM'을 '행정구역으로로'
    result.columns.name = None

    return result.rename(
        columns={"PRD_DE": "날짜", "동(호)수": "거래량", "면적": "면적(천㎡)"}
    )


# 사용 예시
# address = "서울 송파구 마천동 299-23"
# print(get_trade_volume(address))

# address = "서울 송파구 마천동 299-23"


# print(get_trade_volume(address))
