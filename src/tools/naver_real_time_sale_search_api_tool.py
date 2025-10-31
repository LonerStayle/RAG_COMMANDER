import requests
import time
import json
import re
import math
import random
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
import os

load_dotenv()

KAKAO_API_KEY = os.getenv("KAKAO_REST_API_KEY")

# 네이버 부동산 API 엔드포인트 (비공식 API, 모바일 웹에서 사용하는 엔드포인트)
# 참고: 네이버 부동산의 공식 API가 아닌 모바일 웹의 XHR 엔드포인트를 사용합니다.
# 이용약관을 준수해야 하며, 과도한 요청은 차단될 수 있습니다.
NAVER_CLUSTER_LIST = (
    "https://m.land.naver.com/cluster/clusterList"  # 클러스터(그룹) 조회
)
NAVER_ARTICLE_LIST = (
    "https://m.land.naver.com/cluster/ajax/articleList"  # 매물 상세 조회
)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


def price_to_manwon(price_str: Optional[str]) -> Optional[float]:
    """
    네이버 priceString을 만원 단위 숫자로 변환.
    예: '12억 3,000' -> 123000, '3,500' -> 3500, '전세 6억' -> 60000
    """
    if not price_str:
        return None

    text = re.sub(r"[^\d억만천백십 ]", "", str(price_str))
    eok = 0
    man = 0

    eok_match = re.search(r"(\d+)\s*억", text)
    if eok_match:
        eok = int(eok_match.group(1))

    man_match = re.search(r"(\d+)\s*만", text)
    if man_match:
        man = int(man_match.group(1))

    if "억" not in text and "만" not in text:
        digits = re.sub(r"\D", "", text)
        if digits:
            man = int(digits)

    return eok * 10000 + man


def normalize_article_response(js: Any) -> List[Dict[str, Any]]:
    """articleList 응답을 정규화"""
    if isinstance(js, list):
        return js
    if isinstance(js, dict):
        body = js.get("body")
        if isinstance(body, list):
            return body
        if isinstance(body, dict):
            arr = body.get("articles") or body.get("list")
            if isinstance(arr, list):
                return arr
        arr = js.get("articles")
        if isinstance(arr, list):
            return arr
    return []


def calculate_price_per_pyeong(
    price_manwon: Optional[float], area_m2: Optional[float]
) -> Optional[float]:
    """
    평당 가격 계산 (만원/평)
    1평 = 3.3㎡
    """
    if not price_manwon or not area_m2 or area_m2 <= 0:
        return None

    pyeong = area_m2 / 3.3
    if pyeong <= 0:
        return None

    return round(price_manwon / pyeong, 2)


def get_naver_land_price(address: str) -> str:
    """
    네이버 부동산에서 특정 주소(아파트명 포함)의 매매가격과 평당가격 조회

    Args:
        address: 아파트명을 포함한 주소 (예: "서울시 강남구 래미안 강남파크", "강남구 역삼동 래미안")

    Returns:
        JSON 형식의 가격 정보 문자열 (ensure_ascii=False, indent=2)

    반환 형식 예시:
    {
      "status": "success",
      "address": "서울시 강남구 래미안 강남파크",
      "아파트명": "래미안 강남파크",
      "매물수": 5,
      "정확일치_매물수": 3,
      "평균_평당가격_만원": 8500.5,
      "매물목록": [
        {
          "아파트명": "래미안 강남파크",
          "주소": "서울시 강남구 역삼동",
          "가격": "12억 5,000",
          "가격_만원": 125000,
          "전용면적_㎡": 84.98,
          "평당가격_만원": 8500.5,
          "층": "15층"
        }
      ]
    }
    """
    if not KAKAO_API_KEY:
        return json.dumps(
            {
                "status": "error",
                "error": "KAKAO_REST_API_KEY가 설정되지 않았습니다.",
                "tip": ".env 파일에 KAKAO_REST_API_KEY를 설정해주세요.",
            },
            ensure_ascii=False,
            indent=2,
        )

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://m.land.naver.com/",
    }

    session = requests.Session()
    session.headers.update(headers)

    try:
        # 아파트명 추출 (주소에서 추출 시도)
        # 주소에서 아파트명 관련 키워드 찾기
        apartment_name = None
        address_clean = address

        # 쉼표로 구분된 경우 처리
        if "," in address:
            parts = [p.strip() for p in address.split(",")]
            address_clean = parts[0]  # 주소 부분만 사용
            if len(parts) > 1:
                apartment_name = parts[1]  # 아파트명 부분

        # 주소 패턴 확인 (시/구/동 등이 포함되어 있는지)
        has_address_pattern = any(
            keyword in address_clean
            for keyword in ["시", "구", "동", "로", "길", "번지"]
        )

        # 주소 패턴이 없으면 아파트명만 입력된 것으로 간주
        if not has_address_pattern and not apartment_name:
            apartment_name = address_clean
            address_clean = None
        elif not apartment_name and has_address_pattern:
            # 주소에서 아파트명 추출 시도 (래미안, 힐스테이트, 팰리스 등)
            address_parts = address_clean.split()
            # 마지막 1-2개 단어가 아파트명일 가능성
            for i in range(len(address_parts) - 1, max(0, len(address_parts) - 3), -1):
                part = address_parts[i]
                # 숫자만 있는 경우 제외
                if not part.isdigit() and len(part) > 1:
                    apartment_name = " ".join(address_parts[i:])
                    address_clean = " ".join(address_parts[:i])
                    break

        # 1단계: 주소를 좌표로 변환 (카카오 API 사용)
        kakao_url = "https://dapi.kakao.com/v2/local/search/address.json"
        kakao_keyword_url = "https://dapi.kakao.com/v2/local/search/keyword.json"
        kakao_headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}

        # 주소가 없고 아파트명만 있는 경우 처리
        if not address_clean or (apartment_name and address_clean == apartment_name):
            # 아파트명으로 직접 검색 시도 (여러 지역 포함)
            search_query = address if not address_clean else apartment_name

            # 아파트명에 지역 정보가 없으면 서울 추가
            if (
                apartment_name
                and "서울" not in search_query
                and "경기" not in search_query
            ):
                search_query = f"서울 {search_query}"

            keyword_params = {"query": search_query, "size": 15}  # 더 많은 결과 조회
            keyword_response = session.get(
                kakao_keyword_url,
                headers=kakao_headers,
                params=keyword_params,
                timeout=10,
            )
            keyword_data = keyword_response.json()

            if keyword_data.get("documents"):
                # 아파트명이 정확히 일치하는 결과 찾기
                best_match = None
                best_score = 0

                for doc in keyword_data["documents"]:
                    place_name = doc.get("place_name", "")
                    address_name = doc.get("road_address_name") or doc.get(
                        "address_name", ""
                    )

                    # 점수 계산
                    score = 0
                    if apartment_name:
                        apartment_keywords = apartment_name.split()
                        # 정확히 일치하는 경우
                        if apartment_name in place_name or place_name in apartment_name:
                            score += 100
                        # 키워드 매칭
                        for keyword in apartment_keywords:
                            if len(keyword) > 1 and keyword in place_name:
                                score += 20

                        # 서울 지역 우선 (아파트는 대부분 서울/경기)
                        if "서울" in address_name or "서울" in place_name:
                            score += 10
                        if "강남" in address_name or "강남" in place_name:
                            score += 5
                        if "대치" in address_name or "대치" in place_name:
                            score += 5

                    if score > best_score:
                        best_score = score
                        best_match = doc

                if best_match:
                    lat = float(best_match["y"])
                    lng = float(best_match["x"])
                    road_address = best_match.get(
                        "road_address_name"
                    ) or best_match.get("address_name", "")
                    if road_address:
                        address_clean = road_address
                else:
                    # 매칭되는 것이 없으면 첫 번째 결과 사용
                    lat = float(keyword_data["documents"][0]["y"])
                    lng = float(keyword_data["documents"][0]["x"])
                    road_address = keyword_data["documents"][0].get(
                        "road_address_name"
                    ) or keyword_data["documents"][0].get("address_name", "")
                    if road_address:
                        address_clean = road_address
        else:
            # 주소가 있는 경우: 여러 방식으로 주소 검색 시도
            search_queries = [address_clean]

            # 키워드 검색도 시도
            if apartment_name:
                # 주소 + 동명으로 검색
                if "동" in address_clean:
                    search_queries.append(address_clean.split("동")[0] + "동")

            lat = None
            lng = None

            for query in search_queries:
                kakao_params = {"query": query}
                coord_response = session.get(
                    kakao_url, headers=kakao_headers, params=kakao_params, timeout=10
                )
                coord_data = coord_response.json()

                if coord_data.get("documents"):
                    lat = float(coord_data["documents"][0]["y"])
                    lng = float(coord_data["documents"][0]["x"])
                    break

            if lat is None or lng is None:
                # 키워드 검색으로 시도
                keyword_params = {"query": address_clean}
                keyword_response = session.get(
                    kakao_keyword_url,
                    headers=kakao_headers,
                    params=keyword_params,
                    timeout=10,
                )
                keyword_data = keyword_response.json()

                if keyword_data.get("documents"):
                    lat = float(keyword_data["documents"][0]["y"])
                    lng = float(keyword_data["documents"][0]["x"])

        if lat is None or lng is None:
            return json.dumps(
                {
                    "status": "error",
                    "error": f"주소를 찾을 수 없습니다: {address}",
                    "tip": "주소 형식을 확인해주세요 (예: '서울시 강남구 대치동' 또는 '서울 강남구 대치동 633, 래미안 대치팰리스')",
                },
                ensure_ascii=False,
                indent=2,
            )

        time.sleep(random.uniform(0.8, 1.2))

        # 2단계: 네이버 부동산에서 클러스터(그룹) 조회
        # 여러 줌 레벨로 시도 (범위를 넓혀서 더 많은 매물 찾기)
        # 참고: 네이버 부동산 API는 좌표 기반 검색이므로 다양한 줌 레벨로 시도
        # 줌 레벨이 낮을수록 넓은 범위, 높을수록 좁은 범위
        cluster_params_list = [
            {
                "view": "atcl",
                "rletTpCd": "APT",  # 아파트
                "tradTpCd": "A1",  # 매매
                "z": "12",  # 매우 넓은 범위
                "lat": str(lat),
                "lon": str(lng),
            },
            {
                "view": "atcl",
                "rletTpCd": "APT",
                "tradTpCd": "A1",
                "z": "13",  # 넓은 범위
                "lat": str(lat),
                "lon": str(lng),
            },
            {
                "view": "atcl",
                "rletTpCd": "APT",
                "tradTpCd": "A1",
                "z": "14",
                "lat": str(lat),
                "lon": str(lng),
            },
            {
                "view": "atcl",
                "rletTpCd": "APT",
                "tradTpCd": "A1",
                "z": "15",
                "lat": str(lat),
                "lon": str(lng),
            },
            {
                "view": "atcl",
                "rletTpCd": "APT",
                "tradTpCd": "A1",
                "z": "16",
                "lat": str(lat),
                "lon": str(lng),
            },
        ]

        groups = []
        cluster_response_data = None
        for cluster_params in cluster_params_list:
            cluster_response = session.get(
                NAVER_CLUSTER_LIST, params=cluster_params, timeout=20
            )
            cluster_response.raise_for_status()
            cluster_data = cluster_response.json()
            cluster_response_data = cluster_data  # 디버깅용

            # 응답 구조 확인: data.ARTICLE 또는 다른 경로
            found_groups = []
            if "data" in cluster_data:
                data = cluster_data["data"]
                if isinstance(data, dict):
                    # ARTICLE 키 확인 (대소문자 구분)
                    found_groups = (
                        data.get("ARTICLE")
                        or data.get("article")
                        or data.get("Article")
                        or []
                    )
                    # data가 비어있지 않은 경우 다른 키들 확인
                    if not found_groups and data:
                        # data 내부의 다른 키들 확인
                        for key in data.keys():
                            if isinstance(data[key], list) and len(data[key]) > 0:
                                found_groups = data[key]
                                break
                elif isinstance(data, list):
                    found_groups = data
            elif isinstance(cluster_data, list):
                found_groups = cluster_data

            if found_groups:
                groups.extend(found_groups)
                time.sleep(random.uniform(0.5, 1.0))  # API 호출 간 지연
                if len(groups) >= 5:  # 충분한 그룹을 찾으면 중단
                    break
            else:
                # data가 비어있으면 다음 줌 레벨 시도
                time.sleep(random.uniform(0.3, 0.6))
                continue

        # 중복 제거 (lgeo 기준)
        seen_lgeo = set()
        unique_groups = []
        for group in groups:
            lgeo = group.get("lgeo")
            if lgeo and lgeo not in seen_lgeo:
                seen_lgeo.add(lgeo)
                unique_groups.append(group)
        groups = unique_groups

        if not groups:
            # 디버깅: 실제 응답 구조 확인
            debug_info = {
                "lat": lat,
                "lng": lng,
                "cluster_response": "success",
                "groups_count": 0,
                "apartment_name": apartment_name,
                "address_clean": address_clean,
            }

            # 응답 구조 확인 (디버깅용)
            if cluster_response_data:
                debug_info["response_keys"] = (
                    list(cluster_response_data.keys())
                    if isinstance(cluster_response_data, dict)
                    else "not_dict"
                )
                debug_info["response_sample"] = str(cluster_response_data)[
                    :500
                ]  # 처음 500자만

            return json.dumps(
                {
                    "status": "no_data",
                    "message": f"'{address}' 주변에 매물이 없습니다.",
                    "debug": debug_info,
                },
                ensure_ascii=False,
                indent=2,
            )

        time.sleep(random.uniform(0.8, 1.2))

        # 3단계: 각 그룹에서 매물 조회
        all_articles = []
        for group in groups[:3]:  # 최대 3개 그룹만 조회
            lgeo = group.get("lgeo")
            count = int(group.get("count", 0))

            if not lgeo or count <= 0:
                continue

            z = group.get("z")
            lat_group = group.get("lat")
            lon_group = group.get("lon")

            pages = max(1, math.ceil(count / 20))

            for page in range(1, min(pages + 1, 3)):  # 최대 3페이지까지
                article_params = {
                    "itemId": lgeo,
                    "lgeo": lgeo,
                    "totCnt": str(count),
                    "z": str(z),
                    "lat": str(lat_group),
                    "lon": str(lon_group),
                    "rletTpCd": "APT",
                    "tradTpCd": "A1",
                    "page": str(page),
                    "showR0": "",
                }

                article_response = session.get(
                    NAVER_ARTICLE_LIST, params=article_params, timeout=20
                )
                article_response.raise_for_status()
                articles = normalize_article_response(article_response.json())

                all_articles.extend(articles)
                time.sleep(random.uniform(0.8, 1.2))

        # 디버깅: 조회된 매물 수 확인
        if not all_articles:
            return json.dumps(
                {
                    "status": "no_data",
                    "message": f"'{address}' 주변에 매물을 조회할 수 없습니다.",
                    "debug": {
                        "lat": lat,
                        "lng": lng,
                        "groups_count": len(groups),
                        "articles_count": 0,
                        "apartment_name": apartment_name,
                    },
                },
                ensure_ascii=False,
                indent=2,
            )

        # 4단계: 아파트명으로 필터링 및 평당 가격 계산
        matched_articles = []
        exact_matches = []  # 정확히 일치하는 매물
        partial_matches = []  # 부분 일치하는 매물

        for article in all_articles:
            # 아파트명 확인
            apt_name = article.get("atclNm") or article.get("articleName") or ""

            # 아파트명이 주소에 포함되어 있는지 확인
            # 아파트명이 있으면 필터링, 없으면 모두 포함
            if apartment_name:
                # 아파트명의 주요 키워드 추출 (래미안, 팰리스 등)
                apartment_keywords = [k for k in apartment_name.split() if len(k) > 1]

                # 아파트명 매칭 점수 계산
                match_score = 0
                exact_match = False

                # 정확히 일치하는 경우
                if apartment_name in apt_name or apt_name in apartment_name:
                    exact_match = True
                    match_score = 100
                elif apartment_keywords:
                    # 키워드 기반 매칭
                    matched_keywords = 0
                    for keyword in apartment_keywords:
                        if keyword in apt_name:
                            matched_keywords += 1

                    if matched_keywords > 0:
                        match_score = (matched_keywords / len(apartment_keywords)) * 100
                    else:
                        continue  # 매칭되지 않으면 제외
                else:
                    # 아파트명이 너무 짧거나 의미없는 경우, 모두 포함
                    match_score = 50
                    exact_match = False
            else:
                # 아파트명이 없으면 모두 포함
                match_score = 0
                exact_match = False

            # 가격 정보
            price_str = article.get("prc") or article.get("priceString")
            price_manwon = price_to_manwon(price_str)

            # 면적 정보 (전용면적)
            area_m2 = article.get("spc2") or article.get("area2")
            if area_m2:
                try:
                    area_m2 = float(str(area_m2).replace(",", ""))
                except:
                    area_m2 = None
            else:
                area_m2 = None

            # 평당 가격 계산
            price_per_pyeong = calculate_price_per_pyeong(price_manwon, area_m2)

            article_data = {
                "아파트명": apt_name,
                "주소": article.get("addr")
                or article.get("roadAddress")
                or article.get("address"),
                "가격": price_str,
                "가격_만원": price_manwon,
                "전용면적_㎡": area_m2,
                "평당가격_만원": price_per_pyeong,
                "층": article.get("flrInfo") or article.get("floorInfo"),
                "매칭점수": match_score,
            }

            # 정확히 일치하는 것과 부분 일치하는 것을 분리
            if exact_match:
                exact_matches.append(article_data)
            else:
                partial_matches.append(article_data)

        # 정확히 일치하는 매물을 먼저, 그 다음 부분 일치하는 매물
        matched_articles = exact_matches + partial_matches

        if not matched_articles:
            # 디버깅 정보 포함
            sample_apt_names = [
                a.get("atclNm") or a.get("articleName", "") for a in all_articles[:5]
            ]
            return json.dumps(
                {
                    "status": "no_data",
                    "message": f"'{address}'에 해당하는 아파트 매물을 찾을 수 없습니다.",
                    "tip": "아파트명을 포함한 정확한 주소를 입력해주세요.",
                    "debug": {
                        "total_articles": len(all_articles),
                        "apartment_name": apartment_name,
                        "sample_apt_names": sample_apt_names,
                    },
                },
                ensure_ascii=False,
                indent=2,
            )

        # 정렬: 먼저 매칭점수로 정렬 (높은 것부터), 그 다음 평당 가격으로 정렬 (낮은 것부터)
        matched_articles.sort(
            key=lambda x: (
                -(x.get("매칭점수") or 0),  # 매칭점수는 내림차순 (높은 것이 먼저)
                x.get("평당가격_만원")
                or float("inf"),  # 평당가격은 오름차순 (낮은 것이 먼저)
            )
        )

        # 평균 평당 가격 계산
        valid_prices = [
            a["평당가격_만원"] for a in matched_articles if a.get("평당가격_만원")
        ]
        avg_price_per_pyeong = (
            round(sum(valid_prices) / len(valid_prices), 2) if valid_prices else None
        )

        # 매칭점수 제거 (최종 출력에는 불필요)
        for article in matched_articles:
            article.pop("매칭점수", None)

        result = {
            "status": "success",
            "address": address,
            "아파트명": apartment_name,
            "매물수": len(matched_articles),
            "정확일치_매물수": len(exact_matches),
            "평균_평당가격_만원": avg_price_per_pyeong,
            "매물목록": matched_articles[
                :10
            ],  # 최대 10개 반환 (아파트명 우선순위 고려)
        }

        return json.dumps(result, ensure_ascii=False, indent=2)

    except requests.exceptions.RequestException as e:
        return json.dumps(
            {
                "status": "error",
                "error": f"API 호출 오류: {str(e)}",
            },
            ensure_ascii=False,
            indent=2,
        )
    except Exception as e:
        return json.dumps(
            {
                "status": "error",
                "error": f"처리 오류: {str(e)}",
            },
            ensure_ascii=False,
            indent=2,
        )


# 사용 예시
if __name__ == "__main__":
    #     # 예시 1: 아파트명 포함 주소로 조회
    #     print("=== 예시 1: 서울시 강남구 래미안 강남파크 ===")
    #     result_json = get_naver_land_price("서울시 강남구 래미안 강남파크")
    #     result = json.loads(result_json)

    #     if result.get("status") == "success":
    #         print(f"매물수: {result['매물수']}개")
    #         print(f"평균 평당가격: {result['평균_평당가격_만원']}만원")
    #         print("\n매물 목록:")
    #         for i, item in enumerate(result["매물목록"], 1):
    #             print(f"\n[{i}] {item['아파트명']}")
    #             print(f"    주소: {item.get('주소', 'N/A')}")
    #             print(
    #                 f"    가격: {item.get('가격', 'N/A')} ({item.get('가격_만원', 'N/A')}만원)"
    #             )
    #             print(f"    전용면적: {item.get('전용면적_㎡', 'N/A')}㎡")
    #             print(f"    평당가격: {item.get('평당가격_만원', 'N/A')}만원/평")
    #             print(f"    층: {item.get('층', 'N/A')}")
    #     else:
    #         print(result_json)

    # 예시: JSON 형식으로 반환 확인

    test_address = "도곡렉슬"
    print(f"검색 주소: {test_address}\n")

    # 함수 호출 - JSON 문자열 반환
    result_json = get_naver_land_price(test_address)

    # JSON 형식으로 출력
    print(result_json)

    # JSON 파싱 예시 (필요한 경우)
    # result = json.loads(result_json)
    # if result.get("status") == "success":
    #     print(f"\n✓ 성공! 매물수: {result['매물수']}개")
    #     print(f"평균 평당가격: {result['평균_평당가격_만원']}만원")
