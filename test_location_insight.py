"""
Location Insight Agent 테스트 스크립트
"""
# .env 파일에서 환경 변수 로드
from dotenv import load_dotenv
load_dotenv()

from agents.analysis.location_insight_agent import location_insight_graph

def test_location_insight():
    # 테스트 입력
    initial_state = {
        "start_input": {
            "target_area": "서울시 강남구 역삼동",
            "main_type": "84제곱미터",
            "total_units": 500
        }
    }

    print("\n" + "=" * 80)
    print("Location Insight Agent 실행 시작")
    print("=" * 80)
    print(f"분석 지역: {initial_state['start_input']['target_area']}")
    print(f"규모: {initial_state['start_input']['main_type']}")
    print(f"세대수: {initial_state['start_input']['total_units']}")
    print("=" * 80 + "\n")

    # 그래프 실행
    result = location_insight_graph.invoke(initial_state)

    # 최종 결과 출력
   
    print("=" * 80)
    print(result.get("location_insight_output", "결과 없음"))
    print("=" * 80 + "\n")

    # 추가 정보
    print("기타 정보:")
    print(f"- RAG Context: {result.get('rag_context', 'N/A')}")
    print(f"- Web Context: {result.get('web_context', 'N/A')}")
    print(f"- 메시지 개수: {len(result.get('messages', []))}")

    return result

if __name__ == "__main__":
    result = test_location_insight()
