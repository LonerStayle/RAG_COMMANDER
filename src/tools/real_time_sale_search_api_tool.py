import requests
import xml.etree.ElementTree as ET
import json
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv("REAL_TIME_SALE_SEARCH_API_KEY")
KAKAO_API_KEY = os.getenv("KAKAO_REST_API_KEY")

# 주요 지역코드 매핑 (법정동 코드 5자리)
REGION_CODE_MAP = {
    # 서울특별시
    "종로구": "11110",
    "중구": "11140",
    "용산구": "11170",
    "성동구": "11200",
    "광진구": "11215",
    "동대문구": "11230",
    "중랑구": "11260",
    "성북구": "11290",
    "강북구": "11305",
    "도봉구": "11320",
    "노원구": "11350",
    "은평구": "11380",
    "서대문구": "11410",
    "마포구": "11440",
    "양천구": "11470",
    "강서구": "11500",
    "구로구": "11530",
    "금천구": "11545",
    "영등포구": "11560",
    "동작구": "11590",
    "관악구": "11620",
    "서초구": "11650",
    "강남구": "11680",
    "송파구": "11710",
    "강동구": "11740",
    # 부산광역시
    "중구": "26110",
    "서구": "26140",
    "동구": "26170",
    "영도구": "26200",
    "부산진구": "26230",
    "동래구": "26260",
    "남구": "26290",
    "북구": "26320",
    "해운대구": "26350",
    "사하구": "26380",
    "금정구": "26410",
    "강서구": "26440",
    "연제구": "26470",
    "수영구": "26500",
    "사상구": "26530",
    "기장군": "26710",
    # 인천광역시
    "중구": "28110",
    "동구": "28140",
    "미추홀구": "28177",
    "연수구": "28185",
    "남동구": "28200",
    "부평구": "28237",
    "계양구": "28245",
    "서구": "28260",
    "강화군": "28710",
    "옹진군": "28720",
    # 경기도 주요 지역
    "수원시": "41110",
    "성남시": "41130",
    "고양시": "41280",
    "용인시": "41460",
    "부천시": "41190",
    "안산시": "41270",
    "안양시": "41170",
    "평택시": "41220",
    "시흥시": "41390",
    "김포시": "41570",
    "의정부시": "41150",
    "광명시": "41210",
    "하남시": "41450",
    "오산시": "41370",
    "이천시": "41500",
    "구리시": "41310",
    "안성시": "41550",
    "포천시": "41650",
    "의왕시": "41430",
    "양주시": "41630",
    "여주시": "41670",
    "화성시": "41590",
    "광주시": "41610",
    "양평군": "41830",
    "가평군": "41820",
    "연천군": "41800",
    "동두천시": "41250",
    "과천시": "41290",
    "남양주시": "41360",
    "파주시": "41480",
    "수원시 영통구": "41113",
    "수원시 팔달구": "41111",
    "성남시 분당구": "41135",
    "용인시 기흥구": "41463",
    "용인시 수지구": "41461",
    "고양시 일산동구": "41281",
    "고양시 일산서구": "41285",
    "안산시 상록구": "41271",
    "안산시 단원구": "41273",
    "안양시 만안구": "41171",
    "안양시 동안구": "41173",
    "평택시 팽성읍": "41221",
    # 기타 주요 도시
    "대전광역시": "30000",
    "대구광역시": "27000",
    "광주광역시": "29000",
    "울산광역시": "31000",
    "세종특별자치시": "36000",
}


def get_building_name_from_road_address(road_address):
    """도로명 주소에서 건물명 추출"""
    building_name = road_address.get("building_name", "")
    has_building_name = building_name and building_name.strip()
    return building_name.strip() if has_building_name else None


def get_building_name_from_address_info(address_info):
    """지번 주소에서 건물명 추출"""
    building_name = address_info.get("building_name", "")
    has_building_name = building_name and building_name.strip()
    return building_name.strip() if has_building_name else None


def get_building_name_from_address_string(address_string):
    """주소 문자열에서 건물명 추출 시도"""
    parts = address_string.split()
    has_enough_parts = len(parts) >= 2
    if not has_enough_parts:
        return None

    last_part = parts[-1]
    is_valid_building_name = not last_part.isdigit() and len(last_part) > 1
    return last_part if is_valid_building_name else None


def check_apartment_category(category_name, place_name):
    """아파트 관련 카테고리인지 확인"""
    is_apartment = "아파트" in category_name or "아파트" in place_name
    return is_apartment


def check_building_category(category_name, place_name):
    """건물 관련 카테고리인지 확인"""
    has_place_name = place_name
    is_building = "건물" in category_name or "공동주택" in category_name
    return has_place_name and is_building


def extract_apartment_name_from_kakao(address: str) -> Optional[str]:
    """
    카카오 API를 사용하여 주소에서 아파트명을 추출합니다.
    도로명 주소와 구주소 둘 다 처리합니다.

    Args:
        address: 주소 문자열 (예: "서울 강남구 언주로 711", "서울시 강남구 역삼동 123-45")

    Returns:
        아파트명 또는 None
    """
    no_api_key = not KAKAO_API_KEY
    if no_api_key:
        return None

    try:
        headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}

        # 방법 1: 주소 검색 API로 도로명 주소와 구주소 모두 처리
        url_address = "https://dapi.kakao.com/v2/local/search/address.json"
        params_address = {"query": address, "size": 5}

        response_address = requests.get(
            url_address, headers=headers, params=params_address, timeout=5
        )

        is_success = response_address.status_code == 200
        if not is_success:
            return None

        data_address = response_address.json()
        documents_address = data_address.get("documents", [])

        has_documents = len(documents_address) > 0
        if not has_documents:
            return None

        # 첫 번째 문서에서 건물명 추출 시도
        first_doc = documents_address[0]
        road_address = first_doc.get("road_address", {})
        address_info = first_doc.get("address", {})

        # 도로명 주소에서 건물명 추출
        building_name = get_building_name_from_road_address(road_address)
        if building_name:
            return building_name

        # 지번 주소에서 건물명 추출
        building_name = get_building_name_from_address_info(address_info)
        if building_name:
            return building_name

        # 주소 문자열에서 건물명 추출 시도
        road_address_name = first_doc.get("road_address_name", "")
        address_name = first_doc.get("address_name", "")

        building_name = get_building_name_from_address_string(road_address_name)
        if building_name:
            return building_name

        building_name = get_building_name_from_address_string(address_name)
        if building_name:
            return building_name

        # 방법 2: 키워드 검색 API 사용
        url_keyword = "https://dapi.kakao.com/v2/local/search/keyword.json"
        params_keyword = {"query": address, "size": 5}

        response_keyword = requests.get(
            url_keyword, headers=headers, params=params_keyword, timeout=5
        )

        is_keyword_success = response_keyword.status_code == 200
        if not is_keyword_success:
            return None

        data_keyword = response_keyword.json()
        documents_keyword = data_keyword.get("documents", [])

        has_keyword_documents = len(documents_keyword) > 0
        if not has_keyword_documents:
            return None

        # 첫 번째 문서 확인
        first_keyword_doc = documents_keyword[0]
        place_name = first_keyword_doc.get("place_name", "")
        category_name = first_keyword_doc.get("category_name", "")

        # 아파트 관련 카테고리인 경우
        is_apartment = check_apartment_category(category_name, place_name)
        if is_apartment:
            return place_name

        # 건물 관련 카테고리인 경우
        is_building = check_building_category(category_name, place_name)
        if is_building:
            return place_name

        # 방법 3: 좌표 기반 검색
        x = first_doc.get("x")
        y = first_doc.get("y")

        has_coordinates = x and y
        if not has_coordinates:
            return None

        params_nearby = {
            "query": address,
            "x": x,
            "y": y,
            "radius": 50,
            "size": 3,
        }

        response_nearby = requests.get(
            url_keyword, headers=headers, params=params_nearby, timeout=5
        )

        is_nearby_success = response_nearby.status_code == 200
        if not is_nearby_success:
            return None

        data_nearby = response_nearby.json()
        docs_nearby = data_nearby.get("documents", [])

        has_nearby_docs = len(docs_nearby) > 0
        if not has_nearby_docs:
            return None

        # 첫 번째 문서 확인
        first_nearby_doc = docs_nearby[0]
        nearby_place_name = first_nearby_doc.get("place_name", "")
        nearby_category_name = first_nearby_doc.get("category_name", "")

        is_nearby_apartment = check_apartment_category(
            nearby_category_name, nearby_place_name
        )
        if is_nearby_apartment:
            return nearby_place_name

        is_nearby_building = check_building_category(
            nearby_category_name, nearby_place_name
        )
        if is_nearby_building:
            return nearby_place_name

        return None

    except Exception as e:
        print(f"[DEBUG] 카카오 API 아파트명 추출 실패: {str(e)}")
        return None


def extract_apartment_name_from_address(address: str) -> Optional[str]:
    """
    주소 문자열에서 아파트명을 추출합니다.
    도로명 주소와 구주소 둘 다 처리합니다.

    Args:
        address: 주소 문자열 (예: "서울 강남구 언주로 711", "서울시 강남구 역삼동 123-45")

    Returns:
        추출된 아파트명 또는 None
    """
    # 카카오 API로 먼저 시도
    apartment_name = extract_apartment_name_from_kakao(address)
    has_apartment_name = apartment_name is not None
    if has_apartment_name:
        return apartment_name

    # 카카오 API 실패 시, 주소에서 직접 추출 시도
    # 주소를 공백으로 분리
    parts = address.split()

    # 일반적인 아파트명 패턴 찾기
    apartment_keywords = [
        "래미안",
        "힐스테이트",
        "자이",
        "엘지",
        "삼성",
        "대우",
        "아파트",
    ]

    # 각 키워드 확인
    keyword_found = None
    for keyword in apartment_keywords:
        keyword_in_address = keyword in address
        if keyword_in_address:
            keyword_found = keyword
            break

    if keyword_found:
        keyword_index = address.find(keyword_found)
        start = max(0, keyword_index - 20)
        end = min(len(address), keyword_index + len(keyword_found) + 20)
        context = address[start:end]
        context_parts = context.split()

        # 키워드 포함 부분 추출
        for part in context_parts:
            has_keyword = keyword_found in part
            is_long_enough = len(part) > 2
            if has_keyword and is_long_enough:
                return part

    return None


def extract_region_code(address: str) -> Optional[str]:
    """
    주소에서 지역코드를 추출합니다.

    Args:
        address: 주소 문자열 (예: "서울시 강남구", "강남구", "서울특별시 강남구 역삼동")

    Returns:
        지역코드 (5자리 문자열) 또는 None
    """
    # 주소에서 구/시/군 추출
    region_found = None
    for region_name, code in REGION_CODE_MAP.items():
        region_in_address = region_name in address
        if region_in_address:
            region_found = code
            break

    if region_found:
        return region_found

    # "서울"이 포함된 경우 강남구로 기본값
    has_seoul = "서울" in address
    if has_seoul:
        return "11680"  # 강남구

    return None


def extract_xml_text(element, default="N/A"):
    """XML 요소에서 텍스트 추출"""
    no_element = element is None
    if no_element:
        return default

    no_text = element.text is None
    if no_text:
        return default

    return element.text.strip()


def clean_apartment_name(apartment_name):
    """아파트명 정리 (번지, 쉼표 등 제거)"""
    cleaned = apartment_name.strip()

    # 쉼표 제거
    has_comma = "," in cleaned
    if has_comma:
        parts = cleaned.split(",")
        has_multiple_parts = len(parts) > 1
        if has_multiple_parts:
            cleaned = parts[-1].strip()
        else:
            first_part = parts[0].strip()
            is_only_digit = first_part.replace(",", "").isdigit()
            if is_only_digit:
                cleaned = ""

    # 번지 패턴 제거
    cleaned_parts = cleaned.split()
    filtered_parts = []

    for part in cleaned_parts:
        is_digit_only = part.replace(",", "").replace("-", "").isdigit()
        starts_with_digit = len(part) > 0 and part[0].isdigit() and len(part) <= 5
        is_jibun = is_digit_only or starts_with_digit

        if not is_jibun:
            filtered_parts.append(part)

    has_filtered_parts = len(filtered_parts) > 0
    if has_filtered_parts:
        cleaned = " ".join(filtered_parts)
    else:
        cleaned = apartment_name

    return cleaned


def match_apartment_name(cleaned_name, actual_name):
    """아파트명이 일치하는지 확인"""
    # 정확히 포함되는지 확인
    exact_match = cleaned_name in actual_name
    if exact_match:
        return True

    # 주요 키워드 추출
    keywords = cleaned_name.replace("아파트", "").replace(" ", "").strip()

    # 공백 제거한 이름으로 확인
    actual_no_space = actual_name.replace(" ", "")
    keyword_match = keywords in actual_no_space
    if keyword_match:
        return True

    return False


def parse_xml_response(
    xml_text: str, apartment_name: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    XML 응답을 파싱하여 실거래가 정보를 추출합니다.

    Args:
        xml_text: XML 형식의 응답 텍스트
        apartment_name: 필터링할 아파트명 (None이면 전체)

    Returns:
        실거래가 정보 리스트
    """
    try:
        root = ET.fromstring(xml_text)
        results = []

        # resultCode 확인
        result_code = root.find(".//resultCode")
        has_result_code = result_code is not None
        if has_result_code:
            code_text = result_code.text.strip()
            is_error = code_text not in ["00", "000"]
            if is_error:
                result_msg = root.find(".//resultMsg")
                error_msg = extract_xml_text(result_msg, "알 수 없는 오류")
                return [{"error": f"API 오류: {error_msg}"}]

        # item 요소 찾기
        items = root.findall(".//item")

        has_no_items = len(items) == 0
        if has_no_items:
            return []

        # 각 항목 처리
        for item in items:
            apt_name = item.find("aptNm")
            no_apt_name = apt_name is None or apt_name.text is None
            if no_apt_name:
                continue

            apt_name_text = apt_name.text.strip()

            # 아파트명 필터링
            has_filter = apartment_name is not None
            if has_filter:
                cleaned_apartment_name = clean_apartment_name(apartment_name)
                is_matched = match_apartment_name(cleaned_apartment_name, apt_name_text)

                if not is_matched:
                    print(
                        f"[DEBUG] 아파트명 불일치 - 추출: '{cleaned_apartment_name}', 실제: '{apt_name_text}'"
                    )
                    continue

                print(
                    f"[DEBUG] 아파트명 매칭 성공 - 추출: '{cleaned_apartment_name}', 실제: '{apt_name_text}'"
                )

            # 거래금액 추출
            deal_amount = item.find("dealAmount")
            deal_amount_text = extract_xml_text(deal_amount, "N/A")
            deal_amount_text = deal_amount_text.replace(",", "").replace(" ", "")

            # 건축년도
            build_year = item.find("buildYear")
            build_year_text = extract_xml_text(build_year, "N/A")

            # 거래일자
            deal_year = item.find("dealYear")
            deal_month = item.find("dealMonth")
            deal_day = item.find("dealDay")
            year_text = extract_xml_text(deal_year, "N/A")
            month_text = extract_xml_text(deal_month, "N/A")
            day_text = extract_xml_text(deal_day, "N/A")
            deal_date = f"{year_text}-{month_text}-{day_text}"

            # 전용면적
            area = item.find("excluUseAr")
            area_text = extract_xml_text(area, "N/A")

            # 층
            floor = item.find("flr")
            floor_text = extract_xml_text(floor, "N/A")

            # 지번
            jibun = item.find("jibun")
            jibun_text = extract_xml_text(jibun, "N/A")

            # 도로명
            road_name = item.find("roadName")
            road_name_text = extract_xml_text(road_name, "N/A")

            # 평당 가격 계산
            price_per_pyeong = "N/A"
            is_valid_amount = deal_amount_text != "N/A"
            is_valid_area = area_text != "N/A"

            if is_valid_amount and is_valid_area:
                try:
                    deal_amount_num = float(deal_amount_text.replace(",", ""))
                    area_num = float(area_text.replace(",", ""))
                    is_valid_area_size = area_num > 0

                    if is_valid_area_size:
                        pyeong_price = deal_amount_num / (area_num / 3.3)
                        price_per_pyeong = f"{pyeong_price:.1f}"
                except (ValueError, ZeroDivisionError):
                    pass

            results.append(
                {
                    "아파트명": apt_name_text,
                    "거래금액": deal_amount_text,
                    "거래일자": deal_date,
                    "전용면적": area_text,
                    "평당가격": price_per_pyeong,
                    "층": floor_text,
                    "건축년도": build_year_text,
                    "지번": jibun_text,
                    "도로명": road_name_text,
                }
            )

        return results

    except ET.ParseError as e:
        return [{"error": f"XML 파싱 오류: {str(e)}"}]
    except Exception as e:
        return [{"error": f"처리 오류: {str(e)}"}]


def get_real_estate_price(
    address_or_apartment: str,
    api_key: Optional[str] = None,
    lawd_cd: Optional[str] = None,
    deal_ymd: Optional[str] = None,
    apartment_name: Optional[str] = None,
) -> str:
    """
    공공데이터포털 API를 사용한 아파트 매매 실거래가 조회

    주소나 아파트명을 입력하면 해당 지역의 실거래가를 조회합니다.
    아파트명이 포함된 경우 해당 아파트만 필터링합니다.

    Args:
        address_or_apartment: 조회할 주소 또는 아파트명
                              (예: "서울시 강남구", "강남구", "래미안 강남파크", "서울시 강남구 래미안 강남파크")
        api_key: 공공데이터포털에서 발급받은 API 키 (Decoding 버전 사용). None이면 .env의 REAL_TIME_SALE_SEARCH_API_KEY 사용
        lawd_cd: 지역코드 (5자리, 예: "11680" = 강남구). None이면 address에서 추출 시도
        deal_ymd: 조회 월 (YYYYMM 형식, 예: "202412"). None이면 최근 5년 중 가장 최신 거래 조회
        apartment_name: 아파트명 (예: "래미안"). None이면 address_or_apartment에서 추출 시도

    Returns:
        JSON 형식의 실거래가 정보 문자열
    """
    # API 키 설정
    no_api_key_param = api_key is None
    if no_api_key_param:
        api_key = API_KEY

    no_api_key = api_key is None
    if no_api_key:
        return json.dumps(
            {
                "status": "error",
                "error": "API 키가 설정되지 않았습니다.",
                "tip": ".env 파일에 REAL_TIME_SALE_SEARCH_API_KEY를 설정하거나 api_key 파라미터를 제공해주세요.",
            },
            ensure_ascii=False,
            indent=2,
        )

    # 공공데이터포털 End Point
    url = "https://apis.data.go.kr/1613000/RTMSDataSvcAptTrade/getRTMSDataSvcAptTrade"

    # 지역코드 추출
    no_lawd_cd = lawd_cd is None
    if no_lawd_cd:
        lawd_cd = extract_region_code(address_or_apartment)

    no_lawd_cd_extracted = lawd_cd is None
    if no_lawd_cd_extracted:
        return json.dumps(
            {
                "status": "error",
                "error": f"주소에서 지역코드를 추출할 수 없습니다: {address_or_apartment}",
                "tip": "지역명을 명확히 입력해주세요 (예: '서울시 강남구', '부산 해운대구')",
            },
            ensure_ascii=False,
            indent=2,
        )

    # 아파트명 추출
    no_apartment_name_param = apartment_name is None
    if no_apartment_name_param:
        has_address_info = "시" in address_or_apartment or "구" in address_or_apartment
        is_only_apartment_name = not has_address_info

        if is_only_apartment_name:
            apartment_name = address_or_apartment
        else:
            apartment_name = extract_apartment_name_from_address(address_or_apartment)
            has_extracted_name = apartment_name is not None
            if has_extracted_name:
                print(f"[DEBUG] 주소에서 추출한 아파트명: {apartment_name}")

    # 가장 최신 거래 찾기 (최근 5년까지 조회)
    try:
        from datetime import datetime, timedelta

        now = datetime.now()
        latest_transaction = None

        # 최근 5년까지 역순으로 조회하여 가장 최신 거래 찾기
        for i in range(60):
            month_date = now - timedelta(days=30 * i)
            month_str = month_date.strftime("%Y%m")

            params = {
                "serviceKey": api_key,
                "LAWD_CD": lawd_cd,
                "DEAL_YMD": month_str,
                "numOfRows": "100",
                "pageNo": "1",
            }

            response = requests.get(url, params=params, timeout=10)

            is_success = response.status_code == 200
            if not is_success:
                is_first_call = i == 0
                if is_first_call:
                    print(
                        f"[DEBUG] HTTP 오류: {response.status_code}, 응답: {response.text[:200]}"
                    )
                continue

            response_text = response.text

            # 첫 번째 호출 시 응답 확인
            is_first_call = i == 0
            if is_first_call:
                print(f"[DEBUG] API 응답 샘플 (처음 500자): {response_text[:500]}")
                try:
                    root = ET.fromstring(response_text)
                    result_code = root.find(".//resultCode")
                    result_msg = root.find(".//resultMsg")
                    has_result_code = result_code is not None
                    if has_result_code:
                        print(f"[DEBUG] resultCode: {result_code.text}")
                    has_result_msg = result_msg is not None
                    if has_result_msg:
                        print(f"[DEBUG] resultMsg: {result_msg.text}")
                except:
                    pass

            # XML 파싱
            parsed_data = parse_xml_response(response_text, apartment_name)

            # 에러 확인
            has_data = parsed_data and len(parsed_data) > 0
            has_error = has_data and "error" in parsed_data[0]

            if has_error:
                if is_first_call:
                    print(f"[DEBUG] 파싱 오류: {parsed_data[0].get('error')}")
                continue

            # 데이터가 있는 경우
            if has_data:
                # 거래일자로 정렬하여 가장 최신 것 선택
                sorted_data = sorted(
                    parsed_data, key=lambda x: x.get("거래일자", ""), reverse=True
                )
                latest_transaction = sorted_data[0]
                print(
                    f"[DEBUG] {month_str}월에서 {len(parsed_data)}건의 거래 발견, 최신 거래 선택"
                )

                has_apartment_name = apartment_name is not None
                if has_apartment_name:
                    print(
                        f"[DEBUG] 매칭된 아파트: {latest_transaction.get('아파트명', 'N/A')}"
                    )
                break  # 최신 거래를 찾았으므로 중단

            elif is_first_call and apartment_name:
                print(
                    f"[DEBUG] {month_str}월에서 아파트명 '{apartment_name}'에 대한 거래 데이터 없음"
                )

    except Exception as e:
        return json.dumps(
            {"status": "error", "error": str(e)}, ensure_ascii=False, indent=2
        )

    no_transaction = latest_transaction is None
    if no_transaction:
        return json.dumps(
            {
                "status": "no_data",
                "message": f"'{address_or_apartment}'에 대한 최근 실거래가 데이터를 찾을 수 없습니다.",
                "tip": "최근 5년간 거래 내역이 없거나, 다른 지역명이나 아파트명으로 시도해보세요.",
            },
            ensure_ascii=False,
            indent=2,
        )

    result = {
        "status": "success",
        "address": address_or_apartment,
        "apartment_name": apartment_name,
        "region_code": lawd_cd,
        "latest_transaction": latest_transaction,
    }

    return json.dumps(result, ensure_ascii=False, indent=2)


# 사용 예시
if __name__ == "__main__":
    result_json = get_real_estate_price("서울시 강남구 도곡동 527 도곡렉슬")
    print(result_json)


# from src.tools.real_time_sale_search_api_tool import get_real_estate_price
# import json

# # 주소만 입력하면 됩니다
# result_json = get_real_estate_price("서울시 강남구")
# result = json.loads(result_json)

