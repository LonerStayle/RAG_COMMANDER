from langgraph.graph import StateGraph, START, END 
from agents.state.analysis_state import HousingFaqState
from agents.state.start_state import StartInput


start_input_key = HousingFaqState.KEY.start_input
target_area_key = StartInput.KEY.target_area
housing_faq_context_key = HousingFaqState.KEY.housing_faq_context
housing_rule_context_key = HousingFaqState.KEY.housing_rule_context


def test(state:HousingFaqState) -> HousingFaqState:
    start_input = state[start_input_key]
    target_area = state[target_area_key]
    
    return {
        "housing_faq_output": "housing_faq_output_test"
    }
    
    
graph_builder = StateGraph(HousingFaqState)
graph_builder.add_node("test",test)
graph_builder.add_edge(START, "test")
graph_builder.add_edge("test", END)

housing_faq_graph = graph_builder.compile()