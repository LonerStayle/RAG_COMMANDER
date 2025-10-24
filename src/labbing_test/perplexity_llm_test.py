from mcp_client_test import get_tools
import asyncio
from dotenv import load_dotenv
from perplexity import Perplexity

load_dotenv()

client = Perplexity()


async def get_mcp_tools():
    tools = await get_tools()  # ✅ 그냥 await로 실행 가능
    print(tools)
    return tools


def run():
    completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": (
                    "당신은 대한민국 수도권 아파트 분양·미분양 시장을 데이터 분석 기반으로 정밀하게 진단하는 '퍼블릭시티 리서처’ 입니다. "
                    "공공 및 민간 데이터(예: 국토교통부, 서울시, 부동산원 등)를 근거로 지역별(서울 포함) 분양현황, 미분양 리스크, 입주물량 변동을 분석하세요. "
                    "요약형 답변을 피하고, 수치+출처+해석을 포함한 완전한 인사이트를 제공해야 합니다. "
                    "출처가 불명확한 정보가 있다면 ‘데이터 확인 불가’라고 명시하십시오."
                ),
            },
            {
                "role": "user",
                "content": (
                    "서대문구 홍제동 ‘서대문 센트럴 아이파크’를 중심으로 최근 미분양 현황과 "
                    "주변 입주물량, 실거래가 추세를 분석해 주세요. "
                    "가능하다면 2025년 10월 데이터 기준으로 부탁드립니다."
                ),
            },
        ],
        stream=True,
        model="sonar-deep-research",
        web_search_options={
            "user_location": {
                "country": "KR",
                "region": "서대문구",
                "city": "Seoul",
                "latitude": 37.4979,
                "longitude": 127.0276,
            }
        },
        timeout=1200,
    )
    for event in completion:
        chunk = event.choices[0].delta.content
        print(chunk, end="", flush=True)


if __name__ == "__main__":
    # asyncio.run(get_mcp_tools())
    run()
