from utils.util import attach_auto_keys
from typing import Annotated, TypedDict, Optional
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage

@attach_auto_keys
class JungMinJaeState(TypedDict):
    analysis_outputs:dict
    start_input: dict
    rag_context:Optional[str]
    final_report: Optional[str]
    messages : Annotated[list[AnyMessage], add_messages]