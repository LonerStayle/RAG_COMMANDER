from mcp_client_test import get_tools
import asyncio
from dotenv import load_dotenv
from perplexity import Perplexity
from langchain_openai import ChatOpenAI
load_dotenv()
client = Perplexity()


async def get_mcp_tools():
    tools = await get_tools()  # ✅ 그냥 await로 실행 가능
    print(tools)
    return tools


def run():
    search = client.search.create(
        query=[
            """대한민국 수도권 아파트 분양가 및 미분양 리스크를 거시경제 관점에서 정밀히 진단하기 위해 검색해주세요.""",
            """반드시 2025년 10월 기준으로 찾아주세요.
            다음 거시환경 요소들에 대해 최근 3년(2023-2025) 또는 최신 가능 연도 기준으로 한국(특히 수도권) 데이터를 활용해 분석해 주세요:  
            • 기준금리 및 주택담보대출 금리 추이  
            • 국내 GDP 성장률 및 산업생산지수 변화  
            • 주택 매매가·전세가 인덱스 시계열 변화  
            • 금융시장(예: 채권금리, 주가지수) 및 심리지표 변화  

            분석 결과가 아파트 분양가 및 미분양 리스크에 어떤 영향을 줄 수 있는지 서론·본론·결론 구조로 설명해 주세요""",
        ]
    )
    #     completion = client.chat.completions.create(
    #         messages=[
    #             {
    #                 "role": "system",
    #                 "content": """반드시 2025년 10월 기준으로 찾아주세요.
    # 당신은 대한민국 수도권 아파트 분양가 및 미분양 리스크를 거시경제 관점에서 정밀히 진단하는 ‘퍼블릭시티 거시환경 애널리스트’입니다.
    # 요약형 답변을 피하고, **수치 + 출처 + 해석**을 포함한 분석 리포트 형식(서론 → 본론 → 결론)으로 응답하십시오.
    # 답변을 완성후 맨 마지막에 모든 출처 링크를 달아주세요.
    # 추가로 접근이 필요했지만 권한이 없어서 접근 못한 링크도 달아주세요.
    # 확인이 안 되는 정보는 “데이터 확인 불가”라고 명시하세요.""",
    #             },
    #             {
    #                 "role": "user",
    #                 "content": """반드시 2025년 10월 기준으로 찾아주세요.
    # 다음 거시환경 요소들에 대해 최근 3년(2023-2025) 또는 최신 가능 연도 기준으로 한국(특히 수도권) 데이터를 활용해 분석해 주세요:
    # • 기준금리 및 주택담보대출 금리 추이
    # • 국내 GDP 성장률 및 산업생산지수 변화
    # • 주택 매매가·전세가 인덱스 시계열 변화
    # • 금융시장(예: 채권금리, 주가지수) 및 심리지표 변화

    # 분석 결과가 아파트 분양가 및 미분양 리스크에 어떤 영향을 줄 수 있는지 서론·본론·결론 구조로 설명해 주세요.""",
    #             }
    #         ],
    #         stream=True,
    #         model="sonar-reasoning-pro",
    #         web_search_options={
    #             "user_location": {
    #                 "country": "KR",
    #                 "region": "서대문구",
    #                 "city": "Seoul",
    #                 "latitude": 37.4979,
    #                 "longitude": 127.0276,
    #             }
    #         },
    #         # search_domain_filter=["kosis.kr", "krihs.re.kr", "-blog.naver.com"],
    #         timeout=1200,
    #     )
    # for event in completion:
    #     chunk = event.choices[0].delta.content
    #     print(chunk, end="", flush=True)
    for result in search.results:
        print(result)
        print(f"{result.snippet}")

async def start_llm():
    llm = ChatOpenAI(model="gpt-4.0",temperature=0)
    tools = await get_mcp_tools()
    llm_tools = llm.bind_tools(tools)
    res = llm_tools.invoke(         
        """대한민국 수도권 아파트 분양가 및 미분양 리스크를 거시경제 관점에서 정밀히 진단하기 위해 검색해주세요.""" +   
        """반드시 2025년 10월 기준으로 찾아주세요.
            다음 거시환경 요소들에 대해 최근 3년(2023-2025) 또는 최신 가능 연도 기준으로 한국(특히 수도권) 데이터를 활용해 분석해 주세요:  
            • 기준금리 및 주택담보대출 금리 추이  
            • 국내 GDP 성장률 및 산업생산지수 변화  
            • 주택 매매가·전세가 인덱스 시계열 변화  
            • 금융시장(예: 채권금리, 주가지수) 및 심리지표 변화  

            분석 결과가 아파트 분양가 및 미분양 리스크에 어떤 영향을 줄 수 있는지 서론·본론·결론 구조로 설명해 주세요""")
    print(res.content)

if __name__ == "__main__":

    # asyncio.run(get_mcp_tools())
    asyncio.run(start_llm())
    
