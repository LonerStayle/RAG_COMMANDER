from langgraph.graph import StateGraph, START, END 
from agents.state.analysis_state import LocationInsightState
from agents.state.start_state import StartInput
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from utils.util import get_today_str
from utils.enum import LLMProfile
from langchain_openai import ChatOpenAI
from prompts import PromptManager, PromptType
from langgraph.prebuilt import ToolNode
    

@tool(parse_docstring=True)
def think_tool(reflection: str) -> str:
    """입지분석(Location Insight) 진행 중 **전략적 성찰(Reflection)**을 기록/보정하는 도구입니다.

    이 도구는 각 **검색/POI 조회/경로계산** 직후 잠시 멈춰, 현재 발견·공백·품질·다음단계를
    체계적으로 점검하기 위해 사용합니다. 결과는 보고서 품질(정확성/일관성/재현성)을 높이기
    위한 내부 메모이자, 다음 액션을 결정하는 근거로 활용됩니다.

    사용 시점:
        - 지도/POI/학교/역/버스/도보경로/개발계획 등 툴 호출 직후
        - '도보 10분' 판정/거리·시간 단위 확정 직전
        - 개발호재의 **실현성(단계/ETA)** 판단 전
        - 최종 NARRATIVE 작성 직전(중복·모순 검사)

    성찰(Reflection)에 반드시 포함할 항목:
        1. 발견(Findings): 수집한 **구체 수치**(분/미터/개수)와 **출처**(공식 우선)
        2. 공백(Gaps): 아직 **미확인 핵심값**(예: 통학로 위험요소, ETA 근거 문서, 혐오시설 거리)
        3. 품질(Quality): 단위/시점 표기 여부, '도보 10분' 판정의 일관성, 출처의 신뢰도
        4. 결정(Next step): 
           - 추가 수집이 필요한가? (예: 지자체 고시문서·교통계획 원문)
           - 아니면 보고서 서술로 넘어가도 충분한가?
        5. 서술 적합성: 수치→서술 인과 연결이 자연스러운가(과장·단정 금지)?

    도메인별 체크리스트(입지):
        - 교육: 초등학교 **실보행 기준 분/미터** 명시? 통학로 위험요소 기록?
        - 교통: 역 **도보 10분 이내** 판정 근거 명확? 버스 노선 다변성 요약?
        - 편의: 반경 1km **핵심 POI 개수** 최소 집계 완료?
        - 환경: 공원/혐오시설 **거리·영향도** 수치화? 판단 어휘(낮음/중간/높음) 일관?
        - 호재: **단기 실현성** 높은 것만 유지(단계/ETA/공식문서 링크 확인)

    Args:
        reflection: 현재 진행 상황, 발견·공백·품질평가, 다음 단계에 대한 **구체적 성찰 서술**.
            예) "정자초 560m/7분 확보. 정자역 9분. 정자공원 450m. 
                지자체 고시문서로 GTX 관련 ETA 확정 필요. 혐오시설 거리 미확인 → 추가 검색."

    Returns:
        성찰이 기록되었음을 나타내는 메시지(내부 로그용). 예: "Reflection recorded: <요약>"

    주의:
        - 수치는 **단위/시점**을 반드시 포함하십시오(분/미터/YYYY-MM).
        - 미확인은 '미확인(사유)'로 명시하고, **구체 쿼리**까지 제안하십시오.
        - 공식/1차 출처를 우선 채택하십시오.
    """
    return f"Reflection recorded: {reflection}"
    
    
output_key = LocationInsightState.KEY.location_insight_output
start_input_key = LocationInsightState.KEY.start_input
rag_context_key = LocationInsightState.KEY.rag_context
messages_key = LocationInsightState.KEY.messages
target_area_key = StartInput.KEY.target_area
scale_key = StartInput.KEY.scale
total_units_key = StartInput.KEY.total_units


llm = ChatOpenAI(model=LLMProfile.ANALYSIS, temperature=0)
tool_list = [think_tool]
llm_with_tools = llm.bind_tools(tool_list)
tool_node = ToolNode(tool_list)

# 여기 수정 예정.. 
def retreiver(state: LocationInsightState) -> LocationInsightState:
    start_input = state[start_input_key]
    # start_input 로 RAG 사용했다 치고..
    return {rag_context_key: "rag_test"}


def analysis_setting(state: LocationInsightState) -> LocationInsightState:
    start_input = state[start_input_key]
    target_area = start_input[target_area_key]
    scale = start_input[scale_key]
    total_units = start_input[total_units_key]
    today_date = get_today_str()
    rag_context = state[rag_context_key]

    system_prompt = PromptManager(PromptType.LOCATION_INSIGHT_SYSTEM).get_prompt(
        target_area=target_area,scale = scale, total_units=total_units, date=today_date
    )
    humun_prompt = PromptManager(PromptType.LOCATION_INSIGHT_HUMAN).get_prompt(
        target_area=target_area,
        date=today_date,
        context=rag_context,
    )
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=humun_prompt),
    ]
    return {messages_key: messages }


def agent(state: LocationInsightState) -> LocationInsightState:    
    messages = state.get(messages_key, [])
    response = llm_with_tools.invoke(messages)
    new_messages = messages + [response]
    new_state = {**state, messages_key: new_messages}
    new_state[output_key] = response.content
    return new_state



def router(state: LocationInsightState):
    messages = state[messages_key]
    last_ai_message = messages[-1]
    if last_ai_message.tool_calls:
        return "tools"
    return "__end__"


retreiver_key = "retreiver"
analysis_setting_key = "analysis_setting"
tools_key = "tools"
agent_key = "agent"
graph_builder = StateGraph(LocationInsightState)
graph_builder.add_node(retreiver_key, retreiver)
graph_builder.add_node(analysis_setting_key, analysis_setting)
graph_builder.add_node(tools_key, tool_node)
graph_builder.add_node(agent_key, agent)

graph_builder.add_edge(START, retreiver_key)
graph_builder.add_edge(retreiver_key, analysis_setting_key)
graph_builder.add_edge(analysis_setting_key, agent_key)

graph_builder.add_conditional_edges(agent_key, router, [tools_key, END])
graph_builder.add_edge(tools_key, agent_key)

location_insight_graph = graph_builder.compile()