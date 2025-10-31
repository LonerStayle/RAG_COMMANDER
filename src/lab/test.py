import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent / "RAG_COMMANDER"  # 프로젝트 경로에 맞게 수정
sys.path.insert(0, str(project_root / "src"))

# from tools import get_location_profile

# # 사용
# result = get_location_profile("서울특별시 강남구 역삼동")
# print(result)


# {
#   "매매아파트": [
#     {
#       "주소와단지명": "",
#       "규모": "",
#       "타입": "",
#       "평당매매가격": "",
#       "거리": "약 0.3km",
#       "비고": "대상지와 가장 인접한 대단지 준신축 아파트로 직접적인 시세 비교군입니 다."
#     },
#   ],
#   "분양아파트": [
 
#     {
#       "주소와단지명": "",
#       "규모": "",
#       "타입": "",
#       "평당매매가격": "",
#       "거리": "약 0.3km",
#       "비고": "대상지와 가장 인접한 대단지 준신축 아파트로 직접적인 시세 비교군입니 다."
#     },
#   ],
# }

    # 단지명:
    # 주소:
    # 규모:
    # 타입:
    # 평당매매가격 OR 평당분양가격:
    # 거리:
    # 비고:
from src.tools.pre_pomise_competition_tool import search_by_address
result = search_by_address("송파구 마천동 299-23")
print(result)