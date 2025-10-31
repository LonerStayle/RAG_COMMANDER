import math

def calculate_distance(x1, y1, x2, y2):
    """두 좌표 간 거리 계산 (Haversine 공식)"""
    R = 6371000  # 지구 반지름 (미터)
    
    lat1, lon1 = math.radians(y1), math.radians(x1)
    lat2, lon2 = math.radians(y2), math.radians(x2)
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c