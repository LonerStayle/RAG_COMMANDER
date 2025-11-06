import os, sys
from pathlib import Path

# 스크립트 파일 위치 기준으로 src 경로 계산
# 현재 파일: src/agents/main/main_agent_run.py
# src 경로: src/agents/main -> src/agents -> src
src_path = Path(__file__).resolve().parents[2]
sys.path.append(str(src_path))

print(f"Added to sys.path: {sys.path[-1]}")
print(f"Current working directory: {os.getcwd()}")

from agents.main.main_agent import graph_builder

graph = graph_builder.compile()

import asyncio
from utils.format_message import format_message
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from agents.state.main_state import MainState


async def main():
    messages_key = MainState.KEY.messages
    checkpointer = InMemorySaver()
    graph = graph_builder.compile(checkpointer=checkpointer)

    thread = {"configurable": {"thread_id": "1"}}
    result = await graph.ainvoke(
        {
            messages_key: [
                HumanMessage(
                    content="서울 강남구 논현동, 84타입, 500세대\n이메일은 immortal0900@gmail.com"
                )
            ]
        },
        config=thread,
    )

    format_message(result[messages_key])


if __name__ == "__main__":
    asyncio.run(main())