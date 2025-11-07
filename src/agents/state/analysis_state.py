from typing import TypedDict, Dict, Annotated, Optional
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage
import operator
from utils.util import attach_auto_keys


@attach_auto_keys
class LocationInsightState(TypedDict):
    start_input: dict
    location_insight_output: dict
    rag_context: Optional[str]
    web_context: Optional[str]
    kakao_api_distance_context: Optional[str]
    kakao_api_distance_download_link: Optional[str]
    gemini_search: Optional[str]
    perplexity_search: Optional[str]
    messages: Annotated[list[AnyMessage], add_messages]
    my_tool: str


@attach_auto_keys
class PolicyState(TypedDict):
    start_input: dict
    policy_output: dict
    national_context: Optional[str]
    region_context: Optional[str]
    national_download_link: Optional[str]
    region_download_link: Optional[str]
    messages: Annotated[list[AnyMessage], add_messages]
    my_tool: str


@attach_auto_keys
class HousingFaqState(TypedDict):
    start_input: dict
    housing_faq_output: dict
    housing_faq_context: Optional[str]
    housing_rule_context: Optional[str]
    housing_faq_download_link: Optional[str]
    housing_rule_download_link: Optional[str]
    messages: Annotated[list[AnyMessage], add_messages]


@attach_auto_keys
class NearbyMarketState(TypedDict):
    start_input: dict
    nearby_market_output: dict
    kakao_api_distance_context: Optional[str]
    kakao_api_distance_download_link: Optional[str]
    gemini_search: Optional[str]
    real_estate_price_context: Optional[str]
    perplexity_search: Optional[str]
    rag_context: Optional[str]
    web_context: Optional[str]
    messages: Annotated[list[AnyMessage], add_messages]


@attach_auto_keys
class PopulationInsightState(TypedDict):
    start_input: dict
    population_insight_output: dict
    age_population_context: Optional[str]
    age_population_download_link:Optional[str]
    move_population_context: Optional[str]
    move_population_download_link:Optional[str]
    messages: Annotated[list[AnyMessage], add_messages]


@attach_auto_keys
class SupplyDemandState(TypedDict):
    start_input: dict
    supply_demand_output: dict

    year10_after_house: Optional[str]
    year10_after_house_download_link:Optional[str]
    jeonse_price: Optional[str]
    jeonse_price_download_link:Optional[str]
    sale_price: Optional[str]
    sale_price_download_link:Optional[str]
    trade_balance: Optional[str]
    trade_balance_download_link:Optional[str]
    use_kor_rate: Optional[str]
    use_kor_rate_download_link:Optional[str]
    home_mortgage: Optional[str]
    home_mortgage_download_link:Optional[str]
    one_people_gdp: Optional[str]
    one_people_grdp: Optional[str]
    one_people_gdp_grdp_download_link:Optional[str]
    housing_sales_volume: Optional[str]
    housing_sales_volume_download_link:Optional[str]
    planning_move: Optional[str]
    planning_move_download_link:Optional[str]
    pre_pomise_competition: Optional[str]
    pre_pomise_competition_download_link:Optional[str]

    messages: Annotated[list[AnyMessage], add_messages]


@attach_auto_keys
class UnsoldInsightState(TypedDict):
    start_input: dict
    unsold_insight_output: dict
    unsold_unit: Optional[str]
    unsold_unit_download_link: Optional[str]
    messages: Annotated[list[AnyMessage], add_messages]


@attach_auto_keys
class AnalysisGraphState(TypedDict, total=False):

    location_insight_output: dict
    policy_output: dict
    housing_faq_output: dict
    nearby_market_output: dict
    population_insight_output: dict
    supply_demand_output: dict
    unsold_insight_output: dict

    # (Main → 상위 → 하위 전달용 입니다.)
    start_input: Annotated[dict, operator.or_]

    analysis_outputs: Annotated[Dict[str, dict], operator.or_]
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
