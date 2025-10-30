import requests
import json

# 카카오 API 키 설정

KAKAO_API_KEY = "e60c354495a6119f002fbbc9a27483fa"

def search_nearby_keyword(x, y, keyword, radius=3000):
    """키워드로 장소 검색 (예: 공원)
    
    Args:
        x: 경도 (longitude)
        y: 위도 (latitude)
        keyword: 검색 키워드 (예: "공원")
        radius: 검색 반경 (미터 단위, 기본값: 3000m)
    """
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    
    facilities = []
    page = 1
    
    while True:
        params = {
            "query": keyword,
            "x": x,
            "y": y,
            "radius": radius,
            "page": page,
            "size": 15  # 한 페이지당 최대 15개
        }
        
        response = requests.get(url, headers=headers, params=params)
        result = response.json()
        
        if not result.get('documents'):
            break
            
        for place in result['documents']:
            facility_info = {
                'name': place['place_name'],
                'category': place['category_name'],
                'address': place['address_name'],
                'road_address': place.get('road_address_name', ''),
                'x': float(place['x']),
                'y': float(place['y']),
                'distance': int(place['distance']) if place.get('distance') else None  # 미터 단위
            }
            facilities.append(facility_info)
        
        # 마지막 페이지 확인
        if result['meta']['is_end']:
            break
        page += 1
    
    return facilities

parks = search_nearby_keyword(longitude, latitude, 주소)

