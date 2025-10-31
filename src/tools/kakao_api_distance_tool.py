import os
import requests
from dotenv import load_dotenv

load_dotenv()

KAKAO_BASE_URL = "https://dapi.kakao.com"
DEFAULT_RADIUS = 3000

"""
주소를 좌표로 변환하고 좌표를 기준으로 주변 입지를 검색하는 도구구
"""


def _load_api_key():
    key = os.getenv("KAKAO_REST_API_KEY")
    if key:
        return key
    raise RuntimeError(
        "카카오 REST API 키가 없습니다. .env 파일에 KAKAO_REST_API_KEY를 추가해 주세요."
    )


def _call_kakao(path, params):
    headers = {"Authorization": f"KakaoAK {_load_api_key()}"}
    response = requests.get(
        f"{KAKAO_BASE_URL}{path}",
        headers=headers,
        params=params,
        timeout=10,
    )
    data = response.json()
    return data.get("documents") or []


def get_coordinates(address):
    """주소를 경도/위도로 변환."""
    documents = _call_kakao("/v2/local/search/address.json", {"query": address})
    if not documents:
        return None
    first = documents[0]
    return {"longitude": float(first["x"]), "latitude": float(first["y"])}


def _build_place(place):
    return {
        "이름": place.get("place_name", ""),
        "주소": place.get("road_address_name") or place.get("address_name", ""),
        "거리(미터)": int(place.get("distance") or 0),
    }


def _format_places(documents):
    places = [_build_place(place) for place in documents]
    return sorted(places, key=lambda item: item["거리(미터)"])[:3]


def _search_category(coords, category_code, radius):
    params = {
        "category_group_code": category_code,
        "x": coords["longitude"],
        "y": coords["latitude"],
        "radius": radius,
        "size": 15,
    }
    return _format_places(_call_kakao("/v2/local/search/category.json", params))


def _search_keyword(coords, keyword, radius):
    params = {
        "query": keyword,
        "x": coords["longitude"],
        "y": coords["latitude"],
        "radius": radius,
        "size": 15,
    }
    return _format_places(_call_kakao("/v2/local/search/keyword.json", params))


def _get_school_info(coords, radius):
    return _search_category(coords, "SC4", radius)


def _get_academy_info(coords, radius):
    return _search_category(coords, "AC5", radius)


def _get_transport_info(coords, radius):
    return _search_category(coords, "SW8", radius)


def _get_convenience_info(coords, radius):
    mart = _search_category(coords, "MT1", radius)
    hospital = _search_category(coords, "HP8", radius)
    return {"대형마트": mart, "병원": hospital}


def _get_nature_info(coords, radius):
    return _search_keyword(coords, "공원", radius)


def _get_future_value_info(coords, radius):
    return _search_keyword(coords, "재건축", radius)


def get_location_profile(address, radius=DEFAULT_RADIUS):
    coords = get_coordinates(address)
    if not coords:
        return {"주소": address, "좌표": None, "메시지": "좌표를 찾지 못했습니다."}
    return {
        "주소": address,
        "좌표": coords,
        "교육환경": {
            "학교": _get_school_info(coords, radius),
            "학원": _get_academy_info(coords, radius),
        },
        "교통여건": _get_transport_info(coords, radius),
        "편의여건": _get_convenience_info(coords, radius),
        "자연환경": _get_nature_info(coords, radius),
        "미래가치": _get_future_value_info(coords, radius),
    }


__all__ = ["get_location_profile"]


if __name__ == "__main__":
    sample_address = "서울특별시 송파구 마천동 299-23"
    profile = get_location_profile(sample_address)
    print(profile)

"""
[사용예시]

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent / "RAG_COMMANDER"  # 프로젝트 경로에 맞게 수정
sys.path.insert(0, str(project_root / "src"))

from tools import get_location_profile

# 사용
result = get_location_profile("서울특별시 강남구 역삼동")
print(result)

"""
