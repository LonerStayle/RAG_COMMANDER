from langgraph.graph import StateGraph, START, END
from langchain_core.tools import tool
from utils.llm import LLMProfile
from prompts import PromptManager, PromptType
from utils.util import get_today_str
from langchain_core.messages import SystemMessage, HumanMessage
from agents.state.jung_min_jae_state import JungMinJaeState
from agents.state.start_state import StartInput
from agents.state.analysis_state import AnalysisGraphState


@tool(parse_docstring=True)
def think_tool(reflection: str) -> str:
    """협회 대표가 최종 보고서를 완성하기 전에 **자체 검증(자아성찰)**을 수행하는 도구입니다.

    Args:
        reflection (str): 방금 작성한 보고서 초안 또는 섹션 내용.

    Returns:
        str: 점검 결과 및 개선 제안 Markdown 텍스트.

    점검 기준:
        1. 각 페이지 시작부에 핵심 인사이트의 근거가 명확한가
        2. 근거로 사용할 데이터를 명확하게 표기했는가
        3. 근거로 사용할 데이터는 정확한 데이터인가
        4. 비슷한 스펙의 주변 매매아파트, 분양아파트와 요인비교분석에 현재의 정책, 경제지표, 공급과 수요, 미분양 분석, 인구 분석 등의 내용을 종합해서 분양성과 분양가를 평가 했는가

    위 기준에 따라 **보완 의견**을 Markdown 형식으로 작성하고,
    필요 시 개선 제안이나 문장 수정 예시도 함께 포함한다.
    """
    feedback = f"""
    🔍 **자체 검증 결과 요약**
    - 내용 요약: {reflection[:200]}...
    - 평가: 논리 흐름은 자연스럽지만 일부 문장은 근거가 약합니다.
    - 개선 제안:
        1. 주요 수치나 데이터 출처를 명시하세요.
        2. 결론부의 단정 표현(예: '확실히', '반드시')을 완화하세요.
        3. 리스크 서술 시 완화 조건(금리/정책/공급 등)을 병기하세요.
    """
    return feedback.strip()


analysis_outputs_key = JungMinJaeState.KEY.analysis_outputs
start_input_key = JungMinJaeState.KEY.start_input
rag_context_key = JungMinJaeState.KEY.rag_context
final_report_key = JungMinJaeState.KEY.final_report
segment_key = JungMinJaeState.KEY.segment
segment_buffers_key = JungMinJaeState.KEY.segment_buffers
messages_key = JungMinJaeState.KEY.messages
review_feedback_key = JungMinJaeState.KEY.review_feedback

location_insight_output_key = "location_insight"
policy_output_key = "policy_output"
housing_faq_output_key = "housing_faq"
nearby_market_output_key = "nearby_market"
population_insight_output_key = "population_insight"
supply_demand_output_key = "supply_demand"
unsold_insight_output_key = "unsold_insight"

target_area_key = StartInput.KEY.target_area
scale_key = StartInput.KEY.scale
total_units_key = StartInput.KEY.total_units

llm = LLMProfile.report_llm()


def segment_directive(seg: int) -> str:
    if seg == 1:
        return PromptManager(PromptType.JUNG_MIN_JAE_SEGMENT_01).get_prompt()
    if seg == 2:
        return PromptManager(PromptType.JUNG_MIN_JAE_SEGMENT_02).get_prompt()
    return PromptManager(PromptType.JUNG_MIN_JAE_SEGMENT_03).get_prompt()


dev_llm = LLMProfile.dev_llm()


def prev_segment_context(state: JungMinJaeState) -> str:
    seg = state.get(segment_key, 1)
    if seg <= 1:
        return

    summary_prompt = PromptManager(PromptType.JUNG_MIN_JAE_SUMMARY).get_prompt()
    buffers = state.get(segment_buffers_key, {})
    segments = list(buffers.values())
    response = dev_llm.invoke(
        [SystemMessage(content=summary_prompt), HumanMessage(content=str(segments))]
    )

    return f"# 이전 세그먼트 요약/맥락\n{response.content}"


# 여기 수정 예정..
def retreiver(state: JungMinJaeState) -> JungMinJaeState:
    start_input = state[start_input_key]
    # start_input 로 RAG 사용했다 치고..
    return {rag_context_key: "rag_test"}


def reporting(state: JungMinJaeState) -> JungMinJaeState:
    seg = state.get(segment_key, 1)
    analysis_outputs = state[analysis_outputs_key]
    start_input = state[start_input_key]

    target_area = start_input[target_area_key]
    scale = start_input[scale_key]
    total_units = start_input[total_units_key]

    location_insight = analysis_outputs[location_insight_output_key]
    policy = analysis_outputs[policy_output_key]
    housing_faq = analysis_outputs[housing_faq_output_key]
    nearby_market = analysis_outputs[nearby_market_output_key]
    population_insight = analysis_outputs[population_insight_output_key]
    supply_demand = analysis_outputs[supply_demand_output_key]
    unsold_insight = analysis_outputs[unsold_insight_output_key]

    directive = segment_directive(seg)
    prev_context = prev_segment_context(state)

    system_prompt = PromptManager(PromptType.JUNG_MIN_JAE_SYSTEM).get_prompt(
        date=get_today_str()
    )

    human_prompt = PromptManager(PromptType.JUNG_MIN_JAE_HUMAN).get_prompt(
        target_area=target_area,
        scale=scale,
        total_units=total_units,
        housing_faq=housing_faq,
        location_insight=location_insight,
        policy=policy,
        supply_demand=supply_demand,
        unsold_insight=unsold_insight,
        population_insight=population_insight,
        nearby_market=nearby_market,
    )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"{directive}\n\n{prev_context}\n\n{human_prompt}"),
    ]
    return {messages_key: messages}


def agent(state: JungMinJaeState) -> JungMinJaeState:
    messages = state.get(messages_key, [])
    seg = state.get(segment_key, 1)
    buffers = dict(state.get(segment_buffers_key, {}))

    response = llm.invoke(messages)
    buffers[f"seg{seg}"] = response.content

    new_state = {**state}
    new_state[messages_key] = messages + [response]
    new_state[segment_buffers_key] = buffers
    if seg <= 3:
        new_state[segment_key] = seg + 1
    return new_state


def review_with_think(state: JungMinJaeState) -> JungMinJaeState:
    final_text = state.get(final_report_key, "")
    feedback = think_tool.invoke({"reflection": final_text})
    improved = f"{final_text}\n\n---\n\n## 검토 노트(자동 성찰)\n{feedback}"
    return {review_feedback_key: feedback, final_report_key: improved}


def finalize_merge(state: JungMinJaeState) -> JungMinJaeState:
    """세그먼트 병합 후, 목차/헤더/중복 간단 정리(필요 시)."""
    buffers = state.get(segment_buffers_key, {})
    merged = "\n\n".join(
        [
            buffers.get("seg1", ""),
            buffers.get("seg2", ""),
            buffers.get("seg3", ""),
        ]
    )
    # (선택) 간단한 후처리: 헤더 중복/수평선 정리 등
    merged = merged.replace("\n\n--\n\n", "\n\n---\n\n")  # 구분선 통일
    return {final_report_key: merged}


def router(state: JungMinJaeState):
    seg = state.get(segment_key, 1)

    if seg <= 3:
        return "reporting"

    # seg == 4 (3 초과)
    if not state.get(final_report_key):
        return "finalize_merge"

    if not state.get(review_feedback_key):
        return "review_with_think"

    return "__end__"


retreiver_key = "retreiver"
reporting_key = "reporting"
agent_key = "agent"
finalize_key = "finalize_merge"
review_key = "review_with_think"

graph_builder = StateGraph(JungMinJaeState)
graph_builder.add_node(retreiver_key, retreiver)
graph_builder.add_node(reporting_key, reporting)
graph_builder.add_node(agent_key, agent)
graph_builder.add_node(finalize_key, finalize_merge)
graph_builder.add_node(review_key, review_with_think)

graph_builder.add_edge(START, retreiver_key)
graph_builder.add_edge(retreiver_key, reporting_key)
graph_builder.add_edge(reporting_key, agent_key)

graph_builder.add_conditional_edges(
    agent_key,
    router,
    [reporting_key, finalize_key, review_key, END],
)
graph_builder.add_edge(finalize_key, review_key)
graph_builder.add_edge(review_key, END)


report_graph = graph_builder.compile()
