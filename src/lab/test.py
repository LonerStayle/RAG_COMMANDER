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
from tools.gemini_search_tool import gemini_search
result = gemini_search("""
<CONTEXT>
주소:송파구 마천동 299-23
규모: 1000세대
타입: 84m²
</CONTEXT>
<GOAL>
<CONTEXT> 주변 분양호재를 <OUTPUT>을 참조해서 json 형식으로 출력해주세요
</GOAL>
<OUTPUT>
{
  "분양호재": [
    {
      "name": "",
      "location": "",
      "description": "",
      "status": ""
    },
  ]
}
</OUTPUT>
""")
print(result)