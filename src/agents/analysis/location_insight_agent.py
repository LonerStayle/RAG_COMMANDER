from langgraph.graph import StateGraph, START, END
from agents.state.analysis_state import LocationInsightState
from agents.state.start_state import StartInput
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from utils.util import get_today_str
from utils.llm import LLMProfile
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
web_context_key = LocationInsightState.KEY.web_context


llm = LLMProfile.analysis_llm()
tool_list = [think_tool]
llm_with_tools = llm.bind_tools(tool_list)
tool_node = ToolNode(tool_list)

from perplexity import Perplexity
search_client = Perplexity()

def web_search(state: LocationInsightState) -> LocationInsightState:
    start_input = state[start_input_key]
    target_area = start_input[target_area_key]
    total_units = start_input[total_units_key]
    queries=[
            # 1) 학교/통학: 실보행 시간·거리·통학로 위험요소(공식/지자체·교육청·지도 우선)
            f"{target_area} 초등학교 최근접 실보행 거리 분 미터 통학로 안전 보행자도로 횡단보도 site:go.kr OR site:sc.go.kr OR site:gg.go.kr 지도",
            # 2) 지하철/버스 접근: 역세권(도보 10분), 버스정류장 거리·노선 다변성
            f"{target_area} 지하철역 출구 도보 10분 이내 여부 실보행 분 거리 m 버스정류장 거리 노선 환승 급행 site:seoul.go.kr OR site:gg.go.kr 지도",
            # 3) 1km 생활편의 POI 집계: 마트·병원·은행·공공시설(공식/포털지도)
            f"{target_area} 반경 1km 마트 병원 은행 공공시설 개수 위치 목록 공식 지도 통계",
            # 4) 환경/혐오시설: 공원·수변 접근 + 소각장 매립장 변전소 고압선 소음원 거리/영향
            f"{target_area} 공원 수변 산책로 접근성 및 소각장 매립장 변전소 송전선 소음원 위치 거리 영향 보고",
            # 5) 개발호재(단기 실현 위주): 노선/역 신설·도로·상업/공공시설 - 단계(계획/인허가/착공/개통 예정)·ETA
            f"{target_area} 개발 호재 신규 노선 역 신설 도로 확장 상업 공공 복합 인허가 착공 개통 예정 ETA site:go.kr OR site:mlit.go.kr OR site:seoul.go.kr 보도자료 공고",
            # 6) 통근 접근성: 러시아워 기준 강남 여의도 판교 예상 소요시간(근거 포함)
            f"{target_area} 러시아워 출퇴근 시간 강남 여의도 판교 대중교통 환승 기준 소요시간 근거",
            # 7) 학원가·교육 수요 보조: 학원가 밀집·학군 키워드(대단지/세대수도 함께 언급)
            f"{target_area} 학원가 밀집 학군 형성 수요 특징 아파트 세대수 {total_units} 규모 주변 교육 인프라 분석",
            # 8) PDF/공식자료 필터(있으면 가점): 계획서·보도자료·보고서 위주
            f"{target_area} 파일type:pdf 개발 계획 보도자료 보고서 site:go.kr OR site:mlit.go.kr OR site:seoul.go.kr",
    ]
    
    search_list = []
    for i in range(0, len(queries), 5):
        batch = queries[i:i+5]
        res = search_client.search.create(query=batch)
        search_list.append(res)
        return {**state, web_context_key: search_list}


from langchain_openai import OpenAIEmbeddings
import json


def retreive(state: LocationInsightState) -> LocationInsightState:
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


def analysis_setting(state: LocationInsightState) -> LocationInsightState:
    start_input = state[start_input_key]
    target_area = start_input[target_area_key]
    scale = start_input[scale_key]
    total_units = start_input[total_units_key]
    rag_context = state[rag_context_key]
    web_context = state[web_context_key]

    system_prompt = PromptManager(PromptType.LOCATION_INSIGHT_SYSTEM).get_prompt()
    humun_prompt = PromptManager(PromptType.LOCATION_INSIGHT_HUMAN).get_prompt(
        target_area=target_area,
        scale=scale,
        total_units=total_units,
        date=get_today_str(),
        web_context=web_context,
        rag_context=rag_context,
    )
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=humun_prompt),
    ]
    return {messages_key: messages}


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


retreive_key = "retreive"
web_search_key = "web_search"
analysis_setting_key = "analysis_setting"
tools_key = "tools"
agent_key = "agent"
graph_builder = StateGraph(LocationInsightState)
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

location_insight_graph = graph_builder.compile()
