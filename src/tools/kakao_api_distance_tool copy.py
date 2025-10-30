import requests
import pandas as pd
import json
import math
import os
from dotenv import load_dotenv
load_dotenv()

# ============================================================
# API 키 설정
# ============================================================
KAKAO_REST_API_KEY = os.getenv("KAKAO_REST_API_KEY")
MOLIT_API_KEY = os.getenv("MOLIT_API_KEY")
REB_API_KEY = 'YOUR_REB_API_KEY'

# ============================================================
# 1. 주소 → 좌표 변환
# ============================================================
def get_coordinates_from_address(address):
    """주소를 위경도 좌표로 변환"""
    url = 'https://dapi.kakao.com/v2/local/search/address.json'
    headers = {'Authorization': f'KakaoAK {KAKAO_REST_API_KEY}'}
    params = {'query': address}
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        result = response.json()
        if result['documents']:
            x = float(result['documents'][0]['x'])  # 경도
            y = float(result['documents'][0]['y'])  # 위도
            return y, x
    return None, None

# ============================================================
# 2. 거리 계산 (Haversine Formula)
# ============================================================
def calculate_distance(lat1, lon1, lat2, lon2):
    """두 좌표 간 거리(km) 계산"""
    R = 6371  # 지구 반지름(km)
    
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

# ============================================================
# 3. 주변 아파트 검색 (카카오 API)
# ============================================================
def search_nearby_apartments(lat, lon, radius=5000):
    """
    좌표 기반 주변 아파트 검색
    radius: 검색 반경(미터), 최대 20000m
    """
    url = 'https://dapi.kakao.com/v2/local/search/keyword.json'
    headers = {'Authorization': f'KakaoAK {KAKAO_REST_API_KEY}'}
    
    apartments = []
    page = 1
    
    while page <= 3:  # 최대 45개
        params = {
            'query': '아파트',
            'x': lon,
            'y': lat,
            'radius': radius,
            'sort': 'distance',  # 거리순 정렬
            'page': page,
            'size': 15
        }
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            result = response.json()
            documents = result.get('documents', [])
            
            if not documents:
                break
                
            for doc in documents:
                apartments.append({
                    '아파트명': doc['place_name'],
                    '주소': doc['address_name'],
                    '도로명주소': doc.get('road_address_name', ''),
                    '위도': float(doc['y']),
                    '경도': float(doc['x']),
                    '거리(km)': float(doc['distance']) / 1000
                })
            
            if result['meta']['is_end']:
                break
            page += 1
        else:
            break
    
    return pd.DataFrame(apartments)

# ============================================================
# 4. 분양정보 조회 (한국부동산원 API)
# ============================================================
def get_presale_apartments(area_name):
    """지역명으로 분양정보 조회"""
    url = 'https://api.odcloud.kr/api/ApplyhomeInfoDetailSvc/v1/getAPTLttotPblancDetail'
    
    params = {
        'serviceKey': REB_API_KEY,
        'page': '1',
        'perPage': '100',
        'returnType': 'json',
        'cond[SUBSCRPT_AREA_CODE_NM::EQ]': area_name
    }
    
    response = requests.get(url, params=params)
    
    presales = []
    if response.status_code == 200:
        result = response.json()
        data = result.get('data', [])
        
        for item in data:
            presales.append({
                '주택명': item.get('HOUSE_NM', ''),
                '공급위치': item.get('HSSPLY_ADRES', ''),
                '공급규모': item.get('TOT_SUPLY_HSHLDCO', ''),
                '모집공고일': item.get('RCRIT_PBLANC_DE', ''),
                '청약접수시작일': item.get('SUBSCRPT_RCEPT_BGNDE', '')
            })
    
    return pd.DataFrame(presales)

# ============================================================
# 5. 메인 함수
# ============================================================
def get_real_estate_info(business_site_address):
    """사업지 주소 입력 → 자동 수집"""
    
    print(f"\n{'='*60}")
    print(f"사업지: {business_site_address}")
    print(f"{'='*60}\n")
    
    # 1) 좌표 획득
    lat, lon = get_coordinates_from_address(business_site_address)
    
    if lat is None:
        print("주소를 찾을 수 없습니다.")
        return None
    
    print(f"✓ 좌표: 위도 {lat:.6f}, 경도 {lon:.6f}\n")
    
    # 2) 매매 아파트 검색
    print("■ 주변 매매 아파트 검색 중...")
    apartments_df = search_nearby_apartments(lat, lon, radius=5000)
    
    if apartments_df.empty:
        print("⚠ 주변 아파트 없음\n")
        top3_sale = pd.DataFrame()
    else:
        top3_sale = apartments_df.head(3)
        print(f"✓ 발견: {len(apartments_df)}개\n")
        
        print("=== 가장 가까운 매매 아파트 TOP 3 ===")
        for idx, row in top3_sale.iterrows():
            print(f"{idx+1}. {row['아파트명']}")
            print(f"   주소: {row['주소']}")
            print(f"   거리: {row['거리(km)']:.2f}km\n")
    
    # 3) 분양 정보 조회
    region = business_site_address.split()[0]
    print(f"{region} 분양 아파트 검색 중...")
    
    presale_df = get_presale_apartments(region)
    
    if presale_df.empty:
        print("분양 정보 없음\n")
        top3_presale = pd.DataFrame()
    else:
        # 거리 계산
        presale_with_dist = []
        for idx, row in presale_df.iterrows():
            p_lat, p_lon = get_coordinates_from_address(row['공급위치'])
            if p_lat:
                distance = calculate_distance(lat, lon, p_lat, p_lon)
                row['거리(km)'] = distance
                presale_with_dist.append(row)
        
        presale_df = pd.DataFrame(presale_with_dist)
        presale_df = presale_df.sort_values('거리(km)').reset_index(drop=True)
        top3_presale = presale_df.head(3)
        
        print(f"✓ 발견: {len(presale_df)}개\n")
        
        print("=== 가장 가까운 분양 아파트 TOP 3 ===")
        for idx, row in top3_presale.iterrows():
            print(f"{idx+1}. {row['주택명']}")
            print(f"   위치: {row['공급위치']}")
            print(f"   거리: {row['거리(km)']:.2f}km")
            print(f"   규모: {row['공급규모']}세대\n")
    
    # 4) JSON 저장
    result = {
        "사업지": {
            "주소": business_site_address,
            "위도": lat,
            "경도": lon
        },
        "매매아파트": top3_sale.to_dict('records'),
        "분양아파트": top3_presale.to_dict('records')
    }
    
    with open('부동산분석.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"{'='*60}")
    print(f"✓ 완료! 결과: 부동산분석.json")
    print(f"{'='*60}\n")
    
    return result

# ============================================================
# 실행
# ============================================================
if __name__ == '__main__':
    # 사업지 주소만 입력
    result = get_real_estate_info('서울특별시 송파구 마천동 299-23')
