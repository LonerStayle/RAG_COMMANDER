from langgraph.graph import StateGraph, START, END
from agents.state.analysis_state import EconomicInsightState
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from utils.enum import LLMProfile
from langgraph.prebuilt import ToolNode
from prompts import PromptManager, PromptType
from utils.util import get_today_str
from agents.state.start_state import StartInput
from langchain_core.messages import SystemMessage, HumanMessage


@tool(parse_docstring=True)
def think_tool(reflection: str) -> str:
    """거시·정책(Economic Insight) 분석 중 **전략적 성찰(Reflection)**을 기록/보정하는 도구입니다.

    금리·거시지표·정책/규제 정보를 수집한 뒤, **시점 일치·단위 일관·인과 연결**을
    점검하고 다음 액션(추가 수집 vs 보고서 서술)을 결정합니다.
    Reflexion/Self-Refine류의 자기피드백 원리를 적용해, 결과의 일관성과 정확도를 높입니다.

    사용 시점:
        - 기준금리/체감금리/심리지수/GRDP 등 수치 확보 직후
        - LTV/DTI/분양가상한제/규제지역 등 **변경 시점** 확인 직후
        - impacts(price_pressure, demand_absorption) 설정 전
        - NARRATIVE 최종화 직전(모순/중복 제거)

    성찰(Reflection)에 반드시 포함할 항목:
        1. 발견(Findings): 기준금리 레벨·결정일, 체감금리 범위, 인플레이션/성장/심리 최신값,
           정책/규제 변경 요지(조문/보도자료·공고 링크)**와 함께** 요약
        2. 공백(Gaps): **결정일 누락**, 지역별 규제 여부 불명확, 심리지수 결측 등
        3. 품질(Quality): 퍼센트 단위, YYYY-MM-DD 날짜 일치, 출처 신뢰도(공식 1차 우선)
        4. 인과(Logic): "금리·정책 변화 → 수요/분양가 압력" 연결이 서술과 **같은 방향**인지 점검
        5. 결정(Next step):
           - 추가로 확보할 공식 문서/데이터는?
           - 충분하다면 impacts(상향/중립/하향; 양호/보통/부진) 값을 **근거**와 함께 고정

    도메인별 체크리스트(경제·정책):
        - 금리: base_rate **레벨/결정일** 일치? trend_12m(상승/보합/하락)과 서술 방향 일치?
        - 거시: 물가/성장/심리 값이 **서술에도 반영**되었는가?
        - 규제: LTV/DTI/상한제/규제지역 **적용 여부**와 **시점** 명확?
        - 결론: impacts.price_pressure & demand_absorption가 **rationales**와 모순 없는가?

    Args:
        reflection: 진행 상황, 수치·시점·출처 점검, 인과 평가, 다음 단계에 대한 상세 성찰.
            예) "기준금리 2.50%(2025-10-23). 주담대 3.2~3.6% 추정.
                LTV 완화 지역 확인 미흡 → 국토부 공고 필요.
                심리지수 보합 → price_pressure=중립, demand_absorption=보통 잠정."

    Returns:
        성찰 기록 확인 메시지(내부 로그용). 예: "Reflection recorded: <요약>"

    주의:
        - 숫자는 % 단위를 명시하고, 날짜는 YYYY-MM-DD로 표기하십시오.
        - 공식/1차 출처(한국은행·금융위·국토부·통계청 등)를 우선하십시오.
        - 과도한 단정은 피하고, 불확실성은 '미확인(사유)'로 명시하십시오.
    """
    return f"Reflection recorded: {reflection}"


output_key = EconomicInsightState.KEY.economic_insight_output
start_input_key = EconomicInsightState.KEY.start_input
rag_context_key = EconomicInsightState.KEY.rag_context
target_area_key = StartInput.KEY.target_area
messages_key = EconomicInsightState.KEY.messages

llm = ChatOpenAI(model=LLMProfile.ANALYSIS, temperature=0)
tool_list = [think_tool]
llm_with_tools = llm.bind_tools(tool_list)
tool_node = ToolNode(tool_list)

# 여기 수정 예정.. 
def retreiver(state: EconomicInsightState) -> EconomicInsightState:
    start_input = state[start_input_key]
    # start_input 로 RAG 사용했다 치고..
    return {rag_context_key: "rag_test"}


def analysis_setting(state: EconomicInsightState) -> EconomicInsightState:
    start_input = state[start_input_key]
    target_area = start_input[target_area_key]
    today_date = get_today_str()
    rag_context = state[rag_context_key]

    system_prompt = PromptManager(PromptType.ECONOMIC_INSIGHT_SYSTEM).get_prompt(
        target_area=target_area, date=today_date
    )
    humun_prompt = PromptManager(PromptType.ECONOMIC_INSIGHT_HUMAN).get_prompt(
        target_area=target_area,
        date=today_date,
        context=rag_context,
    )
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=humun_prompt),
    ]
    return {messages_key: messages}


def agent(state: EconomicInsightState) -> EconomicInsightState:
    messages = state.get(messages_key, [])
    response = llm_with_tools.invoke(messages)
    new_messages = messages + [response]
    new_state = {**state, messages_key: new_messages}
    new_state[output_key] = response.content
    return new_state


def router(state: EconomicInsightState):
    messages = state[messages_key]
    last_ai_message = messages[-1]
    if last_ai_message.tool_calls:
        return "tools"
    return "__end__"


retreiver_key = "retreiver"
analysis_setting_key = "analysis_setting"
tools_key = "tools"
agent_key = "agent"
graph_builder = StateGraph(EconomicInsightState)
graph_builder.add_node(retreiver_key, retreiver)
graph_builder.add_node(analysis_setting_key, analysis_setting)
graph_builder.add_node(tools_key, tool_node)
graph_builder.add_node(agent_key, agent)

graph_builder.add_edge(START, retreiver_key)
graph_builder.add_edge(retreiver_key, analysis_setting_key)
graph_builder.add_edge(analysis_setting_key, agent_key)

graph_builder.add_conditional_edges(agent_key, router, [tools_key, END])
graph_builder.add_edge(tools_key, agent_key)

economic_insight_graph = graph_builder.compile()
