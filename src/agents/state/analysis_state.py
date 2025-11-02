from typing import TypedDict, Dict, Annotated, Optional
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage
import operator
from utils.util import attach_auto_keys


@attach_auto_keys
class LocationInsightState(TypedDict):
    start_input: dict
    location_insight_output: Optional[str]
    rag_context: Optional[str]
    web_context: Optional[str]
    messages: Annotated[list[AnyMessage], add_messages]
    my_tool: str


@attach_auto_keys
class PolicyState(TypedDict):
    start_input: dict
    policy_output: str
    national_context: Optional[str]
    region_context: Optional[str]
    messages: Annotated[list[AnyMessage], add_messages]
    my_tool: str


@attach_auto_keys
class HousingFaqState(TypedDict):
    start_input: dict
    housing_faq_output: str
    housing_faq_context: Optional[str]
    housing_rule_context: Optional[str]
    messages: Annotated[list[AnyMessage], add_messages]


@attach_auto_keys
class NearbyMarketState(TypedDict):
    start_input: dict
    nearby_market_output: str
    rag_context: Optional[str]
    web_context: Optional[str]
    messages: Annotated[list[AnyMessage], add_messages]


@attach_auto_keys
class PopulationInsightState(TypedDict):
    start_input: dict
    population_insight_output: str
    age_population_context: Optional[str]
    move_population_context: Optional[str]
    messages: Annotated[list[AnyMessage], add_messages]


@attach_auto_keys
class SupplyDemandState(TypedDict):
    start_input: dict
    supply_demand_output: str

    year10_after_house: Optional[str]
    jeonse_price: Optional[str]
    sale_price: Optional[str]
    trade_balance: Optional[str]
    use_kor_rate: Optional[str]
    home_mortgage: Optional[str]
    one_people_gdp: Optional[str]
    one_people_grdp: Optional[str]
    housing_sales_volume: Optional[str]
    planning_move: Optional[str]
    pre_pomise_competition: Optional[str]

    messages: Annotated[list[AnyMessage], add_messages]


@attach_auto_keys
class UnsoldInsightState(TypedDict):
    start_input: dict
    unsold_insight_output: str
    unsold_unit: Optional[str]
    messages: Annotated[list[AnyMessage], add_messages]


@attach_auto_keys
class AnalysisGraphState(TypedDict, total=False):
    analysis_outputs: Annotated[Dict[str, str], operator.or_]
    location_insight_output: str
    policy_output: str
    housing_faq_output: str
    nearby_market_output: str
    population_insight_output: str
    supply_demand_output: str
    unsold_insight_output: str

    # (Main → 상위 → 하위 전달용 입니다.)
    start_input: Annotated[dict, operator.or_]

    # 필요 없을 것 같아서 주석
    # analysis_group_messages : Annotated[list[AnyMessage], add_messages]
