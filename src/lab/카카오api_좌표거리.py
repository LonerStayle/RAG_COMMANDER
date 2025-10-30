import requests
import json

# 카카오 API 키 설정

KAKAO_API_KEY = "e60c354495a6119f002fbbc9a27483fa"

def get_coordinates(address):
    """주소를 좌표로 변환"""
    url = "https://dapi.kakao.com/v2/local/search/address.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    params = {"query": address}

    response = requests.get(url, headers=headers, params=params)
    result = response.json()

    # 응답 확인 (디버깅용)
    print(f"API 응답: {json.dumps(result, indent=2, ensure_ascii=False)}")

    # 응답에 'documents' 키가 있는지 확인
    if 'documents' in result and result['documents']:
        x = float(result['documents'][0]['x'])  # 경도
        y = float(result['documents'][0]['y'])  # 위도
        return x, y
    else:
        # 에러 메시지가 있으면 출력
        if 'message' in result:
            print(f"API 에러: {result['message']}")
        return None, None

# 사용 예시
address = "서울특별시 송파구 마천동 299-23"
longitude, latitude = get_coordinates(address)
print(f"좌표: 경도 {longitude}, 위도 {latitude}")

def search_nearby_facilities(x, y, category_code, radius=3000):
    """반경 내 시설 검색
    
    카테고리 코드:
    - SC4: 학교
    - AC5: 학원  
    - SW8: 지하철역
    - MT1: 대형마트
    - HP8: 병원
    - BK9: 은행
    - OL7: 주유소소
    """
    url = "https://dapi.kakao.com/v2/local/search/category.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    
    facilities = []
    page = 1
    
    while True:
        params = {
            "category_group_code": category_code,
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
                'distance': int(place['distance'])  # 미터 단위
            }
            facilities.append(facility_info)
        
        # 마지막 페이지 확인
        if result['meta']['is_end']:
            break
        page += 1
    
    return facilities

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



# 사용 예시: 교육환경 검색
schools = search_nearby_facilities(longitude, latitude, 'SC4')
academies = search_nearby_facilities(longitude, latitude, 'AC5')
subway = search_nearby_facilities(longitude, latitude, 'SW8')
mart = search_nearby_facilities(longitude, latitude, 'MT1')
hospital = search_nearby_facilities(longitude, latitude, 'HP8')
bank = search_nearby_facilities(longitude, latitude, 'BK9')
parks = search_nearby_keyword(longitude, latitude, "공원")

# print(f"\n반경 3km 내 학교: {len(schools)}개")
# for school in schools[:3]:
#     print(f"  - {school['name']}: {school['distance']}m")

# print(subway)

# for school in schools[:2]:
#     print(school)
print(schools[:3])
print(academies[:3])
print(subway[:3])
print(mart[:3])
print(hospital[:3])
print(bank[:3])
print(parks[:3])
