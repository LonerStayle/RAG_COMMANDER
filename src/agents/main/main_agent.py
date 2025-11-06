from dotenv import load_dotenv

load_dotenv()

from langgraph.graph.state import Command, Literal
from agents.state.start_state import StartConfirmation, StartInput
from agents.state.main_state import MainState
from utils.llm import LLMProfile
from utils.util import get_today_str
from langchain_core.messages import HumanMessage, get_buffer_string, AIMessage
from langgraph.graph import StateGraph, START, END
from prompts import PromptManager, PromptType
from agents.analysis.analysis_graph import analysis_graph
from agents.jung_min_jae.jung_min_jae_agent import report_graph
from agents.renderer.renderer_agent import renderer_graph
from copy import deepcopy

# def start_confirmation(
#     state: MainState,
# ) -> Command[Literal["start", "__end__"]]:
#     # gmail_authenticate()
#     parser_llm = start_llm.with_structured_output(StartConfirmation)

#     messages_str = get_buffer_string(messages=state[messages_key])

#     prompt = PromptManager(PromptType.MAIN_START_CONFIRMATION).get_prompt(
#         messages=messages_str
#     )
#     response: StartConfirmation = parser_llm.invoke([HumanMessage(content=prompt)])

#     if response.confirm == False:
#         return Command(
#             goto=END, update={messages_key: [AIMessage(content=response.question)]}
#         )
#     else:
#         return Command(
#             goto="start",
#             update={messages_key: [AIMessage(content=response.verification)]},
#         )


start_llm = LLMProfile.chat_bot_llm()
messages_key = MainState.KEY.messages
start_input_key = MainState.KEY.start_input
analysis_outputs_key = MainState.KEY.analysis_outputs
final_report_key = MainState.KEY.final_report
status_key = MainState.KEY.status


def start(state: MainState) -> MainState:
    parser_model = start_llm.with_structured_output(StartInput)
    prompt = PromptManager(PromptType.MAIN_START).get_prompt(
        messages=get_buffer_string(state[messages_key]), date=get_today_str()
    )
    response: StartInput = parser_model.invoke([HumanMessage(content=prompt)])
    print("start_input", response)
    return {start_input_key: response.model_dump(), status_key: "ANALYSIS"}


async def analysis_graph_node(state: MainState) -> MainState:

    result = await analysis_graph.ainvoke(
        {"start_input": deepcopy(state[start_input_key])}
    )
    return {
        "analysis_outputs": result.get("analysis_outputs", {}),        
        status_key: "JUNG_MIN_JAE",
    }


def jung_min_jae_graph(state: MainState) -> MainState:
    
    result = report_graph.invoke(
        {
            "start_input": deepcopy(state[start_input_key]),
            "analysis_outputs": deepcopy(state[analysis_outputs_key]),
            "segment": 1,
        }
    )
    return {"final_report": result["final_report"], status_key: "RENDERING"}

# def rendering(state: MainState) -> MainState:
    
#     renderer_graph.invoke(
#         {
#             "start_input": deepcopy(state[start_input_key]),
#             "analysis_outputs": deepcopy(state[analysis_outputs_key]),
#             'final_report': deepcopy(state[final_report_key])
#         }
#     )
#     return {status_key: "DONE"} 

graph_builder = StateGraph(MainState)

# start_confirmation_key = "start_confirmation"
start_key = "start"
analysis_graph_key = "analysis_graph"
jung_min_jae_key = "jung_min_jae_graph"
renderer_key =  "renderer"

# graph_builder.add_node(start_confirmation_key, start_confirmation)
graph_builder.add_node(start_key, start)
graph_builder.add_node(analysis_graph_key, analysis_graph_node)
graph_builder.add_node(jung_min_jae_key, jung_min_jae_graph)
# graph_builder.add_node(renderer_key, rendering)

# graph_builder.add_edge(START, start_confirmation_key)
graph_builder.add_edge(START, start_key)
graph_builder.add_edge(start_key, analysis_graph_key)
graph_builder.add_edge(analysis_graph_key, jung_min_jae_key)
# graph_builder.add_edge(jung_min_jae_key, renderer_key)
graph_builder.add_edge(jung_min_jae_key, END)
