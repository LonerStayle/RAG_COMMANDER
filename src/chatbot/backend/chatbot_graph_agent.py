"""
LangGraph 기반 Housing FAQ 챗봇 에이전트
"""
from typing import List, Dict, Any
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.documents import Document

import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root / "src"))

from chatbot_state import ChatbotState
from tools.rag.retriever.housing_faq_retriever import (
    housing_faq_retrieve,
    housing_rule_retrieve,
)
from tools.rag.retriever.policy_pdf_retriever import PolicyPDFRetriever
from utils.llm import LLMProfile


# Retriever 초기화
faq_retriever = housing_faq_retrieve()
rule_retriever = housing_rule_retrieve()
policy_retriever = PolicyPDFRetriever()
llm = LLMProfile.report_llm()


def build_query(
    message: str,
    target_area: str = "",
    main_type: str = "",
    total_units: str = "",
) -> str:
    """검색 쿼리 구성"""
    query_parts = [message]

    if target_area:
        query_parts.append(f"사업지: {target_area}")
    if main_type:
        query_parts.append(f"타입: {main_type}")
    if total_units:
        query_parts.append(f"세대수: {total_units}")

    return "\n".join(query_parts)


# 1. FAQ 검색 노드
def retrieve_faq(state: ChatbotState) -> ChatbotState:
    """FAQ 데이터 검색"""
    if not state.get("use_faq", True):
        return {"faq_context": [], "source_docs": []}

    query = build_query(
        state["user_message"],
        state.get("target_area", ""),
        state.get("main_type", ""),
        state.get("total_units", ""),
    )

    docs = faq_retriever.invoke(query)
    contexts = [f"[FAQ] {doc.page_content}" for doc in docs]

    return {"faq_context": contexts, "source_docs": docs}


# 2. 주택공급규칙 검색 노드
def retrieve_rule(state: ChatbotState) -> ChatbotState:
    """주택공급규칙 데이터 검색"""
    if not state.get("use_rule", True):
        return {"rule_context": [], "source_docs": []}

    query = build_query(
        state["user_message"],
        state.get("target_area", ""),
        state.get("main_type", ""),
        state.get("total_units", ""),
    )

    docs = rule_retriever.invoke(query)
    contexts = [f"[주택공급규칙] {doc.page_content}" for doc in docs]

    # Annotated reducer가 자동으로 병합
    return {"rule_context": contexts, "source_docs": docs}


# 3. 정책문서 검색 노드
def retrieve_policy(state: ChatbotState) -> ChatbotState:
    """정책문서 데이터 검색"""
    if not state.get("use_policy", True):
        return {"policy_context": [], "source_docs": []}

    query = build_query(
        state["user_message"],
        state.get("target_area", ""),
        state.get("main_type", ""),
        state.get("total_units", ""),
    )

    docs = policy_retriever.hybrid_search(query, k=5)
    contexts = []
    for doc in docs:
        policy_date = doc.metadata.get("policy_date", "날짜 미상")
        policy_title = doc.metadata.get("title", "제목 미상")
        contexts.append(
            f"[정책문서 - {policy_date} {policy_title}] {doc.page_content}"
        )

    # Annotated reducer가 자동으로 병합
    return {"policy_context": contexts, "source_docs": docs}


# 4. 프롬프트 구성 및 LLM 호출 노드
def generate_response(state: ChatbotState) -> ChatbotState:
    """LLM을 사용하여 응답 생성"""
    # 컨텍스트 합치기
    all_contexts = []
    all_contexts.extend(state.get("faq_context", []))
    all_contexts.extend(state.get("rule_context", []))
    all_contexts.extend(state.get("policy_context", []))

    context_text = "\n\n".join(all_contexts) if all_contexts else "관련 정보 없음"

    # 프롬프트 구성
    prompt = f"""당신은 주택 청약 및 분양 전문 상담사입니다.

## 사용자 정보
- 사업지: {state.get('target_area', '미제공')}
- 타입: {state.get('main_type', '미제공')}
- 세대수: {state.get('total_units', '미제공')}

## 참고 자료
{context_text}

## 사용자 질문
{state['user_message']}

## 응답 지침
1. 제공된 참고 자료를 바탕으로 정확하고 상세하게 답변하세요.
2. 사용자 정보를 고려하여 맞춤형 답변을 제공하세요.
3. 확실하지 않은 정보는 추측하지 말고 솔직하게 알려주세요.
4. 전문적이면서도 친근한 톤으로 답변하세요.
5. 필요시 출처를 명시하세요 (예: [FAQ], [주택공급규칙], [정책문서]).

답변:"""

    # LLM 호출
    messages = state.get("messages", [])
    messages.append(HumanMessage(content=prompt))

    response = llm.invoke(messages)
    answer = response.content

    # 메시지 업데이트
    new_messages = messages + [response]

    return {"response": answer, "messages": new_messages}


# 5. 소스 포맷팅 노드
def format_sources(state: ChatbotState) -> ChatbotState:
    """소스 문서를 포맷팅"""
    source_docs = state.get("source_docs", [])
    sources = []

    for i, doc in enumerate(source_docs[:10]):  # 상위 10개
        # 출처 정보 구성
        source_type = "알 수 없음"
        source_detail = ""
        file_name = ""
        page_info = ""

        # 파일명 추출
        if "source" in doc.metadata:
            source_file = doc.metadata["source"]
            file_name = source_file.split("/")[-1].split("\\")[-1]  # 파일명만 추출

            # 소스 타입 판별
            if "faq" in source_file.lower():
                source_type = "FAQ"
                source_detail = f"파일: {file_name}"
            elif "rule" in source_file.lower():
                source_type = "주택공급규칙"
                source_detail = f"파일: {file_name}"
            elif "policy" in source_file.lower() or doc.metadata.get("policy_date"):
                source_type = "정책문서"
                policy_date = doc.metadata.get("policy_date", "날짜 미상")
                policy_title = doc.metadata.get("title", file_name)
                policy_type = doc.metadata.get("policy_type", "")

                # 청크 정보
                chunk_id = doc.metadata.get("chunk_id", 0)
                total_chunks = doc.metadata.get("total_chunks", 0)

                # 페이지 정보 (있는 경우)
                page = doc.metadata.get("page", None)
                if page is not None:
                    page_info = f"페이지 {page + 1}"

                # 상세 정보 구성
                parts = [f"파일: {policy_title}"]
                if policy_date != "날짜 미상":
                    parts.append(f"날짜: {policy_date}")
                if policy_type:
                    parts.append(f"유형: {policy_type}")
                if page_info:
                    parts.append(page_info)
                if total_chunks > 0:
                    parts.append(f"구간: {chunk_id + 1}/{total_chunks}")

                source_detail = " | ".join(parts)

        sources.append(
            {
                "id": i + 1,
                "type": source_type,
                "detail": source_detail,
                "content": doc.page_content[:300] + "...",  # 미리보기
                "metadata": doc.metadata,
            }
        )

    return {"sources": sources}


# 그래프 구성
graph_builder = StateGraph(ChatbotState)

# 노드 추가
graph_builder.add_node("retrieve_faq", retrieve_faq)
graph_builder.add_node("retrieve_rule", retrieve_rule)
graph_builder.add_node("retrieve_policy", retrieve_policy)
graph_builder.add_node("generate_response", generate_response)
graph_builder.add_node("format_sources", format_sources)

# 엣지 설정
graph_builder.add_edge(START, "retrieve_faq")
graph_builder.add_edge(START, "retrieve_rule")
graph_builder.add_edge(START, "retrieve_policy")

graph_builder.add_edge("retrieve_faq", "generate_response")
graph_builder.add_edge("retrieve_rule", "generate_response")
graph_builder.add_edge("retrieve_policy", "generate_response")

graph_builder.add_edge("generate_response", "format_sources")
graph_builder.add_edge("format_sources", END)

# 그래프 컴파일
chatbot_graph = graph_builder.compile()
