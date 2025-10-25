from langgraph.graph import StateGraph, START, END 
from langchain_core.tools import tool
from langchain.chat_models import init_chat_model
from utils.enum import LLMProfile
from langgraph.prebuilt import ToolNode
from prompts import PromptManager, PromptType
from utils.util import get_today_str
from agents.state.start_state import StartInput
from langchain_core.messages import SystemMessage, HumanMessage
from agents.state.jung_min_jae_state import JungMinJaeState


@tool(parse_docstring=True)
def think_tool(reflection: str) -> str:
    """최종 보고서 산출 직전, **합성 품질 점검·수정 지시·결정(Proceed/Revise)**를 남기는 내부 성찰(Reflexion) 도구입니다.

    이 도구는 `analysis_outputs`(각 에이전트 하이브리드 결과)와 선택적 RAG(`rag_docs`: 교육과정 PDF 청크)가
    병합된 초안(보고서 Markdown + 부록 메타 초안)을 대상으로 다음을 강제 점검합니다:
    **시점/단위/출처/격자 스키마 일치**, **가격 밴드 로직**, **리스크·완화의 근거 매핑**, **RAG 인용의 적합성**.

    사용 시점(모두 해당):
        - 최종 Markdown 초안과 메타(JSON) 초안이 생성된 직후
        - PDF RAG 근거(education PDFs)와 외부 인용(citations)이 연결된 뒤
        - 출력 확정 전, 단 한 번 실행(필요하면 1회 재실행 가능)

    성찰 본문(reflection)에 반드시 포함할 체크리스트:
        1) Coverage — 핵심 섹션이 모두 채워졌는가?
           - Exec Summary(5~7문장), 입지, 개요 표, 수요타겟, 주변 시세/분양, 미분양, 정책/FAQ, 종합결론
        2) Dates — **기준일(as-of)** 표기가 일관한가? (YYYY-MM 또는 YYYY-MM-DD)
           - 청약/미분양/실거래/보급률 등 각 시계열의 최신월이 과도하게 상이하지 않은가?
        3) Units — 단위 일관성 점검: m, 분, **만원/3.3㎡**, 배, %
           - 환산(3.3㎡, 총액 예시) 근거가 부록에 기록되었는가?
        4) Citations — `citations[*].evidence_for` ↔ **facts 경로**가 정확히 매핑되었는가?
           - 외부 URL은 1차/공식 우선, 내부 PDF는 `source:"internal_pdf", id, page`로 식별했는가?
        5) Conflicts — 출처 충돌/수치 불일치가 있으면 **채택 우선순위**(공식>공시>민간)에 따라 채택했고,
           미해결 불일치는 본문에 “불일치”로, 부록 `diagnostics`에 상세 기록했는가?
        6) RAG Fit — 교육과정 PDF는 **정의/전략/체크리스트** 용도로만 사용되었는가?
           - 정량 수치의 1차 근거로 사용하지 않았는가? 직접 인용은 25단어 이내인가?
        7) Price Band — 권장 분양가 밴드(만원/3.3㎡, 전용84 총액 예시)가
           - 1km 유사 연식·평형 **매매 평단가 대비 ±10%** 규칙을 기본으로, 브랜드/입지 등 **±(5~10%)** 보정 논리를 갖추었는가?
           - `relative_position.risk_flag`와 본문 경고 문구가 일치하는가?
        8) Risk Register — 핵심 리스크(수요/미분양/가격/정책)가 **evidence_for**와 연결되고,
           각 리스크의 완화책이 교육과정 PDF 전술(무이자·계약금·타깃 평형 등)과 호응하는가?
        9) Narrative Logic — 문단이 “수치 → 의미 → **분양성/분양가 영향**”의 인과로 끝나는가?
           과도한 단정 표현은 제거되었는가?

    권장 서술 포맷(반드시 이 머리표를 포함해 시작할 것):
        DECISION: <PROCEED | REVISE> 
        FIXES:
          - <수정 지시 1: 위치/파일 경로/문장 교체 지시>
          - <수정 지시 2: 단위/시점/표 라벨 정정>
        GAPS:
          - <미확인 값과 사유, 재수집 쿼리 제안(공식 경로 포함)>
        CONFLICTS:
          - <항목/출처 간 불일치와 채택 사유; 미해결은 diagnostics로 이관>
        PRICE_BAND_CHECK:
          - base: <매매 평단가 근거> / adjustment: <보정 사유와 % 범위> / verdict: <적정/보수/공격>
        RISK_REGISTER_CHECK:
          - <리스크 항목: level, mitigation, evidence_for 경로 검증 결과>
        RAG_LINKS:
          - <사용한 PDF id/page → 본문 단락/부록 항목 매핑 점검 요약>

    Args:
        reflection (str): 위 체크리스트·포맷을 충족하는 **자유 서술**.
            - 보고서 초안에서 발견한 문제/수정/보강 지시를 구체적으로 기입
            - 필요한 경우 ‘REVISE’를 선언하고 어떤 노드(에이전트 facts) 재조회가 필요한지 명시

    Returns:
        str: "Reflection recorded: <요약>" 형식의 확인 메시지.
             (런타임에서는 이 문자열 외에, `DECISION`이 "REVISE"일 때 워크플로우가 재수집/재합성 분기로 이동)

    주의:
        - 이 도구 자체는 외부 호출 없이 텍스트만 기록합니다(부수효과 없음).
        - 구글 스타일 도크스트링을 준수해야 하며, 파싱 오류 시 예외가 발생할 수 있습니다.
        - 구조화 출력 및 도구 스키마 파싱은 LangChain 권장 방식을 따릅니다.
    """
    return f"Reflection recorded: {reflection}"
 
 
analysis_outputs_key = JungMinJaeState.KEY.analysis_outputs
start_input_key = JungMinJaeState.KEY.start_input
rag_context_key = JungMinJaeState.KEY.rag_context
final_report_key = JungMinJaeState.KEY.final_report
messages_key = JungMinJaeState.KEY.messages

llm = init_chat_model(model=LLMProfile.REPORT, temperature=0)
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
        analysis_outputs=analysis_outputs, 
    )
    humun_prompt = PromptManager(PromptType.JUNG_MIN_JAE_HUMAN).get_prompt(
        start_input = start_input,
        analysis_outputs=analysis_outputs,
        context=rag_context,
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

    