# LLM 기반 검색 결과 검증 노드 구현 가이드

## 목적
LangGraph 에이전트가 검색 결과가 프롬프트와 맞는지 LLM으로 판단하게 하는 노드 추가

## 구현 위치
**파일**: `src/agents/analysis/policy_agent.py`

## 추가할 노드와 함수

### 1. policy_pdf_retrieve 노드
**역할**: PDF에서 검색 수행

**위치**: `policy_agent.py`의 `policy_pdf_retrieve` 함수 완성

**구현 예시**:
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
        "retrieved_docs": docs  # 검증 노드에서 사용
    }
```

### 2. validate_retrieval_with_llm 노드 (핵심)
**역할**: LLM이 검색 결과가 적절한지 판단

**위치**: `policy_agent.py`에 새 함수 추가

**구현 예시**:
```python
def validate_retrieval_with_llm(state: PolicyState) -> PolicyState:
    """
    LLM을 사용하여 검색 결과가 프롬프트와 맞는지 검증합니다.
    """
    start_input = state.get(start_input_key, {})
    target_area = start_input.get(target_area_key, "")
    pdf_context = state.get(pdf_context_key, "")
    retrieved_docs = state.get("retrieved_docs", [])
    
    # 검색 결과가 없으면 재검색 필요
    if not pdf_context or len(pdf_context.strip()) < 50:
        state["is_valid_retrieval"] = False
        state["validation_reason"] = "검색 결과가 없거나 너무 짧음"
        return state
    
    # LLM에게 검증 요청
    validation_prompt = f"""
다음은 "{target_area}" 지역의 부동산 정책 분석을 위해 검색한 PDF 문서 내용입니다.

[검색된 내용]
{pdf_context[:2000]}

[검증 기준]
1. 검색된 내용이 "{target_area}" 지역과 관련이 있는가?
2. 검색된 내용이 부동산 정책(규제, LTV, DSR, 대출한도 등)과 관련이 있는가?
3. 검색된 내용이 분석에 충분한 정보를 제공하는가?

위 기준을 바탕으로 검색 결과가 적절한지 판단해주세요.
답변 형식: "적절함" 또는 "부적절함: 이유"
"""
    
    # LLM 호출
    validation_response = llm.invoke(validation_prompt)
    validation_result = validation_response.content.strip()
    
    # 결과 파싱
    is_valid = "적절함" in validation_result
    
    state["is_valid_retrieval"] = is_valid
    state["validation_reason"] = validation_result
    
    return state
```

### 3. should_retry_retrieval 함수
**역할**: 재검색 여부 결정 (LLM 판단 결과 기반)

**위치**: `policy_agent.py`에 새 함수 추가

**구현 예시**:
```python
def should_retry_retrieval(state: PolicyState) -> str:
    """
    LLM 판단 결과를 바탕으로 재검색이 필요한지 결정합니다.
    
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

### 4. 워크플로우 수정
**위치**: `policy_agent.py`의 그래프 빌더 부분

**추가할 노드**:
```python
policy_pdf_retrieve_key = "policy_pdf_retrieve"
validate_retrieval_key = "validate_retrieval_with_llm"

# 노드 추가
graph_builder.add_node(policy_pdf_retrieve_key, policy_pdf_retrieve)
graph_builder.add_node(validate_retrieval_key, validate_retrieval_with_llm)

# 엣지 추가
graph_builder.add_edge(START, policy_pdf_retrieve_key)
graph_builder.add_edge(policy_pdf_retrieve_key, validate_retrieval_key)

# 조건부 엣지 (재검색 여부 판단)
graph_builder.add_conditional_edges(
    validate_retrieval_key,
    should_retry_retrieval,
    {
        "retry": policy_pdf_retrieve_key,
        "continue": analysis_setting_key
    }
)
```

## 전체 워크플로우

```
START 
  → national_news
  → region_news
  → policy_pdf_retrieve (신규: PDF 검색)
  → validate_retrieval_with_llm (신규: LLM 검증)
  → [재검색 필요시] → policy_pdf_retrieve
  → [적절함] → analysis_setting
  → agent
  → [tool 필요시] → tools → agent
  → END
```

## 검증 프롬프트 개선 예시

더 정확한 검증을 위한 프롬프트 예시:

```python
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
4. 프롬프트 적합성: 제공된 프롬프트 형식에 맞는 내용인가?

[답변 형식]
반드시 다음 형식으로 답변하세요:
- 적절함: 모든 체크리스트를 만족하는 경우
- 부적절함: [부족한 항목 명시]

예시:
- "적절함"
- "부적절함: 지역 관련성 부족, {target_area}에 대한 직접적인 언급이 없음"
"""
```

## State에 추가할 필드

`src/agents/state/analysis_state.py`의 `PolicyState`에 추가:

```python
@attach_auto_keys
class PolicyState(TypedDict):
    start_input: dict
    policy_output: dict
    national_context: Optional[str]
    region_context: Optional[str]
    pdf_context: Optional[str]
    retry_count: Optional[int]
    retrieved_docs: Optional[List]  # 검증 노드에서 사용
    is_valid_retrieval: Optional[bool]  # LLM 검증 결과
    validation_reason: Optional[str]  # 검증 이유
    messages: Annotated[list[AnyMessage], add_messages]
    my_tool: str
```

## 구현 순서

1. **State 수정**: `PolicyState`에 필드 추가
2. **policy_pdf_retrieve 함수 완성**: 검색 로직 구현
3. **validate_retrieval_with_llm 함수 추가**: LLM 검증 로직 구현
4. **should_retry_retrieval 함수 추가**: 재검색 판단 로직 구현
5. **워크플로우 수정**: 그래프에 노드와 엣지 추가

## 주의사항

1. **LLM 호출 비용**: 검증 노드에서 LLM을 호출하므로 비용이 발생합니다
2. **재시도 횟수**: MAX_RETRIES를 적절히 설정 (예: 3번)
3. **검증 프롬프트**: 명확한 기준을 제시하여 일관된 판단이 나오도록 해야 합니다
4. **에러 처리**: LLM 호출 실패시 기본값(재검색)으로 처리


