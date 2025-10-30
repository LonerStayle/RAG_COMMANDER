

from agents.state.analysis_state import AnalysisGraphState
from langgraph.graph import StateGraph, START, END

from agents.analysis.policy_agent import policy_graph
from agents.analysis.housing_faq_agent import housing_faq_graph
from agents.analysis.location_insight_agent import location_insight_graph
from agents.analysis.nearby_market_agent import nearby_market_graph
from agents.analysis.population_insight_agent import population_insight_graph
from agents.analysis.supply_demand_agent import supply_demand_graph
from agents.analysis.unsold_insight_agent import unsold_insight_graph


from copy import deepcopy

economic_insight_key = "economic_insight"
housing_faq_key = "housing_faq"
location_insight_key = "location_insight"
nearby_market_key = "nearby_market"
population_insight_key = "population_insight"
supply_demand_key = "supply_demand"
unsold_insight_key = "unsold_insight"
analysis_outputs_key = "analysis_outputs"


def make_transform(agent_name: str):
    return {
        "input": lambda s: {"start_input": deepcopy(s.get("start_input", {}))},
        "output": lambda sub_s: {
            f"{agent_name}_output": sub_s.get(f"{agent_name}_output", "")
        },
    }
graph_builder = StateGraph(AnalysisGraphState)    
graph_builder.add_node(economic_insight_key, policy_graph, transform=make_transform(economic_insight_key))
graph_builder.add_node(housing_faq_key, housing_faq_graph, transform=make_transform(housing_faq_key))
graph_builder.add_node(location_insight_key, location_insight_graph, transform=make_transform(location_insight_key))
graph_builder.add_node(nearby_market_key, nearby_market_graph, transform=make_transform(nearby_market_key))
graph_builder.add_node(population_insight_key, population_insight_graph, transform=make_transform(population_insight_key))
graph_builder.add_node(supply_demand_key, supply_demand_graph, transform=make_transform(supply_demand_key))
graph_builder.add_node(unsold_insight_key, unsold_insight_graph, transform=make_transform(unsold_insight_key))

def join_results(state: AnalysisGraphState) -> AnalysisGraphState:
    analysis_outputs = {
        economic_insight_key: state.get(f"{economic_insight_key}_output"),
        housing_faq_key: state.get(f"{housing_faq_key}_output"),
        location_insight_key: state.get(f"{location_insight_key}_output"),
        nearby_market_key: state.get(f"{nearby_market_key}_output"),
        population_insight_key: state.get(f"{population_insight_key}_output"),
        supply_demand_key: state.get(f"{supply_demand_key}_output"),
        unsold_insight_key: state.get(f"{unsold_insight_key}_output"),
    }
    return {analysis_outputs_key: analysis_outputs}

graph_builder.add_node("join", join_results)

for node in [
    economic_insight_key,
    housing_faq_key,
    location_insight_key,
    nearby_market_key,
    population_insight_key,
    supply_demand_key,
    unsold_insight_key,
]:
    graph_builder.add_edge(START, node)
    graph_builder.add_edge(node, "join")

graph_builder.add_edge("join", END)
analysis_graph = graph_builder.compile()
