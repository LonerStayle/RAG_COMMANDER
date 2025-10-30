# 국토교통부 통계누리 검색 Tool

국토교통부(국토부) 통계누리 사이트에서 정책 관련 보도자료와 통계 데이터를 검색하는 LangChain tool입니다.

## 기능

- 국토교통부 공식 사이트에서 정책 보도자료 검색
- 국토교통통계누리에서 통계 데이터 검색
- Perplexity API를 활용한 정확한 검색
- LangChain Agent와 통합 가능

## 설치

필요한 패키지가 이미 `pyproject.toml`에 포함되어 있습니다:
- `perplexityai>=0.17.1`
- `langchain>=1.0.0`
- `langchain-core>=1.0.0`

## 환경 설정

`.env` 파일에 Perplexity API 키를 추가하세요:

```env
PERPLEXITY_API_KEY=your_api_key_here
```

## 사용법

### 1. 기본 사용 (LangChain Tool)

```python
from tools.molit_search_tool import search_molit_policy, search_molit_statistics

# 정책 보도자료 검색
result = search_molit_policy.invoke({"query": "2025년 주택공급"})
print(result)

# 통계 데이터 검색
result = search_molit_statistics.invoke({
    "query": "아파트 분양실적",
    "year": "2025"
})
print(result)
```

### 2. LangChain Agent와 통합

```python
from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate
from tools.molit_search_tool import get_molit_tools

# LLM 및 도구 초기화
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
tools = get_molit_tools()

# 프롬프트 설정
prompt = ChatPromptTemplate.from_messages([
    ("system", "당신은 대한민국 부동산 정책 전문가입니다."),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

# Agent 생성 및 실행
agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

response = agent_executor.invoke({
    "input": "2025년 주택공급 계획에 대해 알려주세요."
})
print(response["output"])
```

### 3. 클래스 직접 사용

```python
from tools.molit_search_tool import MolitSearchTool

# 검색 도구 초기화
searcher = MolitSearchTool()

# 검색 실행
results = searcher.search_policy_news(
    query="주택담보대출",
    max_results=5
)

# 결과 포맷팅
formatted = searcher.format_results(results)
print(formatted)
```

### 4. 특정 사이트만 검색

```python
# 통계누리만 검색
results = searcher.search_policy_news(
    query="아파트 매매가",
    sites=["stat.molit.go.kr"],
    max_results=5
)
```

## Tool 목록

### 1. `search_molit_policy`

국토교통부 공식 사이트에서 정책 관련 보도자료를 검색합니다.

**Parameters:**
- `query` (str): 검색할 키워드

**Returns:**
- 검색 결과 (제목, URL, 요약, 날짜 포함)

**Example:**
```python
search_molit_policy.invoke({"query": "분양가상한제"})
```

### 2. `search_molit_statistics`

국토교통통계누리에서 통계 자료를 검색합니다.

**Parameters:**
- `query` (str): 검색할 통계 주제
- `year` (str, optional): 검색할 연도

**Returns:**
- 검색 결과 (제목, URL, 요약, 날짜 포함)

**Example:**
```python
search_molit_statistics.invoke({
    "query": "아파트 분양실적",
    "year": "2025"
})
```

## 주요 클래스

### `MolitSearchTool`

국토교통부 검색을 위한 핵심 클래스입니다.

**Methods:**

#### `search_policy_news(query, sites=None, max_results=5)`
정책 보도자료 검색

**Parameters:**
- `query` (str): 검색 키워드
- `sites` (List[str], optional): 검색할 사이트 목록
- `max_results` (int): 최대 결과 수 (기본값: 5)

**Returns:**
- List[Dict]: 검색 결과 리스트

#### `format_results(results)`
검색 결과를 읽기 쉬운 형태로 포맷팅

**Parameters:**
- `results` (List[Dict]): 검색 결과 리스트

**Returns:**
- str: 포맷팅된 문자열

## 검색 대상 사이트

기본적으로 다음 사이트를 검색합니다:
- `www.molit.go.kr` - 국토교통부
- `stat.molit.go.kr` - 국토교통통계누리
- `www.molit.go.kr/USR/policyData` - 정책자료실

## 테스트

테스트 노트북을 실행하세요:

```bash
jupyter notebook src/lab/test_molit_tool.ipynb
```

또는 Python 스크립트로 테스트:

```python
python src/tools/molit_search_tool.py
```

## 주의사항

1. **API 키 필요**: Perplexity API 키가 필요합니다.
2. **Rate Limit**: Perplexity API의 rate limit을 고려하세요.
3. **네트워크 연결**: 인터넷 연결이 필요합니다.

## 사용 예시

### 예시 1: 주택 정책 검색
```python
from tools.molit_search_tool import search_molit_policy

result = search_molit_policy.invoke({
    "query": "2025년 주택공급 계획"
})
print(result)
```

### 예시 2: 미분양 통계 검색
```python
from tools.molit_search_tool import search_molit_statistics

result = search_molit_statistics.invoke({
    "query": "미분양 아파트 현황",
    "year": "2025"
})
print(result)
```

### 예시 3: 여러 키워드 검색
```python
from tools.molit_search_tool import MolitSearchTool

searcher = MolitSearchTool()
keywords = ["분양가상한제", "재건축", "재개발"]

for keyword in keywords:
    results = searcher.search_policy_news(keyword)
    formatted = searcher.format_results(results)
    print(f"\n검색어: {keyword}")
    print(formatted)
```

## 트러블슈팅

### Import 에러가 발생하는 경우

```python
import sys
from pathlib import Path

# src 디렉토리를 path에 추가
src_dir = Path(__file__).parent.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from tools.molit_search_tool import search_molit_policy
```

### Perplexity API 에러가 발생하는 경우

1. `.env` 파일에 API 키가 올바르게 설정되었는지 확인
2. API 키가 유효한지 확인
3. Rate limit을 초과하지 않았는지 확인

## 라이센스

이 프로젝트는 RAG_COMMANDER 프로젝트의 일부입니다.

## 기여

버그 리포트나 기능 제안은 이슈로 등록해주세요.
