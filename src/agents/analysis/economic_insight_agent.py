from langgraph.graph import StateGraph, START, END
from agents.state.analysis_state import EconomicInsightState
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from utils.llm import LLMProfile
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
web_context_key = EconomicInsightState.KEY.web_context
rag_context_key = EconomicInsightState.KEY.rag_context
target_area_key = StartInput.KEY.target_area
messages_key = EconomicInsightState.KEY.messages

llm = LLMProfile.analysis_llm()
tool_list = [think_tool]
llm_with_tools = llm.bind_tools(tool_list)
tool_node = ToolNode(tool_list)

from langchain_openai import OpenAIEmbeddings
import json
from tools.rag.vectorstore import build_pgvector_store, TEST_COLLECTION_NAME
from perplexity import Perplexity
search_client = Perplexity()
def web_search(state: EconomicInsightState) -> EconomicInsightState:
    start_input = state[start_input_key]
    target_area = start_input[target_area_key]
    date_str = get_today_str()
    queries=[
        # 1) 기준금리(한국은행) — 레벨/최근 결정일/최근 12~36개월 추세
        f"{date_str} 기준 한국은행 기준금리 최근 추이 결정일 정책금리 site:bok.or.kr",

        # 2) 가계대출·주담대 체감금리(가능 시) — 공식 보도자료/통계
        f"{date_str} 한국 주택담보대출 금리 추이 보도자료 site:bok.or.kr",

        # 3) 물가·경기 지표 — CPI YoY, GDP 성장률(최근 분기) (KOSIS/BOK)
        f"{date_str} 대한민국 소비자물가지수 YoY 최신 통계 site:kosis.kr",
        f"{date_str} 한국 국내총생산 GDP 성장률 최근 분기 속보치 site:bok.or.kr",

        # 4) 주택가격/심리 — 한국부동산원 공식 지표(매매·전세, 심리지수)
        f"{date_str} 한국부동산원 주간 또는 월간 주택가격 동향 매매 전세 지수 site:reb.or.kr",
        f"{date_str} 한국 주택매매심리지수 소비심리지수 변화 site:reb.or.kr OR site:bok.or.kr",

        # 5) 전국 정책(금융 규제) — LTV/DTI/DSR 최근 변경 및 효력일(금융위)
        f"{date_str} LTV DTI DSR 규제 변경 효력일 보도자료 site:fsc.go.kr",

        # 6) 지역 규제(대상지) — 조정대상지역/투기과열지구/토지거래허가구역 상태와 고시일(국토부·지자체)
        f"{target_area} 조정대상지역 투기과열지구 토지거래허가구역 지정 해제 고시일 site:molit.go.kr OR site:go.kr",

        # 7) 분양가상한제/청약 제도 변경 — 적용 범위·요건(국토부·청약홈)
        f"{date_str} 분양가상한제 적용 범위 요건 변경 보도자료 site:molit.go.kr",
        f"{date_str} 청약제도 변경 가점 산정 1순위 요건 안내 site:applyhome.co.kr",

        # 8) 보완: 금융시장 지표 — 국채금리(3/5/10년), 코스피 등(공식 출처 또는 BOK)
        f"{date_str} 한국 국채금리 3년 5년 10년 추이 공식 통계 site:bok.or.kr",

        # 9) 정책 전문/고시 원문 PDF (있으면 가점)
        f"{date_str} 파일type:pdf LTV DSR 규제 개정안 보도자료 site:fsc.go.kr",
        f"{date_str} 파일type:pdf 조정대상지역 지정 해제 고시 site:molit.go.kr"
    ]
    
    search_list = []
    for i in range(0, len(queries), 5):
        batch = queries[i:i+5]
        res = search_client.search.create(query=batch)
        search_list.append(res)
        return {**state, web_context_key: search_list}

def retreive(state: EconomicInsightState) -> EconomicInsightState:
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

def analysis_setting(state: EconomicInsightState) -> EconomicInsightState:
    start_input = state[start_input_key]
    target_area = start_input[target_area_key]
    rag_context = state[rag_context_key]
    web_context = state[web_context_key]

    system_prompt = PromptManager(PromptType.ECONOMIC_INSIGHT_SYSTEM).get_prompt(
        date=get_today_str()
    )
    humun_prompt = PromptManager(PromptType.ECONOMIC_INSIGHT_HUMAN).get_prompt(
        target_area=target_area,
        web_context =web_context,
        rag_context=rag_context,
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


retreive_key = "retreive"
web_search_key = "web_search"
analysis_setting_key = "analysis_setting"
tools_key = "tools"
agent_key = "agent"
graph_builder = StateGraph(EconomicInsightState)
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

economic_insight_graph = graph_builder.compile()
