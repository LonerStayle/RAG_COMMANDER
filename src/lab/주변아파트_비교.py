import pandas as pd
from datetime import datetime
from xml.etree import ElementTree as ET
import 카카오api_좌표거리 as kakao
import 좌표간거리 as distance

def get_lawd_code(address):
    """주소에서 법정동 코드 추출
    예: 서울특별시 송파구 마천동 → 11710
    
    실제로는 행정안전부 법정동코드 API 활용
    """
    # 간단 매핑 예시 (송파구)
    lawd_code_map = {
        '송파구': '11710',
        '강남구': '11680',
        '서초구': '11650'
    }
    
    for key, code in lawd_code_map.items():
        if key in address:
            return code
    
  # 기본값

def get_apartment_trade_data(lawd_cd, deal_ymd, service_key):
    """아파트 매매 실거래가 조회
    
    Args:
        lawd_cd: 법정동코드 (예: 11710)
        deal_ymd: 계약년월 (예: 202410)
        service_key: 공공데이터포털 서비스키
    """
    url = "http://openapi.molit.go.kr/OpenAPI_ToolInstallPackage/service/rest/RTMSOBJSvc/getRTMSDataSvcAptTradeDev"
    
    params = {
        'serviceKey': service_key,
        'pageNo': '1',
        'numOfRows': '999',
        'LAWD_CD': lawd_cd,
        'DEAL_YMD': deal_ymd
    }
    
    response = requests.get(url, params=params)
    root = ET.fromstring(response.content)
    
    items = root.findall('.//item')
    data_list = []
    
    for item in items:
        data = {
            '아파트명': item.findtext('아파트'),
            '법정동': item.findtext('법정동'),
            '지번': item.findtext('지번'),
            '전용면적': float(item.findtext('전용면적')),
            '거래금액': item.findtext('거래금액').strip().replace(',', ''),
            '건축년도': item.findtext('건축년도'),
            '층': item.findtext('층'),
            '년': item.findtext('년'),
            '월': item.findtext('월'),
            '일': item.findtext('일')
        }
        
        # 평당 가격 계산 (1평 = 3.3058㎡)
        pyeong = data['전용면적'] / 3.3058
        data['평수'] = round(pyeong, 2)
        data['평당가격(만원)'] = round(int(data['거래금액']) / pyeong, 2)
        data['주소'] = f"{data['법정동']} {data['지번']}"
        
        data_list.append(data)
    
    return pd.DataFrame(data_list)

def find_nearby_apartments(business_address, biz_x, biz_y, radius_km=3, service_key="YOUR_KEY"):
    """사업지 주변 매매 아파트 찾기"""
    
    # 1. 법정동 코드 획득
    lawd_cd = get_lawd_code(business_address)
    
    # 2. 최근 6개월 실거래 데이터 수집
    now = datetime.now()
    trade_data = pd.DataFrame()
    
    for i in range(6):
        if now.month - i > 0:
            year_month = now.replace(month=now.month - i)
        else:
            year_month = now.replace(year=now.year-1, month=12+now.month-i)
        
        deal_ymd = year_month.strftime('%Y%m')
        month_data = get_apartment_trade_data(lawd_cd, deal_ymd, service_key)
        trade_data = pd.concat([trade_data, month_data], ignore_index=True)
    
    # 3. 각 아파트의 좌표 획득 및 거리 계산
    apartments_with_coords = []
    
    for _, row in trade_data.iterrows():
        full_address = f"{business_address.split()[0]} {business_address.split()[1]} {row['주소']}"
        apt_x, apt_y = kakao.get_coordinates(full_address)
        
        if apt_x and apt_y:
            distance = distance.calculate_distance(biz_x, biz_y, apt_x, apt_y)
            
            if distance <= radius_km * 1000:
                row_dict = row.to_dict()
                row_dict['좌표_x'] = apt_x
                row_dict['좌표_y'] = apt_y
                row_dict['사업지와_거리(m)'] = round(distance, 0)
                apartments_with_coords.append(row_dict)
    
    result_df = pd.DataFrame(apartments_with_coords)
    
    # 4. 아파트별 최신 거래가 기준으로 정리
    if not result_df.empty:
        result_df['거래일'] = pd.to_datetime(
            result_df['년'] + '-' + result_df['월'] + '-' + result_df['일']
        )
        result_df = result_df.sort_values('거래일', ascending=False)
        
        # 아파트별 대표 거래 선정 (가장 최근 거래)
        latest_trades = result_df.groupby('아파트명').first().reset_index()
        
        # 거리순 정렬 후 상위 3개
        top_3 = latest_trades.nsmallest(3, '사업지와_거리(m)')
        return top_3
    
    return pd.DataFrame()

# 사용 예시
business_address = "서울특별시 송파구 마천동 299-23"
biz_x, biz_y = kakao.get_coordinates(business_address)

SERVICE_KEY = "nEmoa4/43u4WcWznQBC8b4Cd0x6Py+Pz20kqQs6G54f2+fK5gPX084Mv/ss5wMEU1noKUrOhMAxLEooMd69UDw=="
nearby_apts = find_nearby_apartments(business_address, biz_x, biz_y, radius_km=3, service_key=SERVICE_KEY)

print("\n=== 주변 매매 아파트 (3개) ===")
for idx, row in nearby_apts.iterrows():
    print(f"\n{row['아파트명']}")
    print(f"  - 주소: {row['주소']}")
    print(f"  - 거리: {row['사업지와_거리(m)']}m")
    print(f"  - 최근 거래가: {row['거래금액']}만원 ({row['평수']}평)")
    print(f"  - 평당가격: {row['평당가격(만원)']}만원")