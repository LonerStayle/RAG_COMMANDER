from langgraph.graph import StateGraph, START, END
from agents.state.analysis_state import PolicyState
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from utils.llm import LLMProfile
from langgraph.prebuilt import ToolNode
from prompts import PromptManager, PromptType
from utils.util import get_today_str
from agents.state.start_state import StartInput
from langchain_core.messages import SystemMessage, HumanMessage


@tool(parse_docstring=False)
def think_tool(reflection: str) -> str:
    """
    [역할]
    당신은 부동산 관련 정책 정리 전문가의 내부 반성·점검(Reflection) 담당자입니다.
    최종 보고서에 들어갈 본문(Markdown)을 쓰기 직전에, 데이터 품질·시계열 해석·핵심 수치·리스크·보고서용 한 줄 메시지를 짧고 구조적으로 요약해 think_tool에 기록합니다.
    이 반성문은 내부용이며, 최종 보고서에 직접 노출되지 않습니다.
    
    [언제 호출할 것인지]
    - 데이터 수집/정제 → 핵심 수치 산출 → 시계열 해석을 마친 직후 1회 호출(필수)
    - 추가 데이터로 추세가 바뀌면 갱신 시마다 1회 재호출(선택)
    
    [강력 지시]
    - 해당 지역에 관련된 내용만 기록
    - 허상 가정,출처 수치 금지 
    - 다음 단계(보고서 에이전트)가 바로 쓸 수 있는 한 줄 핵심 메시지 포함
    
    [나쁜 예]
    - “인구가 늘어난 듯함. 분위기 좋음.”(수치·기간·단위·근거 없음)
    - “인근 해운대도 좋다.”(대상 지역 외 서술)
    - “향후 집값 상승 확실.”(근거 없는 단정)
    
    [검증 체크리스트]
    - 정량 수치가 어긋난 것 이 있는가? 
    - GPT가 시계열 판단하기에 좋은 형식으로 되어있는가?
    - 잘못된 내용은 없는가?    
    """
    return f"Reflection recorded: {reflection}"

output_key = PolicyState.KEY.policy_output
start_input_key = PolicyState.KEY.start_input
target_area_key = StartInput.KEY.target_area
messages_key = PolicyState.KEY.messages
national_context_key = PolicyState.KEY.national_context
region_context_key = PolicyState.KEY.region_context

llm = LLMProfile.analysis_llm()
tool_list = [think_tool]
llm_with_tools = llm.bind_tools(tool_list)
tool_node = ToolNode(tool_list)

from tools.rag.retriever.national_policy_retriever import national_policy_retrieve
def national_news(state: PolicyState) -> PolicyState:
    return {national_context_key: national_policy_retrieve()}

from tools.estate_web_crawling_tool import collect_articles_result
def region_news(state: PolicyState) -> PolicyState:    
    return {region_context_key:collect_articles_result()}

def analysis_setting(state: PolicyState) -> PolicyState:
    start_input = state[start_input_key]
    target_area = start_input[target_area_key]
    national_context = state[national_context_key]
    region_context = state[region_context_key]

    system_prompt = PromptManager(PromptType.POLICY_SYSTEM).get_prompt()
    humun_prompt = PromptManager(PromptType.POLICY_HUMAN).get_prompt(
        target_area=target_area,
        date=get_today_str(),
        national_news_context = national_context,
        region_news_context = region_context
    )
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=humun_prompt),
    ]
    return {messages_key: messages}


def agent(state: PolicyState) -> PolicyState:
    messages = state.get(messages_key, [])
    response = llm_with_tools.invoke(messages)
    new_messages = messages + [response]
    new_state = {**state, messages_key: new_messages}
    new_state[output_key] = {
        "result": response.content,
        national_context_key: state[national_context_key],
        region_context_key: state[region_context_key]
    }
    return new_state


def router(state: PolicyState):
    messages = state[messages_key]
    last_ai_message = messages[-1]
    if last_ai_message.tool_calls:
        return "tools"
    return "__end__"


national_news_key = "national_news"
region_news_key = "region_news"
analysis_setting_key = "analysis_setting"
tools_key = "tools"
agent_key = "agent"
graph_builder = StateGraph(PolicyState)
graph_builder.add_node(national_news_key, national_news)
graph_builder.add_node(region_news_key, region_news)
graph_builder.add_node(analysis_setting_key, analysis_setting)
graph_builder.add_node(tools_key, tool_node)
graph_builder.add_node(agent_key, agent)

graph_builder.add_edge(START, national_news_key)
graph_builder.add_edge(START, region_news_key)

graph_builder.add_edge(national_news_key, analysis_setting_key)
graph_builder.add_edge(region_news_key, analysis_setting_key)

graph_builder.add_edge(analysis_setting_key, agent_key)
graph_builder.add_conditional_edges(agent_key, router, [tools_key, END])
graph_builder.add_edge(tools_key, agent_key)

policy_graph = graph_builder.compile()
