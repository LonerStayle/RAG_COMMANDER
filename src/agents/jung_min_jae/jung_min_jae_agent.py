from langgraph.graph import StateGraph, START, END 
from langchain_core.tools import tool
from langchain.chat_models import init_chat_model
from utils.llm import LLMProfile
from langgraph.prebuilt import ToolNode
from prompts import PromptManager, PromptType
from utils.util import get_today_str
from agents.state.start_state import StartInput
from langchain_core.messages import SystemMessage, HumanMessage
from agents.state.jung_min_jae_state import JungMinJaeState


@tool(parse_docstring=True)
def think_tool(reflection: str) -> str:
    """협회 대표가 최종 보고서를 완성하기 전에 **자체 검증(자아성찰)**을 수행하는 도구입니다.

    Args:
        reflection (str): 방금 작성한 보고서 초안 또는 섹션 내용.

    Returns:
        str: 점검 결과 및 개선 제안 Markdown 텍스트.

    점검 기준:
        1. 서술이 근거 중심인가? (수치·분석 결과 기반)
        2. 독자가 이해할 수 있는가? (용어 난이도·논리 흐름)
        3. 보고서 간 톤앤매너가 일관적인가?
        4. 리스크 요인을 명확히 짚었는가?
        5. 결론이 과도하게 단정적이지 않은가?

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
messages_key = JungMinJaeState.KEY.messages

llm = LLMProfile.repoert_llm()
tool_list = [think_tool]
llm_with_tools = llm.bind_tools(tool_list)
tool_node = ToolNode(tool_list)

# 여기 수정 예정.. 
def retreiver(state: JungMinJaeState) -> JungMinJaeState:
    start_input = state[start_input_key]
    # start_input 로 RAG 사용했다 치고..
    return {rag_context_key: "rag_test"}


def report_setting(state: JungMinJaeState) -> JungMinJaeState:
    analysis_outputs = state[analysis_outputs_key]
    start_input = state[start_input_key]
    rag_context = state[rag_context_key]

    system_prompt = PromptManager(PromptType.JUNG_MIN_JAE_SYSTEM).get_prompt(
        date=get_today_str(), 
    )
    humun_prompt = PromptManager(PromptType.JUNG_MIN_JAE_HUMAN).get_prompt(
        start_input = start_input,
        analysis_outputs=analysis_outputs,
        rag_context=rag_context,
    )
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=humun_prompt),
    ]
    return {messages_key: messages }


def agent(state: JungMinJaeState) -> JungMinJaeState:
    messages = state.get(messages_key, [])
    response = llm_with_tools.invoke(messages)

    new_state = {**state, messages_key: messages + [response]}
    new_state[final_report_key] = response.content
    return new_state


def router(state: JungMinJaeState):
    messages = state[messages_key]
    last_ai_message = messages[-1]
    if last_ai_message.tool_calls:
        return "tools"
    return "__end__"


retreiver_key = "retreiver"
draft_reporting_key = "draft_reporting"
tools_key = "tools"
agent_key = "agent"
graph_builder = StateGraph(JungMinJaeState)
graph_builder.add_node(retreiver_key, retreiver)
graph_builder.add_node(draft_reporting_key, report_setting)
graph_builder.add_node(tools_key, tool_node)
graph_builder.add_node(agent_key, agent)

graph_builder.add_edge(START, retreiver_key)
graph_builder.add_edge(retreiver_key, draft_reporting_key)
graph_builder.add_edge(draft_reporting_key, agent_key)

graph_builder.add_conditional_edges(agent_key, router, [tools_key, END])
graph_builder.add_edge(tools_key, agent_key)

report_graph = graph_builder.compile()

    