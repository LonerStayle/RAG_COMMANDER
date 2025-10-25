from langgraph.graph import StateGraph, START, END 
from agents.state.analysis_state import HousingFaqState
def test(state:HousingFaqState) -> HousingFaqState:
    return {
        "housing_faq_output": "housing_faq_output_test"
    }
    
    
graph_builder = StateGraph(HousingFaqState)
graph_builder.add_node("test",test)
graph_builder.add_edge(START, "test")
graph_builder.add_edge("test", END)

housing_faq_graph = graph_builder.compile()