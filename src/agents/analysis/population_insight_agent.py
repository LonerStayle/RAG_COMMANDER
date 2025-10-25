from langgraph.graph import StateGraph, START, END 
from agents.state.analysis_state import PopulationInsightState
from langchain_core.tools import tool
from agents.state.start_state import StartInput
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from utils.util import get_today_str
from utils.enum import LLMProfile
from langchain_openai import ChatOpenAI
from prompts import PromptManager, PromptType
from langgraph.prebuilt import ToolNode    




@tool(parse_docstring=True)
def think_tool(reflection: str) -> str:
    """인구·가구·이동(Population Insight) 분석의 **전략적 성찰(Reflection)**을 기록/보정하는 도구입니다.

    연령구조/가구형태/순이동 시계열을 수집한 뒤,
    **시점·단위·정의**의 일관성과 “수치→수요층(소형/중대형)→흡수력” **인과 연결**을 점검하고
    다음 액션(추가 수집 vs 보고서 확정)을 결정합니다.

    사용 시점:
        - KOSIS/SGIS에서 연령·가구 지표 취득 직후(참조연도·단위 확인)
        - 행안부 주민등록 인구이동(오픈API/월별) 집계 직후(전입/전출/순이동률)
        - derived_demand(소형/중대형 신호)·narrative_md 확정 직전

    성찰(반드시 포함):
        1) 발견(Findings): 연령 비중·중위연령, 1·2·3인+ 가구 비중, 순이동률/최근 12개월 추세 등 **구체 수치+출처**.
        2) 공백(Gaps): 특정 연도/월 결측, 가구형태 최신연도 부재(총조사 주기), 순이동률 계산 불가 등.
        3) 품질(Quality): 단위(%/명/가구, YYYY 또는 YYYY-MM), 정의(가구/주민등록 기준)·참조연도 일치 여부.
        4) 인과(Logic): 연령·가구·이동 변화가 **수요층 신호**와 같은 방향으로 해석되었는가?
        5) 결정(Next step): 추가로 확보할 1차 자료와 **구체 쿼리** 제시
           - 예) "KOSIS 가구형태 시군구 시계열", 
                 "행안부 인구이동 API: {target_area} 2023-01~{date} 월별",
                 "SGIS 인구피라미드 {target_area} {date[:4]} 중위연령"

    도메인 체크리스트:
        - KOSIS/통계청 지표의 **참조연도·주기**(총조사 0/5년 단위) 반영?  # 가구형태는 주기성 주의
        - 주민등록 인구이동은 **월 단위**이며 외국인 제외?  # 행안부/통계설명 참고
        - derived_demand의 신호(강함/보통/약함)가 rationales와 **모순 없음**?

    Args:
        reflection: 현재 수집·해석 상태, 공백·품질 점검, 다음 단계에 대한 **구체적 성찰 서술**.
            예) "1인 가구 36%(2025), 20–34세 27% 유지, 순유입 +0.6%p(최근 12개월). 
                가구형태 최신연도 공백 → 총조사 2025년치만 사용. 
                소형 수요 신호=강함, 중대형=보통 잠정."

    Returns:
        성찰 기록 확인 메시지(내부 로그용). 예: "Reflection recorded: <요약>"

    주의:
        - 수치에는 **단위/시점**을 반드시 포함하십시오.
        - 1차 공식 출처(KOSIS/통계청/행안부/KRIHS)를 우선하십시오.
        - 과도한 단정은 피하고, 불확실성은 '미확인(사유)'로 명시하십시오.
    """
    return f"Reflection recorded: {reflection}"    
    
output_key = PopulationInsightState.KEY.population_insight_output
start_input_key = PopulationInsightState.KEY.start_input
rag_context_key = PopulationInsightState.KEY.rag_context
messages_key = PopulationInsightState.KEY.messages
target_area_key = StartInput.KEY.target_area


llm = ChatOpenAI(model=LLMProfile.ANALYSIS, temperature=0)
tool_list = [think_tool]
llm_with_tools = llm.bind_tools(tool_list)
tool_node = ToolNode(tool_list)

# 여기 수정 예정.. 
def retreiver(state: PopulationInsightState) -> PopulationInsightState:
    start_input = state[start_input_key]
    # start_input 로 RAG 사용했다 치고..
    return {rag_context_key: "rag_test"}


def analysis(state: PopulationInsightState) -> PopulationInsightState:
    start_input = state[start_input_key]
    target_area = start_input[target_area_key]
    today_date = get_today_str()
    rag_context = state[rag_context_key]

    system_prompt = PromptManager(PromptType.POPULATION_INSIGHT_SYSTEM).get_prompt(
        target_area=target_area, date=today_date
    )
    humun_prompt = PromptManager(PromptType.POPULATION_INSIGHT_HUMAN).get_prompt(
        target_area=target_area,
        date=today_date,
        context=rag_context,
    )
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=humun_prompt),
    ]
    return {messages_key: messages}


def agent(state: PopulationInsightState) -> PopulationInsightState:    
    messages = state.get(messages_key, [])
    response = llm_with_tools.invoke(messages)
    new_messages = messages + [response]
    new_state = {**state, messages_key: new_messages}
    new_state[output_key] = response.content
    return new_state

def router(state: PopulationInsightState):
    messages = state[messages_key]
    last_ai_message = messages[-1]
    if last_ai_message.tool_calls:        
        return "tools"
    return "__end__"


retreiver_key = "retreiver"
analysis_setting_key = "analysis_setting"
tools_key = "tools"
agent_key = "agent"
graph_builder = StateGraph(PopulationInsightState)
graph_builder.add_node(retreiver_key, retreiver)
graph_builder.add_node(analysis_setting_key, analysis)
graph_builder.add_node(tools_key, tool_node)
graph_builder.add_node(agent_key, agent)

graph_builder.add_edge(START, retreiver_key)
graph_builder.add_edge(retreiver_key, analysis_setting_key)
graph_builder.add_edge(analysis_setting_key, agent_key)

graph_builder.add_conditional_edges(agent_key, router, [tools_key, END])
graph_builder.add_edge(tools_key, agent_key)

population_insight_graph = graph_builder.compile()
