from langchain_openai import ChatOpenAI
from langgraph.graph.state import Command, Literal
from main_state import StartConfirmation
from utils.enum import ModelName
from utils.util import get_today_str
from agents.main.main_state import MainState, StartInput
from langchain_core.messages import HumanMessage, get_buffer_string, AIMessage
from langgraph.graph import StateGraph, START, END
from prompts import PromptManager, PromptType

llm = ChatOpenAI(model=ModelName.GPT_4_1_MINI, temperature=0)
messages_key = MainState.Key.messages
start_input_key = MainState.Key.start_input


def start_confirmation(
    state: MainState,
) -> Command[Literal["start", "__end__"]]:

    parser_llm = llm.with_structured_output(StartConfirmation)
    messages_str = get_buffer_string(messages=state[messages_key])

    prompt = PromptManager(PromptType.MAIN_START_CONFIRMATION).get_prompt(
        messages=messages_str
    )
    response: StartConfirmation = parser_llm.invoke([HumanMessage(content=prompt)])

    if response.confirm == False:
        return Command(
            goto=END, update={messages_key: [AIMessage(content=response.question)]}
        )
    else:
        return Command(
            goto="start",
            update={messages_key: [AIMessage(content=response.verification)]},
        )


def start(state: MainState) -> MainState:
    parser_model = llm.with_structured_output(StartInput)
    prompt = PromptManager(PromptType.MAIN_START).get_prompt(
        messages=get_buffer_string(state[messages_key]), 
                                   date=get_today_str()
    )
    response: StartInput = parser_model.invoke([HumanMessage(content=prompt)])

    return {start_input_key: response.model_dump()}

graph_builder = StateGraph(MainState)
graph_builder.add_node("start_confirmation", start_confirmation)
graph_builder.add_node("start",start)

graph_builder.add_edge(START, "start_confirmation")
graph_builder.add_edge("start", END)

