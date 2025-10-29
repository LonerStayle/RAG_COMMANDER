from langgraph.graph import StateGraph, START, END 
from agents.state.analysis_state import SupplyDemandState
from langchain_core.tools import tool
from agents.state.start_state import StartInput
from langchain_core.messages import SystemMessage, HumanMessage,ToolMessage
from utils.util import get_today_str
from utils.llm import LLMProfile
from langchain.chat_models import init_chat_model
from prompts import PromptManager, PromptType
from langgraph.prebuilt import ToolNode    



@tool(parse_docstring=True)
def think_tool(reflection: str) -> str:
    """수급(Supply·Demand) 분석 단계에서 **전략적 성찰(Reflection)**을 기록/보정하는 도구입니다.

    각 통계(분양/입주/청약/미분양/보급률)를 수집·정리한 뒤,
    시점·단위·산식의 **일관성**과 해석의 **인과 구조**를 점검하고,
    추가 수집이 필요한 공백을 정의하여 다음 액션을 결정합니다.

    사용 시점:
        - 국토부 미분양/메타 확인 직후(월·지역·준공 전/후 구분 점검)
        - 청약홈 경쟁률/1순위 마감률 확보 직후(산출식·유형 주석) 
        - 보급률/가구지표 취득 직후(기준연도·정의 일치 검토)
        - diagnosis(균형/과잉/수요우위)·narrative_md 확정 직전

    성찰(반드시 포함):
        1) 발견(Findings): 기간·단위가 명확한 시계열 요약(예: 미분양 2025-09 9.9만호),
           청약 평균 배수/1순위 마감 여부, 입주 집중 구간 등 **구체 수치+출처**.
        2) 공백(Gaps): 예) 시군구 레벨 미분양 결측, 평형별 경쟁률 미확보, 입주 캘린더 부재 등.
        3) 품질(Quality): 단위(%/호/세대/배수)·기간(YYYY-MM/분기)·산식(평균 vs 가중) 표기 여부.
        4) 인과(Logic): 공급/청약/미분양의 **방향성 일치 여부**(예: 공급↑ + 청약↓ → 미분양↑) 점검.
        5) 결정(Next step): 추가로 확보할 공식 1차 자료와 구체 쿼리 제시
           - 예) "stat.molit 미분양 시군구별 2023-2025 다운로드", 
                 "청약홈 당해/기타 구분 경쟁률 팝업 확인",
                 "KOSIS 보급률 2021~2023 시도별 시계열"

    도메인 체크리스트:
        - 미분양: 국토부 통계 **월·지역·준공 전/후** 구분 반영? 메타의 작성기관·주기 준수?  # stat.molit 메타 참고
        - 청약: 경쟁률 산출 방식/모수 차이 주석? 1순위 마감률과 동행 해석?                   # 청약홈 참고
        - 보급률: 정의(주택수/일반가구수×100)·기준연도 일치?                               # KOSIS 정의 참고
        - 진단: diagnosis(균형/과잉/수요우위)가 rationales와 모순 없는가?

    Args:
        reflection: 현재 수집·해석 상태, 공백·품질 점검, 다음 단계에 대한 **구체적 성찰 서술**.
            예) "2022~2025 입주 증가 구간과 2024~2025 청약 배수 하락 동행. 
                2025-09 미분양 증가세 확인(시군구 세부 미확보) → stat.molit 상세 조회 필요. 
                보급률 102% 인근, diagnosis=균형~공급우위 경계 잠정."

    Returns:
        성찰 기록 확인 메시지(내부 로그용). 예: "Reflection recorded: <요약>"

    주의:
        - 수치에는 **단위/기간**을 반드시 포함하십시오(호/세대/배수/%, YYYY-MM).
        - 청약 경쟁률은 **공식 페이지 기준**으로만 인용하고 산식 차이를 주석 처리하십시오.
        - 1차 공식 출처(국토부·청약홈·KOSIS·한국부동산원)를 우선하십시오.
    """
    return f"Reflection recorded: {reflection}"    
    
output_key = SupplyDemandState.KEY.supply_demand_output
start_input_key = SupplyDemandState.KEY.start_input
web_context_key = SupplyDemandState.KEY.web_context
rag_context_key = SupplyDemandState.KEY.rag_context
messages_key = SupplyDemandState.KEY.messages
target_area_key = StartInput.KEY.target_area

llm = LLMProfile.analysis_llm()
tool_list = [think_tool]
llm_with_tools = llm.bind_tools(tool_list)
tool_node = ToolNode(tool_list)

from perplexity import Perplexity
search_client = Perplexity()


def web_search(state: SupplyDemandState) -> SupplyDemandState:
    start_input = state[start_input_key]
    target_area = start_input[target_area_key]
    queries=[
        # ── 공급(인허가/분양계획/착공 보조)
        f"{target_area} 주택건설 인허가 실적 월별 시계열 site:stat.molit.go.kr",
        f"{target_area} 주택건설 착공 실적 월별 시계열 site:stat.molit.go.kr",

        # ── 입주(준공·입주 물량)
        f"{target_area} 주택건설 준공 실적 월별 시계열 site:stat.molit.go.kr",
        f"{target_area} 아파트 입주 예정 물량 최근 36개월 site:applyhome.co.kr",

        # ── 청약(경쟁률/1순위 마감)
        f"{target_area} 아파트 청약 경쟁률 최근 12~24개월 1순위 마감 여부 site:applyhome.co.kr",
        f"{target_area} 청약 경쟁률 팝업 산식 조회 site:applyhome.co.kr",

        # ── 미분양(총/준공후)
        f"{target_area} 미분양 주택 현황 월별 시군구 총량 준공후 구분 site:stat.molit.go.kr",

        # ── 보조지표: 지역 시세/심리(상대 국면 파악)
        f"{target_area} 한국부동산원 주간 또는 월간 아파트 가격 동향 지수 site:reb.or.kr",

        # ── 보급률(가능 시)
        f"{target_area} 주택보급률 지표 시도 또는 시군구 최근 연도 site:kosis.kr",

        # ── 통계 메타(PDF 원문, 정의/주기/작성체계)
        f"미분양주택현황보고 통계 정보 작성주기 작성체계 파일type:pdf site:stat.molit.go.kr OR site:kostat.go.kr",
        f"주택건설실적통계 인허가 착공 준공 통계정보 보고서 파일type:pdf site:stat.molit.go.kr OR site:k-stat.go.kr"
    ]
    
    search_list = []
    for i in range(0, len(queries), 5):
        batch = queries[i:i+5]
        res = search_client.search.create(query=batch)
        search_list.append(res)
        return {**state, web_context_key: search_list}


def retreive(state: SupplyDemandState) -> SupplyDemandState:
    # embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

    # start_input = state[start_input_key]

    # # start_input 로 RAG 사용했다 치고..
    # vector_store = build_pgvector_store(
    #     collection_name=TEST_COLLECTION_NAME, embedding_model=embeddings
    # )
    # retriever = vector_store.as_retriever(search_kwargs={"k": 1})

    # query = json.dumps(start_input, ensure_ascii=False)
    # result = retriever.invoke(query)
    result = "test"
    return {rag_context_key: result}


def analysis_setting(state: SupplyDemandState) -> SupplyDemandState:
    start_input = state[start_input_key]
    target_area = start_input[target_area_key]
    
    web_context = state[web_context_key]
    rag_context = state[rag_context_key]

    system_prompt = PromptManager(PromptType.SUPPLY_DEMAND_SYSTEM).get_prompt(
        date=get_today_str()
    )
    humun_prompt = PromptManager(PromptType.SUPPLY_DEMAND_HUMAN).get_prompt(
        target_area=target_area,
        web_context=web_context,
        rag_context=rag_context,
    )
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=humun_prompt),
    ]
    return {messages_key: messages }


def agent(state: SupplyDemandState) -> SupplyDemandState:    
    messages = state.get(messages_key, [])
    response = llm_with_tools.invoke(messages)
    new_messages = messages + [response]
    new_state = {**state, messages_key: new_messages}
    new_state[output_key] = response.content
    return new_state

def router(state: SupplyDemandState):
    messages = state[messages_key]
    last_ai_message = messages[-1]
    if last_ai_message.tool_calls:        
        return "tools"
    return "__end__"


retreive_key = "retreive"
web_search_key = "web_search"
analysis_setting_key = "analysis_setting"
tools_key = "tools"
agent_key = "agent"
graph_builder = StateGraph(SupplyDemandState)
graph_builder.add_node(web_search_key, web_search)
graph_builder.add_node(retreive_key, retreive)
graph_builder.add_node(analysis_setting_key, analysis_setting)
graph_builder.add_node(tools_key, tool_node)
graph_builder.add_node(agent_key, agent)

graph_builder.add_edge(START, retreive_key)
graph_builder.add_edge(START, web_search_key)
graph_builder.add_edge(retreive_key, analysis_setting_key)
graph_builder.add_edge(web_search_key, analysis_setting_key)
graph_builder.add_edge(analysis_setting_key, agent_key)

graph_builder.add_conditional_edges(agent_key, router, [tools_key, END])
graph_builder.add_edge(tools_key, agent_key)

supply_demand_graph = graph_builder.compile()
