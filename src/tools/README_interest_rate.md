# 한국/미국 금리 조회 Tool

FRED API(미국 연방준비제도)와 ECOS API(한국은행 경제통계시스템)를 사용하여 한국과 미국의 금리 데이터를 조회하는 LangChain tool입니다.

## 기능

- 미국 기준금리 조회 (FRED API)
- 미국 10년물 국채 수익률 조회 (FRED API)
- 한국 기준금리 조회 (ECOS API)
- 한미 금리 비교 및 격차 분석
- 금리 추세 분석
- LangChain Agent와 통합 가능

## 설치

필요한 패키지가 이미 `pyproject.toml`에 포함되어 있습니다:
- `requests`
- `pandas`
- `langchain>=1.0.0`
- `langchain-core>=1.0.0`

## 환경 설정

`.env` 파일에 API 키를 추가하세요:

```env
FRED_API_KEY=your_fred_api_key_here
ECOS_API_KEY=your_ecos_api_key_here
```

### API 키 발급 방법

#### FRED API 키
1. [FRED 웹사이트](https://fred.stlouisfed.org/)에 접속
2. 계정 생성 또는 로그인
3. [API Keys 페이지](https://fred.stlouisfed.org/docs/api/api_key.html)에서 키 발급

#### ECOS API 키
1. [한국은행 경제통계시스템](https://ecos.bok.or.kr/)에 접속
2. 회원가입 및 로그인
3. 인증키 신청 메뉴에서 키 발급

## 사용법

### 1. 기본 사용 (LangChain Tool)

```python
from tools.interest_rate_tool import (
    get_us_interest_rate,
    get_korea_interest_rate,
    compare_korea_us_rates
)

# 미국 기준금리 조회
result = get_us_interest_rate.invoke({
    "rate_type": "base_rate",
    "months": 12
})
print(result)

# 미국 10년물 국채 수익률 조회
result = get_us_interest_rate.invoke({
    "rate_type": "10y_treasury",
    "months": 12
})
print(result)

# 한국 기준금리 조회
result = get_korea_interest_rate.invoke({"months": 12})
print(result)

# 한미 금리 비교
result = compare_korea_us_rates.invoke({"months": 12})
print(result)
```

### 2. LangChain Agent와 통합

```python
from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate
from tools.interest_rate_tool import get_interest_rate_tools

# LLM 및 도구 초기화
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
tools = get_interest_rate_tools()

# 프롬프트 설정
prompt = ChatPromptTemplate.from_messages([
    ("system", "당신은 글로벌 금리 분석 전문가입니다."),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

# Agent 생성 및 실행
agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

response = agent_executor.invoke({
    "input": "현재 한국과 미국의 기준금리를 비교하고 분석해주세요."
})
print(response["output"])
```

### 3. 클래스 직접 사용

```python
from tools.interest_rate_tool import InterestRateTool

# 도구 초기화
rate_tool = InterestRateTool()

# 미국 기준금리 데이터
us_data = rate_tool.get_us_rates("base_rate", months=12)
print(f"데이터 수: {len(us_data)}")
print(f"최신 금리: {us_data[-1]['value']}% ({us_data[-1]['date']})")

# 한국 기준금리 데이터
kr_data = rate_tool.get_korea_rate(months=12)
print(f"데이터 수: {len(kr_data)}")
print(f"최신 금리: {kr_data[-1]['value']}% ({kr_data[-1]['date']})")

# 한미 금리 비교
comparison = rate_tool.compare_rates(months=12)
print(f"금리 격차: {comparison['rate_spread']}%p")
print(f"금리 역전: {comparison['is_inverted']}")
```

## Tool 목록

### 1. `get_us_interest_rate`

미국 금리 데이터를 조회합니다.

**Parameters:**
- `rate_type` (str): 금리 종류
  - `"base_rate"`: 미국 기준금리 (FEDFUNDS)
  - `"10y_treasury"`: 10년물 국채 수익률 (DGS10)
- `months` (int): 조회할 기간 (개월 수, 기본값: 12)

**Returns:**
- 금리 데이터 (날짜와 금리 값 포함)

**Example:**
```python
get_us_interest_rate.invoke({
    "rate_type": "base_rate",
    "months": 12
})
```

### 2. `get_korea_interest_rate`

한국 기준금리 데이터를 조회합니다.

**Parameters:**
- `months` (int): 조회할 기간 (개월 수, 기본값: 12)

**Returns:**
- 금리 데이터 (날짜와 금리 값 포함)

**Example:**
```python
get_korea_interest_rate.invoke({"months": 12})
```

### 3. `compare_korea_us_rates`

한국과 미국의 기준금리를 비교합니다.

**Parameters:**
- `months` (int): 조회할 기간 (개월 수, 기본값: 12)

**Returns:**
- 한미 금리 비교 분석 결과
  - 최신 금리 값
  - 금리 격차 (spread)
  - 금리 역전 여부
  - 추세 (상승/하락/보합)

**Example:**
```python
compare_korea_us_rates.invoke({"months": 12})
```

## 주요 클래스

### `InterestRateTool`

금리 조회를 위한 핵심 클래스입니다.

**Methods:**

#### `get_us_rates(rate_type, months=12, frequency="m")`
미국 금리 데이터 조회

**Parameters:**
- `rate_type` (str): "base_rate" or "10y_treasury"
- `months` (int): 조회 기간 (개월 수)
- `frequency` (str): 데이터 주기 (d: 일별, m: 월별, q: 분기별, a: 연간)

**Returns:**
- List[Dict]: `[{"date": "YYYY-MM-DD", "value": X.XX}, ...]`

#### `get_korea_rate(months=12)`
한국 기준금리 조회

**Parameters:**
- `months` (int): 조회 기간 (개월 수)

**Returns:**
- List[Dict]: `[{"date": "YYYYMM", "value": X.XX}, ...]`

#### `compare_rates(months=12)`
한미 금리 비교

**Parameters:**
- `months` (int): 조회 기간 (개월 수)

**Returns:**
- Dict: 비교 결과 (금리 격차, 역전 여부, 추세 등)

#### `format_rates(data, title)`
금리 데이터 포맷팅

**Parameters:**
- `data` (List[Dict]): 금리 데이터
- `title` (str): 제목

**Returns:**
- str: 포맷팅된 문자열

## 데이터 소스

### FRED (미국)
- **기준금리 (FEDFUNDS)**: 실효 연방기금 금리 (단기 정책 금리)
- **10년물 국채 (DGS10)**: 장기 시장 금리 (시장 벤치마크)
- 데이터 업데이트: 매일
- API 문서: https://fred.stlouisfed.org/docs/api/

### ECOS (한국)
- **기준금리 (722Y001)**: 한국은행 기준금리
- 데이터 업데이트: 금융통화위원회 회의 후
- API 문서: https://ecos.bok.or.kr/api/

## 테스트

테스트 노트북을 실행하세요:

```bash
jupyter notebook src/lab/test_interest_rate_tool.ipynb
```

또는 Python 스크립트로 테스트:

```python
python src/tools/interest_rate_tool.py
```

## 사용 예시

### 예시 1: 최근 금리 동향 확인
```python
from tools.interest_rate_tool import compare_korea_us_rates

result = compare_korea_us_rates.invoke({"months": 12})
print(result)
```

### 예시 2: 장기 추세 분석
```python
from tools.interest_rate_tool import InterestRateTool

rate_tool = InterestRateTool()

# 24개월 데이터 조회
us_data = rate_tool.get_us_rates("base_rate", months=24)
kr_data = rate_tool.get_korea_rate(months=24)

# 추세 분석
first_us = us_data[0]['value']
last_us = us_data[-1]['value']
change_us = last_us - first_us

print(f"미국 금리 변화: {change_us:+.2f}%p")
```

### 예시 3: 데이터 시각화
```python
import matplotlib.pyplot as plt
import pandas as pd
from tools.interest_rate_tool import InterestRateTool

rate_tool = InterestRateTool()

# 데이터 조회
us_data = rate_tool.get_us_rates("base_rate", months=24)
kr_data = rate_tool.get_korea_rate(months=24)

# DataFrame 변환
us_df = pd.DataFrame(us_data)
kr_df = pd.DataFrame(kr_data)

us_df['date'] = pd.to_datetime(us_df['date'])
kr_df['date'] = pd.to_datetime(kr_df['date'], format='%Y%m')

# 그래프 그리기
plt.figure(figsize=(12, 6))
plt.plot(us_df['date'], us_df['value'], label='미국 기준금리', marker='o')
plt.plot(kr_df['date'], kr_df['value'], label='한국 기준금리', marker='s')
plt.legend()
plt.title('한미 기준금리 추이')
plt.xlabel('날짜')
plt.ylabel('금리 (%)')
plt.grid(True)
plt.show()
```

## 주의사항

1. **API 키 필요**: FRED와 ECOS API 키가 모두 필요합니다.
2. **Rate Limit**:
   - FRED: 하루 120,000 요청
   - ECOS: 하루 10,000 요청
3. **데이터 업데이트 주기**:
   - FRED: 실시간
   - ECOS: 월 1회 (금통위 결정 후)
4. **네트워크 연결**: 인터넷 연결이 필요합니다.

## 트러블슈팅

### API 키 오류
```
ValueError: FRED_API_KEY가 설정되지 않았습니다.
```

**해결책:** `.env` 파일에 API 키를 추가하세요.

### ECOS API 응답 오류
```
ECOS API 응답 오류: {'RESULT': {...}}
```

**원인:**
- 잘못된 API 키
- Rate limit 초과
- 날짜 범위 오류

**해결책:**
1. API 키 확인
2. 요청 간격 조정
3. 날짜 범위 확인

### 데이터 없음
```
데이터 없음
```

**원인:**
- 주말/공휴일 (국채 수익률의 경우)
- 데이터가 아직 업데이트되지 않음

**해결책:**
- 더 긴 기간으로 조회
- 다른 날짜로 시도

## 금리 용어 설명

### 기준금리 (Base Rate)
중앙은행이 설정하는 정책 금리로, 시장 금리의 기준이 됩니다.

### 10년물 국채 수익률 (10Y Treasury)
10년 만기 국채의 수익률로, 장기 시장 금리의 벤치마크입니다.

### 금리 격차 (Rate Spread)
두 국가 간 금리 차이로, 자본 흐름을 예측하는 지표입니다.

### 금리 역전 (Rate Inversion)
일반적으로 낮아야 할 금리가 더 높은 경우를 의미합니다.
- 한미 금리 역전: 미국 금리 > 한국 금리
- 장단기 금리 역전: 단기 금리 > 장기 금리

## 라이센스

이 프로젝트는 RAG_COMMANDER 프로젝트의 일부입니다.

## 기여

버그 리포트나 기능 제안은 이슈로 등록해주세요.
