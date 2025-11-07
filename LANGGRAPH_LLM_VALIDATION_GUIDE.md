# LangGraph 공식 문서 기반 LLM 검증 노드 구현 가이드

## LangGraph의 조건부 엣지(Conditional Edges) 개념

LangGraph에서 조건부 엣지는 **현재 상태를 기반으로 다음 노드를 동적으로 결정**합니다.

### 기본 구조
```python
def routing_function(state: State) -> str:
    # 상태를 확인하고 다음 노드 이름을 반환
    if 조건:
        return "node_name_1"
    return "node_name_2"

graph.add_conditional_edges(
    "source_node",           # 출발 노드
    routing_function,        # 라우팅 함수
    {
        "node_name_1": "target_node_1",  # 반환값에 따른 목적지
        "node_name_2": "target_node_2"
    }
)
```

## 구현 방법

### 1. State에 필드 추가

**파일**: `src/agents/state/analysis_state.py`

**수정 내용**:
```python
@attach_auto_keys
class PolicyState(TypedDict):
    start_input: dict
    policy_output: dict
    national_context: Optional[str]
    region_context: Optional[str]
    national_download_link: Optional[str]
    region_download_link: Optional[str]
    pdf_context: Optional[str]
    retry_count: Optional[int]
    retrieved_docs: Optional[List]  # 검색된 문서 리스트
    is_valid_retrieval: Optional[bool]  # LLM 검증 결과
    validation_reason: Optional[str]  # 검증 이유
    messages: Annotated[list[AnyMessage], add_messages]
    my_tool: str
```

### 2. policy_pdf_retrieve 노드 구현

**파일**: `src/agents/analysis/policy_agent.py`

**구현**:
```python
def policy_pdf_retrieve(state: PolicyState) -> PolicyState:
    """
    정책 PDF 문서에서 관련 내용을 검색합니다.
    """
    start_input = state.get(start_input_key, {})
    target_area = start_input.get(target_area_key, "")
    retry_count = state.get(retry_count_key, 0)
    
    # 검색 쿼리 생성
    query = f"{target_area} 부동산 정책 규제"
    
    # 재검색인 경우 쿼리 확장
    if retry_count > 0:
        query = f"{query} 상세 내용 추가 정보"
    
    # Retriever 초기화 및 검색
    retriever = PolicyPDFRetriever()
    docs = retriever.hybrid_search(query, k=10)
    
    # 검색 결과를 텍스트로 변환
    pdf_context_parts = []
    for doc in docs:
        pdf_context_parts.append(doc.page_content)
    
    pdf_context = "\n\n".join(pdf_context_parts)
    
    return {
        pdf_context_key: pdf_context,
        retry_count_key: retry_count + 1,
        "retrieved_docs": docs
    }
```

### 3. validate_retrieval_with_llm 노드 구현 (핵심)

**파일**: `src/agents/analysis/policy_agent.py`

**구현**:
```python
def validate_retrieval_with_llm(state: PolicyState) -> PolicyState:
    """
    LLM을 사용하여 검색 결과가 프롬프트와 맞는지 검증합니다.
    LangGraph의 노드는 State를 받아서 State를 반환합니다.
    """
    start_input = state.get(start_input_key, {})
    target_area = start_input.get(target_area_key, "")
    pdf_context = state.get(pdf_context_key, "")
    retrieved_docs = state.get("retrieved_docs", [])
    
    # 검색 결과가 없으면 재검색 필요
    if not pdf_context or len(pdf_context.strip()) < 50:
        return {
            "is_valid_retrieval": False,
            "validation_reason": "검색 결과가 없거나 너무 짧음"
        }
    
    # LLM에게 검증 요청
    validation_prompt = f"""
당신은 부동산 정책 분석을 위한 검색 결과 검증 전문가입니다.

[분석 목표]
- 대상 지역: {target_area}
- 목적: 부동산 정책이 해당 지역에 미치는 영향 분석

[검색된 PDF 내용]
{pdf_context[:2000]}

[검증 체크리스트]
1. 지역 관련성: 검색 내용이 "{target_area}"와 직접적으로 관련이 있는가?
2. 정책 관련성: 부동산 정책(규제지역, LTV, DSR, 대출한도 등) 내용이 포함되어 있는가?
3. 정보 충분성: 분석에 필요한 핵심 정보(수치, 날짜, 규정 등)가 포함되어 있는가?

[답변 형식]
반드시 다음 형식으로만 답변하세요:
- "적절함" (모든 체크리스트를 만족하는 경우)
- "부적절함: [부족한 항목 명시]" (체크리스트를 만족하지 못하는 경우)

예시:
- "적절함"
- "부적절함: 지역 관련성 부족, {target_area}에 대한 직접적인 언급이 없음"
"""
    
    # LLM 호출
    validation_response = llm.invoke(validation_prompt)
    validation_result = validation_response.content.strip()
    
    # 결과 파싱
    is_valid = "적절함" in validation_result
    
    return {
        "is_valid_retrieval": is_valid,
        "validation_reason": validation_result
    }
```

### 4. should_retry_retrieval 라우팅 함수 구현

**파일**: `src/agents/analysis/policy_agent.py`

**구현**:
```python
def should_retry_retrieval(state: PolicyState) -> str:
    """
    LangGraph 조건부 엣지의 라우팅 함수입니다.
    State를 받아서 다음 노드 이름을 문자열로 반환합니다.
    
    Returns:
        "retry": 재검색 필요
        "continue": 계속 진행
    """
    is_valid = state.get("is_valid_retrieval", False)
    retry_count = state.get(retry_count_key, 0)
    MAX_RETRIES = 3
    
    # 검증 실패하고 최대 재시도 횟수 미만이면 재검색
    if not is_valid and retry_count < MAX_RETRIES:
        return "retry"
    
    return "continue"
```

### 5. 워크플로우 수정

**파일**: `src/agents/analysis/policy_agent.py`

**그래프 빌더 부분 수정**:
```python
# 노드 키 정의
national_news_key = "national_news"
region_news_key = "region_news"
policy_pdf_retrieve_key = "policy_pdf_retrieve"
validate_retrieval_key = "validate_retrieval_with_llm"
analysis_setting_key = "analysis_setting"
tools_key = "tools"
agent_key = "agent"

# 그래프 빌더 생성
graph_builder = StateGraph(PolicyState)

# 노드 추가
graph_builder.add_node(national_news_key, national_news)
graph_builder.add_node(region_news_key, region_news)
graph_builder.add_node(policy_pdf_retrieve_key, policy_pdf_retrieve)
graph_builder.add_node(validate_retrieval_key, validate_retrieval_with_llm)
graph_builder.add_node(analysis_setting_key, analysis_setting)
graph_builder.add_node(tools_key, tool_node)
graph_builder.add_node(agent_key, agent)

# 엣지 추가
graph_builder.add_edge(START, national_news_key)
graph_builder.add_edge(START, region_news_key)
graph_builder.add_edge(START, policy_pdf_retrieve_key)

# national_news와 region_news가 완료되면 검증 노드로 (병렬 처리)
graph_builder.add_edge(national_news_key, validate_retrieval_key)
graph_builder.add_edge(region_news_key, validate_retrieval_key)
graph_builder.add_edge(policy_pdf_retrieve_key, validate_retrieval_key)

# 조건부 엣지: 검증 결과에 따라 재검색 또는 계속 진행
graph_builder.add_conditional_edges(
    validate_retrieval_key,           # 출발 노드
    should_retry_retrieval,           # 라우팅 함수
    {
        "retry": policy_pdf_retrieve_key,    # 재검색
        "continue": analysis_setting_key     # 계속 진행
    }
)

# 분석 설정 후 에이전트 실행
graph_builder.add_edge(analysis_setting_key, agent_key)

# 에이전트가 도구를 사용하면 도구 노드로, 아니면 종료
graph_builder.add_conditional_edges(agent_key, router, [tools_key, END])
graph_builder.add_edge(tools_key, agent_key)

# 그래프 컴파일
policy_graph = graph_builder.compile()
```

## 전체 워크플로우 구조

```
START
  ├─→ national_news ──┐
  ├─→ region_news ────┼─→ validate_retrieval_with_llm
  └─→ policy_pdf_retrieve ──┘         │
                                       │ (조건부 엣지)
                    ┌──────────────────┴──────────────────┐
                    │                                      │
              [부적절함]                            [적절함]
                    │                                      │
                    ↓                                      ↓
         policy_pdf_retrieve (재검색)          analysis_setting
                    │                                      │
                    └──────────────┬──────────────────────┘
                                   ↓
                              agent
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
              [tool 필요]                    [완료]
                    │                             │
                    ↓                             ↓
                  tools ───────────────→        END
                    │
                    └─→ agent (반복)
```

## LangGraph 공식 문서의 핵심 원칙

1. **노드는 State를 받아서 State를 반환**
   - 함수 시그니처: `def node_function(state: State) -> State`
   - State는 딕셔너리 형태로 반환 (부분 업데이트 가능)

2. **조건부 엣지는 라우팅 함수가 문자열 반환**
   - 함수 시그니처: `def routing_function(state: State) -> str`
   - 반환된 문자열이 다음 노드 이름

3. **State는 TypedDict로 정의**
   - Optional 필드는 None 가능
   - Annotated를 사용하여 메시지 리스트 관리

4. **노드는 독립적으로 실행 가능**
   - 각 노드는 순수 함수처럼 동작
   - State만으로 모든 정보 전달

## 주의사항

1. **State 업데이트**: 부분 업데이트 가능 (전체 State 반환 불필요)
   ```python
   return {"is_valid_retrieval": True}  # 부분 업데이트
   ```

2. **조건부 엣지의 반환값**: 반드시 딕셔너리의 키와 일치해야 함
   ```python
   # 라우팅 함수가 "retry" 반환 → "retry" 키가 있어야 함
   graph_builder.add_conditional_edges(
       "node",
       routing_func,
       {
           "retry": "retry_node",      # "retry" 반환시 이동
           "continue": "continue_node" # "continue" 반환시 이동
       }
   )
   ```

3. **LLM 호출**: 검증 노드에서 LLM을 호출하므로 비용 발생
   - 간결한 프롬프트 사용 권장
   - 재시도 횟수 제한 필요

4. **에러 처리**: LLM 호출 실패시 기본값 설정
   ```python
   try:
       validation_response = llm.invoke(validation_prompt)
   except Exception as e:
       return {"is_valid_retrieval": False, "validation_reason": f"에러: {e}"}
   ```

## 구현 순서

1. `PolicyState`에 필드 추가 (`analysis_state.py`)
2. `policy_pdf_retrieve` 함수 완성
3. `validate_retrieval_with_llm` 함수 추가 (LLM 검증)
4. `should_retry_retrieval` 함수 추가 (라우팅 함수)
5. 그래프에 노드와 조건부 엣지 추가


