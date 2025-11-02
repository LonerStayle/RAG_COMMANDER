from langgraph.graph import StateGraph, START, END 
from agents.state.analysis_state import HousingFaqState
from agents.state.start_state import StartInput


start_input_key = HousingFaqState.KEY.start_input
target_area_key = StartInput.KEY.target_area
main_type_key = StartInput.KEY.main_type
housing_faq_context_key = HousingFaqState.KEY.housing_faq_context
housing_rule_context_key = HousingFaqState.KEY.housing_rule_context

from tools.rag.retriever.housing_faq_retriever import housing_rule_retrieve, housing_faq_retrieve
def get_rule_data(state:HousingFaqState) -> HousingFaqState:
    start_input = state[start_input_key]
    target_area = start_input[target_area_key]
    main_type = start_input[main_type_key]

    retriever = housing_rule_retrieve()
    query = f"사업지:{target_area}\n세대수 및 타입:{main_type} 위와 조금이라도 관련된 주택 공급 내용"    
    return {
        housing_rule_context_key: retriever.invoke(query)
    }
    
def get_faq_data(state:HousingFaqState) -> HousingFaqState:
    start_input = state[start_input_key]
    target_area = start_input[target_area_key]
    main_type = start_input[main_type_key]

    retriever = housing_faq_retrieve()
    query = f"사업지:{target_area}\n세대수 및 타입:{main_type} 위와 조금이라도 관련된 청약 질의 내용 모두"    
    
    return {
        housing_faq_context_key: retriever.invoke(query)
    }
    
def analysis_setting(state:HousingFaqState) -> HousingFaqState:
    
    return {
        
    }
    
graph_builder = StateGraph(HousingFaqState)
graph_builder.add_node("test",get_rule_data)
graph_builder.add_edge(START, "test")
graph_builder.add_edge("test", END)

housing_faq_graph = graph_builder.compile()