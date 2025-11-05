from langgraph.graph import StateGraph, START, END 
from agents.state.analysis_state import NearbyMarketState
from agents.state.start_state import StartInput
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage
from utils.util import get_today_str
from utils.llm import LLMProfile
from langchain_openai import ChatOpenAI
from prompts import PromptManager, PromptType
from langgraph.prebuilt import ToolNode    
from langchain_core.tools import tool
import json
from tools.real_time_sale_search_api_tool import get_real_estate_price

@tool(parse_docstring=False)
def think_tool(reflection: str) -> str:
    """
    [역할]
    당신은 사업지 주변 매매 아파트, 분양 아파트들 각각의 시세와 입지를 정리하는 전문가의 내부 반성·점검(Reflection) 담당자입니다.
    최종 보고서에 들어갈 본문(Markdown)을 쓰기 직전에, 데이터 품질·핵심 수치·리스크·보고서용 한 줄 메시지를 짧고 구조적으로 요약해 think_tool에 기록합니다. 이 반성문은 내부용이며, 최종 보고서에 직접 노출되지 않습니다.

    [언제 호출할 것인지]
    - Node 하나의 결과를 받고 tool을 사용하기 전에 호출(필수)
    - 데이터 수집/정제 → 핵심 수치 산출 → 시계열 해석을 마친 직후 1회 호출(필수)
    - 추가 데이터로 최신 데이터로 바뀌면 갱신 시마다 1회 재호출(선택)
    

    [강력 지시]
    - 해당 지역에 관련된 내용만 기록
    - 허상 가정,출처 수치 금지
    - 다음 단계(보고서 에이전트)가 바로 쓸 수 있는 한 줄 핵심 메시지 포함

    [나쁜 예]
    - “경제가 좋아진듯함. 분위기 좋음.”(수치·기간·단위·근거 없음)
    - “인근 해운대의 입지는 이렇다~”(대상 지역 외 서술)
    - “향후 집값 상승 확실.”(근거 없는 단정)

    [검증 체크리스트]
    - 정량 수치가 어긋난 것이 있는가?
    - GPT가 시계열 판단하기에 좋은 형식으로 되어있는가?
    - 잘못된 내용은 없는가?
    """
    return f"Reflection recorded: {reflection}"
        
output_key = NearbyMarketState.KEY.nearby_market_output
start_input_key = NearbyMarketState.KEY.start_input
web_context_key = NearbyMarketState.KEY.web_context
messages_key = NearbyMarketState.KEY.messages
target_area_key = StartInput.KEY.target_area


llm = LLMProfile.analysis_llm()
tool_list = [think_tool]
llm_with_tools = llm.bind_tools(tool_list)
tool_node = ToolNode(tool_list)


from perplexity import Perplexity
search_client = Perplexity()

def web_search(state: NearbyMarketState) -> NearbyMarketState:
    start_input = state[start_input_key]
    target_area = start_input[target_area_key]
    queries=[
        # 1) 1km 매매 실거래(유사 연식/평형; 3.3㎡ 환산 근거 포함)
        # f"{target_area} 아파트 실거래가 단지별 전용 59 74 84 최근 6~12개월 거래월 층 가격 3.3㎡ 환산 근거 site:rt.molit.go.kr",

        # # 2) (보조) 지자체 제공 실거래 뷰어(출처가 '국토부 실거래가'임을 명시)
        # f"{target_area} 아파트 실거래 신고가격 단지별 전용면적 최근 거래월 site:land.seoul.go.kr 국토교통부 실거래가",

        # # 3) 지역 시세/중위 참고(보조): REB 주간·월간 동향
        # f"{target_area} 한국부동산원 아파트 매매 전세 가격 동향 중위 가격 지수 최근 월 site:reb.or.kr",

        # # 4) 2km 최근 2년 분양 단지: 분양가(3.3㎡), 평형, 브랜드, 세대수
        # f"{target_area} 최근 2년 분양 단지 분양가 3.3㎡ 전용 59 74 84 브랜드 세대수 site:applyhome.co.kr",

        # # 5) 2km 최근 2년 청약 지표: 경쟁률, 1순위 마감 여부, 산식 팝업(공식)
        # f"{target_area} 청약 경쟁률 1순위 마감 팝업 산식 최근 2년 site:applyhome.co.kr",

        # # 6) 2km 최근 2년 계약조건: 중도금 무이자/계약금 비율·특약
        # f"{target_area} 분양 공고 계약조건 중도금 무이자 계약금 비율 특약 최근 2년 site:applyhome.co.kr",

        # # 7) 원문 PDF(있으면 가점): 분양공고/분양가 책정 근거
        # f"{target_area} filetype:pdf 분양 공고 분양가 3.3㎡ 계약조건 경쟁률 site:applyhome.co.kr OR site:molit.go.kr",

        # # 8) 도메인-무관 보완(정확한 역/단지 식별용 키워드)
        # f"{target_area} 역세권 단지명 전용 84㎡ 최근 실거래 분양가 비교 3.3㎡"
    ]
    
    search_list = []
    for i in range(0, len(queries), 5):
        batch = queries[i:i+5]
        res = search_client.search.create(query=batch)
        search_list.append(res)
        return {**state, web_context_key: search_list}
    return {web_context_key : ""}

def analysis_setting(state: NearbyMarketState) -> NearbyMarketState:    
    start_input = state[start_input_key]
    target_area = start_input[target_area_key]
    web_context = state[web_context_key]

    system_prompt = PromptManager(PromptType.NEARBY_MARKET_SYSTEM).get_prompt(
        date=get_today_str()
    )
    humun_prompt = PromptManager(PromptType.NEARBY_MARKET_HUMAN).get_prompt(
        target_area=target_area, 
        web_context=web_context,
    )
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=humun_prompt),
    ]
    return {messages_key: messages}


def agent(state: NearbyMarketState) -> NearbyMarketState:    
    messages = state.get(messages_key, [])
    response = llm_with_tools.invoke(messages)
    new_messages = messages + [response]
    new_state = {**state, messages_key: new_messages}
    new_state[output_key] = {
        "result": response.content,
        web_context_key: state[web_context_key]
    }
    return new_state



def router(state: NearbyMarketState):
    messages = state[messages_key]
    last_ai_message = messages[-1]
    if last_ai_message.tool_calls:        
        return "tools"
    return "__end__"


web_search_key = "web_search"
analysis_key = "analysis"
tools_key = "tools"
agent_key = "agent"
graph_builder = StateGraph(NearbyMarketState)
graph_builder.add_node(web_context_key, web_search)
graph_builder.add_node(analysis_key, analysis_setting)
graph_builder.add_node(tools_key, tool_node)
graph_builder.add_node(agent_key, agent)

graph_builder.add_edge(START, web_context_key)
graph_builder.add_edge(web_context_key, analysis_key)
graph_builder.add_edge(analysis_key, agent_key)

graph_builder.add_conditional_edges(agent_key, router, [tools_key, END])
graph_builder.add_edge(tools_key, agent_key)

nearby_market_graph = graph_builder.compile()
