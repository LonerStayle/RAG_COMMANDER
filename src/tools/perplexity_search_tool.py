import os
from perplexity import Perplexity
from dotenv import load_dotenv
from langchain_core.tools import tool

load_dotenv()

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
client = Perplexity(api_key=PERPLEXITY_API_KEY)  # Automatically uses PERPLEXITY_API_KEY


@tool
def perplexity_search(query: str) -> str:
    """Perplexity AI를 사용하여 최신 정보를 검색합니다.

    이 도구는 실시간 웹 검색을 통해 최신 정보, 뉴스, 데이터를 찾아 사실 확인과 검증을 수행합니다.
    부동산 호재, 개발 계획, 교통 인프라 등의 정보를 검증할 때 사용하세요.

    Args:
        query: 검색할 질문이나 프롬프트. 구체적이고 명확한 질문을 사용하세요.

    Returns:
        str: Perplexity AI의 검색 결과 및 분석
    """
    response = client.chat.completions.create(
        model="sonar-reasoning-pro", messages=[{"role": "user", "content": query}]
    )
    return response.choices[0].message.content


"""
    <CONTEXT>
    주소:송파구 마천동 299-23
    규모: 1000세대
    타입: 84m²
    </CONTEXT>
    <GOAL>
    <CONTEXT>의 주소, 규모, 타입이 유사하고, 최단거리에 있는 매매아파트 3개, 분양단지 3개를 찾아서 매매아파트 3개는 각각의 평당매매가격, 분양단지 3개는 각각의 평당분양가격을 출력해 주세요
    </GOAL>
    <RULE>
    json 형식으로 출력해주세요.
    </RULE>
    <OUTPUT>
    단지명:
    주소:
    규모:
    타입:
    평당매매가격 OR 평당분양가격:
    거리:
    비고:
    </OUTPUT>
"""
"""
from src.tools.perplexity_search_tool import perplexity_search
print(perplexity_search(    
    <CONTEXT>
    주소:송파구 마천동 299-23
    규모: 1000세대
    타입: 84m²
    </CONTEXT>
    <GOAL>
    <CONTEXT> 주변 분양호재를 <OUTPUT>을 참조해서 json 형식으로 출력해주세요
    </GOAL>
    <RULE>
    다른 말은 다 생략하고 <OUTPUT> 형식으로 출력해 주세요
    </RULE>
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
)
    """
