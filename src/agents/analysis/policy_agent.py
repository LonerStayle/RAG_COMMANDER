# 구조와 상태 정의
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field

# 프로젝트 내부 모듈
from agents.state.analysis_state import PolicyState
from agents.state.start_state import StartInput
from agents.state.policy_types import ReportCheck
from prompts import PromptManager, PromptType
from tools.context_to_csv import region_news_to_drive, netional_news_to_drive
from tools.estate_web_crawling_tool import collect_articles_result
from tools.rag.retriever.policy_pdf_retriever import PolicyPDFRetriever
from tools.rag.retriever.national_policy_retriever import national_policy_retrieve
from utils.llm import LLMProfile
from utils.util import get_today_str


@tool(parse_docstring=True)
def think_tool(reflection: str) -> str:
    """
    각 노드가 끝날 때마다 메모를 남기는 도구

    Args:
        reflection: 중간 추론 내용(체크리스트, 검증사항, 계획 등)

    Returns:
        추론이 기록되었다는 확인 메세지
    """
    return f"Reflection recorded: {reflection}"


llm = LLMProfile.analysis_llm()
tool_list = [think_tool]
llm_with_tools = llm.bind_tools(tool_list)
tool_node = ToolNode(tool_list)
evaluator_llm = llm.with_structured_output(ReportCheck)


output_key = PolicyState.KEY.policy_output
start_input_key = PolicyState.KEY.start_input
target_area_key = StartInput.KEY.target_area
policy_period_key = StartInput.KEY.policy_period
policy_count_key = StartInput.KEY.policy_count
policy_list_key = StartInput.KEY.policy_list
messages_key = PolicyState.KEY.messages
national_context_key = PolicyState.KEY.national_context
region_context_key = PolicyState.KEY.region_context
national_download_link_key = PolicyState.KEY.national_download_link
region_download_link_key = PolicyState.KEY.region_download_link
pdf_context_key = PolicyState.KEY.pdf_context
retry_count_key = PolicyState.KEY.retry_count

MAX_ITERATIONS = 3  # 재검색 최대 횟수, LLM이 전체 보고서를 작성 → 평가 → 재검색하는 전체 사이클당 1번씩 증가


def record_reflection(title: str, hint: str) -> None:
    """
    노드가 끝날 때마다 think_tool 도구를 호출하여 간단한 메모 남김
    """
    think_tool.invoke({"reflection": f"{title}\n{hint}"})


# 1. 자료수집
def nathional_news(state: PolicyState) -> PolicyState:
    docs = national_policy_retrieve()
    record_reflection("국가 뉴스 수집", "전국 정책 기사 정리")
    return {
        national_context_key: docs,
        national_download_link_key: netional_news_to_drive(docs),
    }


def national_news(state: PolicyState) -> PolicyState:
    docs = national_policy_retrieve()
    record_reflection("국가가 뉴스 수집", "전국 정책 기사 정리")
    return {
        national_context_key: docs,
        national_download_link_key: netional_news_to_drive(docs),
    }


def region_news(state: PolicyState) -> PolicyState:
    docs = collect_articles_result()
    record_reflection("지역 뉴스 수집", "지역 기사 묶음 확보")
    return {
        region_context_key: docs,
        region_download_link_key: region_news_to_drive(docs),
    }


def policy_pdf_retrieve(state: PolicyState) -> PolicyState:
    retriever = PolicyPDFRetriever()
    start_input = state.get(start_input_key, {})
    policy_period = start_input.get(StartInput.KEY.policy_period, "")
    policy_count = start_input.get(StartInput.KEY.policy_count, "")
    policy_list = start_input.get(StartInput.KEY.policy_list, "")
    target_area = start_input.get(StartInput.KEY.target_area, "")

    # 검색 쿼리 구성
    query_parts = []
    if target_area:
        query_parts.append(target_area)
    if policy_period:
        query_parts.append(policy_period)
    if policy_list:
        query_parts.append(policy_list)

    query = " ".join(query_parts) if query_parts else target_area or "정책"

    # policy_count를 k 값으로 사용 (기본값 3)
    try:
        k = policy_count if policy_count else 3
    except ValueError:
        k = 3

    docs = retriever.hybrid_search(query, k=k)
    record_reflection("PDF 검색", "정책 PDF 주요 문단 확보")
    return {pdf_context_key: docs}


# 프롬프트 세팅
def analysis_setting(state: PolicyState) -> PolicyState:
    start_input = state[start_input_key]
    system_prompt = PromptManager(PromptType.POLICY_SYSTEM).get_prompt()
    human_prompt = PromptManager(PromptType.POLICY_HUMAN).get_prompt(
        target_area=start_input[StartInput.KEY.target_area],
        date=get_today_str(),
        national_news_context=state[national_context_key],
        region_news_context=state[region_context_key],
        policy_period=start_input[StartInput.KEY.policy_period],
        policy_count=start_input[StartInput.KEY.policy_count],
        policy_list=start_input[StartInput.KEY.policy_list],
        main_type=start_input.get(StartInput.KEY.main_type, ""),
        total_units=start_input.get(StartInput.KEY.total_units, ""),
        pdf_context=state.get(pdf_context_key, ""),
    )
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_prompt),
    ]
    record_reflection("프롬프트 준비", "시스템/휴먼 프롬프트 설정")
    target_area_value = start_input[StartInput.KEY.target_area]
    return {
        messages_key: messages,
        "documents": state.get(pdf_context_key, []),
        "yaml_context": {
            "summary": PromptManager(PromptType.POLICY_COMPARISON_SUMMARY).get_prompt(
                target_area=target_area_value
            ),
            "segment_01": PromptManager(
                PromptType.POLICY_COMPARISON_SEGMENT_01
            ).get_prompt(),
            "segment_02": PromptManager(
                PromptType.POLICY_COMPARISON_SEGMENT_02
            ).get_prompt(),
            "segment_03": PromptManager(
                PromptType.POLICY_COMPARISON_SEGMENT_03
            ).get_prompt(target_area=target_area_value),
        },
        "iteration": 0,
    }


# 3. 보고서 작성 및 평가
def generate_initial_report(state: PolicyState) -> PolicyState:
    """
    자료 기반 보고서 초안 작성
    """
    messages = state[messages_key]
    response = llm_with_tools.invoke(
        messages
    )  # LLM에 메시지를 전달하여 보고서 초안을 생성
    new_messages = messages + [response]
    record_reflection("초안 작성", "자료 기반 첫 보고서 작성")
    return {
        messages_key: new_messages,
        "report_draft": response.content,
    }


def evaluate_report_completeness(state: PolicyState) -> PolicyState:
    """
    보고서 완성도 평가
    """
    draft = state["report_draft"]
    yaml_context = state.get("yaml_context", {})
    template = (
        "=== Segment 01 Template ===\n"
        f"{yaml_context.get('segment_01', '')}\n\n"
        "=== Segment 02 Template ===\n"
        f"{yaml_context.get('segment_02', '')}\n\n"
        "=== Segment 03 Template ===\n"
        f"{yaml_context.get('segment_03', '')}"
    )
    prompt = (
        "다음 *보고서 초안*이 *템플릿*을 모두 채웠는지 살펴보고, 부족한 항목과 검색어를 알려주세요.\n\n"
        f"[템플릿]\n{template}\n\n"
        f"[보고서 초안]\n{draft}"
    )
    check = evaluator_llm.invoke(prompt)
    record_reflection("완성도 평가", "필수 섹션 충족 여부 판단")
    return {"completeness_check": check}


def decide_next_step(state: PolicyState) -> str:
    """
    조건분기: 완성 시 종료, 부족하면 재검색
    """
    check = state[
        "completeness_check"
    ]  # 이전 단계에서 평가한 보고서 완성도 결과 가져옴옴
    if check.is_complete:
        return "__end__"
    if (
        state.get("iteration", 0) >= MAX_ITERATIONS
    ):  # 최대 반복 횟수에 도달하면 더 이상 재검색하지 않고 종료
        return "__end__"
    return "execute_retrieval"  # 보고서에 부족한 내용이 있으니 추가 자료를 검색하는 노드(execute_retrieval)로 이동
    #  "execute_retrieval" 는 다음 노드


# 4. 재검색과 수정
def execute_additional_retrieval(state: PolicyState) -> PolicyState:
    queries = state[
        "completeness_check"
    ].search_queries  # evaluate_report_completeness에서 나온 부족한 항목과 검색어 리스트
    retriever = PolicyPDFRetriever()
    new_docs = []
    for query in queries:
        new_docs.extend(
            retriever.hybrid_search(query, k=3)
        )  # 각 검색어로 관련 문서를 찾아서 new_docs 리스트에 추가
    added_docs = state["documents"] + new_docs
    record_reflection("추가 검색", "부족한 섹션 보강 자료 확보")
    return {
        "documents": added_docs,
        "iteration": state.get("iteration", 0) + 1,
    }


def revise_report(state: PolicyState) -> PolicyState:
    draft = state["report_draft"]
    check = state["completeness_check"]
    docs = state["documents"]
    prompt = (
        "이전 초안과 부족했던 내용을 참고해 보고서를 보완해 주세요.\n\n"
        f"[부족한 섹션]\n{check.missing_sections}\n\n"
        f"[필요한 정보]\n{check.missing_information}\n\n"
        f"[추가 자료]\n{docs}\n\n"
        f"[이전 초안]\n{draft}"
    )
    reply = llm_with_tools.invoke([HumanMessage(content=prompt)])
    record_reflection("보고서 수정", "추가 자료 반영")
    return {
        "report_draft": reply.content,  #  LLM이 생성한 수정된 보고서 내용을 report_draft 상태 키에 저장장. reply는 llm_with_tools.invoke()의 응답 객체이고, .content는 실제 텍스트 내용
        messages_key: state[messages_key]
        + [reply],  # 대화 로그에 수정된 보고서 내용을 추가
    }


def agent(state: PolicyState) -> PolicyState:
    """최종 결과 묶어 반환"""

    output = {
        "result": state["report_draft"],
        national_context_key: state[national_context_key],
        region_context_key: state[region_context_key],
        national_download_link_key: state[national_download_link_key],
        region_download_link_key: state[region_download_link_key],
    }
    record_reflection("최종 기록", "보고서와 참고링크 정리")
    return {output_key: output}


# def router(state: PolicyState):
#     messages = state[messages_key]
#     last_ai_message = messages[-1]
#     if last_ai_message.tool_calls:
#         return "tools"
#     return "__end__"


national_news_key = "national_news"
region_news_key = "region_news"
analysis_setting_key = "analysis_setting"
tools_key = "tools"
agent_key = "agent"
draft_key = "draft"
policy_pdf_retrieve_key = "policy_pdf_retrieve"
analysis_setting_key = "analysis_setting"
execute_retrieval_key = "execute_retrieval"
evaluate_completeness_key = "evaluate_completeness"
revise_report_key = "revise"


graph_builder = StateGraph(PolicyState)
graph_builder.add_node(national_news_key, national_news)
graph_builder.add_node(region_news_key, region_news)
graph_builder.add_node(policy_pdf_retrieve_key, policy_pdf_retrieve)
graph_builder.add_node(analysis_setting_key, analysis_setting)
graph_builder.add_node(draft_key, generate_initial_report)
graph_builder.add_node(execute_retrieval_key, execute_additional_retrieval)
graph_builder.add_node(evaluate_completeness_key, evaluate_report_completeness)
graph_builder.add_node(revise_report_key, revise_report)
graph_builder.add_node(tools_key, tool_node)
graph_builder.add_node(agent_key, agent)

graph_builder.add_edge(START, national_news_key)
graph_builder.add_edge(START, region_news_key)
graph_builder.add_edge(national_news_key, policy_pdf_retrieve_key)
graph_builder.add_edge(region_news_key, policy_pdf_retrieve_key)
graph_builder.add_edge(policy_pdf_retrieve_key, analysis_setting_key)
graph_builder.add_edge(analysis_setting_key, draft_key)
graph_builder.add_edge(draft_key, evaluate_completeness_key)
graph_builder.add_conditional_edges(
    evaluate_completeness_key,  # 완성도 평가
    decide_next_step,  # 완성 시 종료, 부족하면 재검색
    [execute_retrieval_key, END],  # 보고서가 불완전 하면 자료 추가 검색색
)

graph_builder.add_edge(execute_retrieval_key, revise_report_key)
graph_builder.add_edge(revise_report_key, evaluate_completeness_key)
graph_builder.add_edge(evaluate_completeness_key, agent_key)

policy_graph = graph_builder.compile()
