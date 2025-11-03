
from utils.util import attach_auto_keys
from typing import Annotated, TypedDict, Optional, Dict
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage

@attach_auto_keys
class RendererState(TypedDict):
    start_input: dict
    analysis_outputs:dict
    
    final_report: Optional[str]
    messages : Annotated[list[AnyMessage], add_messages]