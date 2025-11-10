"""
챗봇 상태 정의
"""
from typing import TypedDict, List, Dict, Any, Annotated
from langgraph.graph.message import add_messages


class ChatbotState(TypedDict):
    """챗봇 상태"""

    # 입력 정보
    user_message: str
    target_area: str
    main_type: str
    total_units: str
    session_id: str
    use_faq: bool
    use_rule: bool
    use_policy: bool

    # 검색된 컨텍스트
    faq_context: List[str]
    rule_context: List[str]
    policy_context: List[str]
    source_docs: Annotated[List[Any], lambda x, y: x + y]  # 병렬 실행 시 자동으로 리스트 합치기

    # LLM 메시지
    messages: Annotated[List[Any], add_messages]

    # 출력
    response: str
    sources: List[Dict[str, Any]]
