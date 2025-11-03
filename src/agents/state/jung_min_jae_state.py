from utils.util import attach_auto_keys
from typing import Annotated, TypedDict, Optional, Dict
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage

@attach_auto_keys
class JungMinJaeState(TypedDict):
    
    start_input: dict
    rag_context:Optional[str]
    final_draft: Optional[str]
    final_report: Optional[str]
    
    # think_tool 결과 
    review_feedback: Optional[str]  
    segment: int
    segment_buffers: Dict[str, str]  
    messages : Annotated[list[AnyMessage], add_messages]
    
    analysis_outputs:dict
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