from dotenv import load_dotenv

load_dotenv()
from agents.state.start_state import  StartInput
from agents.state.main_state import MainState
from utils.llm import LLMProfile
from langgraph.graph import StateGraph, START, END
from prompts import PromptManager, PromptType
from agents.jung_min_jae.jung_min_jae_agent import report_graph
from copy import deepcopy

start_input_key = MainState.KEY.start_input
target_area_key = StartInput.KEY.target_area
main_type_key = StartInput.KEY.main_type
total_units_key = StartInput.KEY.total_units
email_key = StartInput.KEY.email

start_llm = LLMProfile.chat_bot_llm()
messages_key = MainState.KEY.messages

analysis_outputs_key = MainState.KEY.analysis_outputs
final_report_key = MainState.KEY.final_report
status_key = MainState.KEY.status


def jung_min_jae_graph(state: MainState) -> MainState:

    result = report_graph.invoke(
        {
            "start_input": deepcopy(state[start_input_key]),
            "analysis_outputs": deepcopy(state[analysis_outputs_key]),
            "segment": 1,
        }
    )

    return {"final_report": result["final_report"], status_key: "RENDERING"}



from tools.send_gmail import gmail_authenticate
from tools.send_gmail import send_single_gmail

housing_faq_key = "housing_faq"
location_insight_key = "location_insight"
policy_output_key = "policy_output"
supply_demand_key = "supply_demand"
unsold_insight_key = "unsold_insight"
population_insight_key = "population_insight"
nearby_market_key = "nearby_market"
def final_node(state: MainState) -> MainState:
    analysis_outputs = state[analysis_outputs_key]
    housing_faq = analysis_outputs[housing_faq_key]
    location_insight = analysis_outputs[location_insight_key]
    policy_output = analysis_outputs[policy_output_key]
    supply_demand = analysis_outputs[supply_demand_key]
    unsold_insight = analysis_outputs[unsold_insight_key]
    population_insight = analysis_outputs[population_insight_key]
    nearby_market = analysis_outputs[nearby_market_key]
    
    prompt = PromptManager(PromptType.MAIN_SOUCE_PAGE).get_prompt(
        housing_faq_context = housing_faq['housing_faq_context'],
        housing_faq_download_link = housing_faq['housing_faq_download_link'],
        
        housing_rule_context = housing_faq['housing_rule_context'],
        housing_rule_download_link = housing_faq['housing_rule_download_link'],
        
        location_context = location_insight['kakao_api_distance_context'],
        location_download_link = location_insight['kakao_api_distance_download_link'],
        
        nearby_context = nearby_market['kakao_api_distance_context'],
        nearby_download_link = nearby_market['kakao_api_distance_download_link'],
        
        netional_news_context = policy_output['national_context'],
        netional_download_link = policy_output['national_download_link'],
        
        region_context = policy_output['region_context'],
        region_download_link = policy_output['region_download_link'],
        
        unsold_unit = unsold_insight['unsold_unit'],
        unsold_unit_download_link = unsold_insight['unsold_unit_download_link'],
        
        move_population_context = population_insight['move_population_context'],
        move_population_download_link = population_insight['move_population_download_link'],
        
        age_population_context = population_insight['age_population_context'],
        age_population_download_link = population_insight['age_population_download_link'],
        
        home_mortgage = supply_demand['home_mortgage'],
        home_mortgage_download_link = supply_demand['home_mortgage_download_link'],
        
        use_kor_rate = supply_demand['use_kor_rate'],
        use_kor_rate_download_link = supply_demand['use_kor_rate_download_link'],
        
        one_people_gdp = supply_demand['one_people_gdp'],
        one_people_grdp = supply_demand['one_people_grdp'],
        one_people_gdp_grdp_download_link = supply_demand['one_people_gdp_grdp_download_link'],
        
        planning_move = supply_demand['planning_move'],
        planning_move_download_link = supply_demand['planning_move_download_link'],
        
        housing_sales_volume = supply_demand['housing_sales_volume'],
        housing_sales_volume_download_link = supply_demand['housing_sales_volume_download_link'],
        
        jeonse_price = supply_demand['jeonse_price'],
        jeonse_price_download_link = supply_demand['jeonse_price_download_link'],
        
                
        sale_price = supply_demand['sale_price'],
        sale_price_download_link = supply_demand['sale_price_download_link'],
        
        year10_after_house = supply_demand['year10_after_house'],
        trade_balance = supply_demand['trade_balance']
    )
        
    res = LLMProfile.dev_llm().invoke(prompt)
    email = state[start_input_key][email_key]
    final_report = state[final_report_key]
    
    
    start_input = state[start_input_key]
    target_area = start_input[target_area_key]
    main_type = start_input[main_type_key]
    total_units = start_input[total_units_key]
    main_title = (
        f"{target_area}\n {main_type}, {total_units}세대 사업 보고서"
    )
    
    source_title = (
        f"{target_area}\n {main_type}, {total_units}세대 사업 보고서 - 데이터 출처"
    )
    gmail_authenticate()
    send_single_gmail(
        md_content=final_report,
        to=email,
        title=main_title,        
    )

    send_single_gmail(
        md_content=res.content,
        to=email,
        title=source_title,        
    )
    
    return {
        'source':res.content
    }
    


graph_builder = StateGraph(MainState)
final_key = "final"

graph_builder.add_node(final_key,final_node)

graph_builder.add_edge(START, final_key)
graph_builder.add_edge(final_key, END)
