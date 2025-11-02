from utils.util import attach_auto_keys
from typing import Annotated, TypedDict, Optional, Dict
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage

@attach_auto_keys
class JungMinJaeState(TypedDict):
    analysis_outputs:dict
    start_input: dict
    rag_context:Optional[str]
    final_draft: Optional[str]
    final_report: Optional[str]
    
    # think_tool 결과 
    review_feedback: Optional[str]  
    segment: int
    segment_buffers: Dict[str, str]  
    messages : Annotated[list[AnyMessage], add_messages]