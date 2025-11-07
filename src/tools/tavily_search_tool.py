import os
from tavily import TavilyClient
from dotenv import load_dotenv
from langchain_core.tools import tool

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
client = TavilyClient(api_key=TAVILY_API_KEY)


@tool
def tavily_search(query: str, max_results: int = 5) -> str:
    """Tavily를 사용하여 웹 검색을 수행합니다.

    이 도구는 실시간 웹 검색을 통해 최신 정보, 뉴스, 데이터를 찾습니다.
    청약 경쟁률, 부동산 정보 등의 검색에 사용하세요.

    Args:
        query: 검색할 질문이나 키워드
        max_results: 최대 결과 수 (기본값: 5)

    Returns:
        str: 검색 결과를 요약한 문자열
    """
    try:
        response = client.search(
            query=query,
            max_results=max_results,
            search_depth="advanced"
        )
        
        results = []
        for result in response.get("results", []):
            title = result.get("title", "")
            url = result.get("url", "")
            content = result.get("content", "")
            results.append(f"제목: {title}\nURL: {url}\n내용: {content}\n")
        
        return "\n".join(results) if results else "검색 결과가 없습니다."
    except Exception as e:
        return f"Tavily 검색 오류: {str(e)}"

