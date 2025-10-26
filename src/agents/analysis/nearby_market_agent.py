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

@tool(parse_docstring=True)
def think_tool(reflection: str) -> str:
    """주변 시세·경쟁단지 비교 단계의 **전략적 성찰(Reflection)**을 기록/보정하는 도구입니다.

    1km 매매 실거래/시세와 2km 이내 최근 분양가·청약지표·계약조건을 수집한 뒤,
    **유사성 매칭(평형/연식)**, **단위/시점** 일관성, **분양가↔매매가 격차 해석**의 타당성을 점검하고
    다음 액션(추가 수집 vs 보고서 확정)을 결정합니다.

    사용 시점:
        - 국토부 실거래/KB·REB 시세 확보 직후(3.3㎡ 환산 포함)
        - 청약홈 경쟁률/1순위 마감·계약조건 확인 직후
        - relative_position·suggested_price_band 확정 직전

    성찰(반드시 포함):
        1) 발견(Findings): 매매 시세(평단가/월), 분양가(평단가/월), 경쟁률/1순위 여부, 계약조건(무이자/계약금), 브랜드·세대수 등.
        2) 공백(Gaps): 비교군 유사성 부족(연식/평형), 특정 단지 시세 출처 불명확, 청약 팝업 미확인 등.
        3) 품질(Quality): 3.3㎡ 환산·단위(만원/3.3㎡)·시점(YYYY-MM)·출처 매핑 정확성.
        4) 인과(Logic): “분양가 vs 매매가 격차 + 브랜드/입지 보정 → 흡수력/리스크” 해석의 방향이 서술과 일치하는가?
        5) 결정(Next step): 추가 확보할 **1차 자료**와 **구체 쿼리** 제시
           - 예) "rt.molit 단지별 2024-10~{date[:7]} 실거래 CSV",
                 "청약홈 경쟁률 팝업 캡처로 산식 확인",
                 "R-ONE 중위가격/주간 동향으로 국면 보정"

    도메인 체크리스트:
        - 유사성: 전용면적 ±5㎡, 연식 ±3~5년 내 비교인가?
        - 출처: 실거래는 **rt.molit**, 청약 지표는 **청약홈 팝업 산식**으로 확인했는가?
        - 격차 판단: presale_vs_sale_gap_pct 계산/부호/단위가 올바른가?
        - 제안 밴드: 보정 근거(브랜드/대단지/입지·교통/학군)가 투명하게 서술되었는가?

    Args:
        reflection: 현재 수집·해석 상태, 공백·품질 점검, 다음 단계에 대한 **구체적 성찰 서술**.
            예) "1km 매매 84㎡ 중위 평단 3,280(2025-08~09), A단지 분양 평단 3,420(2025-07, 1순위 마감).
                B분양 무이자/계약금 10%. 대상지 브랜드 약함→보수적 밴드 제안 필요."

    Returns:
        성찰 기록 확인 메시지(내부 로그용). 예: "Reflection recorded: <요약>"

    주의:
        - 수치에는 **단위/시점**을 반드시 포함하십시오(만원/3.3㎡, YYYY-MM).
        - 1차 공식 출처(국토부 실거래, REB 통계, 청약홈) 우선, 민간 시세는 보조로 병기하십시오.
        - 과도한 단정은 피하고, 불확실성은 '미확인(사유)'로 명시하십시오.
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

from langchain_openai import OpenAIEmbeddings
import json
from tools.rag.vectorstore import build_pgvector_store, TEST_COLLECTION_NAME
from perplexity import Perplexity
search_client = Perplexity()

def web_search(state: NearbyMarketState) -> NearbyMarketState:
    start_input = state[start_input_key]
    target_area = start_input[target_area_key]
    queries=[
        # 1) 1km 매매 실거래(유사 연식/평형; 3.3㎡ 환산 근거 포함)
        f"{target_area} 아파트 실거래가 단지별 전용 59 74 84 최근 6~12개월 거래월 층 가격 3.3㎡ 환산 근거 site:rt.molit.go.kr",

        # 2) (보조) 지자체 제공 실거래 뷰어(출처가 '국토부 실거래가'임을 명시)
        f"{target_area} 아파트 실거래 신고가격 단지별 전용면적 최근 거래월 site:land.seoul.go.kr 국토교통부 실거래가",

        # 3) 지역 시세/중위 참고(보조): REB 주간·월간 동향
        f"{target_area} 한국부동산원 아파트 매매 전세 가격 동향 중위 가격 지수 최근 월 site:reb.or.kr",

        # 4) 2km 최근 2년 분양 단지: 분양가(3.3㎡), 평형, 브랜드, 세대수
        f"{target_area} 최근 2년 분양 단지 분양가 3.3㎡ 전용 59 74 84 브랜드 세대수 site:applyhome.co.kr",

        # 5) 2km 최근 2년 청약 지표: 경쟁률, 1순위 마감 여부, 산식 팝업(공식)
        f"{target_area} 청약 경쟁률 1순위 마감 팝업 산식 최근 2년 site:applyhome.co.kr",

        # 6) 2km 최근 2년 계약조건: 중도금 무이자/계약금 비율·특약
        f"{target_area} 분양 공고 계약조건 중도금 무이자 계약금 비율 특약 최근 2년 site:applyhome.co.kr",

        # 7) 원문 PDF(있으면 가점): 분양공고/분양가 책정 근거
        f"{target_area} filetype:pdf 분양 공고 분양가 3.3㎡ 계약조건 경쟁률 site:applyhome.co.kr OR site:molit.go.kr",

        # 8) 도메인-무관 보완(정확한 역/단지 식별용 키워드)
        f"{target_area} 역세권 단지명 전용 84㎡ 최근 실거래 분양가 비교 3.3㎡"
    ]
    
    search_list = []
    for i in range(0, len(queries), 5):
        batch = queries[i:i+5]
        res = search_client.search.create(query=batch)
        search_list.append(res)
        return {**state, web_context_key: search_list}

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
    new_state[output_key] = response.content
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
