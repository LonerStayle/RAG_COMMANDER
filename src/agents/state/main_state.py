from utils.util import attach_auto_keys
from typing import Optional,Literal, Dict, Annotated, TypedDict, Optional
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage

@attach_auto_keys
class MainState(TypedDict, total=False):
    
    messages : Annotated[list[AnyMessage], add_messages]
    
    # 사용자 입력 정보
    start_input: dict
    
    # 7개 분석 에이전트의 결과물
    analysis_outputs: Dict[str, str]
    
    # 보고서 초안 및 최종 보고서
    final_report: Optional[str]
    logs:list[str]
    
    # 상태 (현재 단계)
    status: Literal[
        "START_CONFIRMATION", # 시작 / 질문 수집
        "ANALYSIS",      # 데이터 분석중       
        "JUNG_MIN_JAE",    # 보고서 작성중
        "RENDERING",  # PDF 작성중
        "DONE"        # 보고서 PDF 생성 완료
    ] = "START_CONFIRMATION"

