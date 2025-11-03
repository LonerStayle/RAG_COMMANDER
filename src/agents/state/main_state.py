from utils.util import attach_auto_keys
from typing import Optional,Literal, Dict, Annotated, TypedDict, Optional
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage

@attach_auto_keys
class MainState(TypedDict, total=False):
    # messages  : AI랑 채팅 내역
    messages : Annotated[list[AnyMessage], add_messages]
    
    # 사용자 입력 정보
    start_input: dict    
    
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

    # 7개 분석 에이전트의 결과물
    analysis_outputs: Dict[str, str]
    """
    ** analysis_outputs 키 정보 **
    # 정책
    - policy_output
        - result 
        - national_context
        - region_context
    
    # 청약 
    - housing_faq_output
        - result
        - housing_faq_context
        - housing_rule_context
    
    # 인구분석
    - population_insight_output
        - result
        - age_population_context
        - move_population_context
    
    #미분양
    - unsold_insight_output
        - result
        - unsold_unit
    
    # 입지분석
    - location_insight_output
        - result
    
    # 매매비교 
    - nearby_market_output
        - result
    
    # 공급과수요
    - supply_demand_output
        - result
        - year10_after_house
        - jeonse_price
        - sale_price
        - trade_balance
        - use_kor_rate
        - home_mortgage
        - one_people_gdp
        - one_people_grdp
        - housing_sales_volume
        - planning_move
        - pre_pomise_competition
    """