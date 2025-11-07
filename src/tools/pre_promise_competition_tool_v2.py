# 기존 Exa MCP 코드 (주석처리)
# from tools.mcp_client.mcp_client import get_tools
from tools.tavily_search_tool import tavily_search
from utils.llm import LLMProfile
from langchain_core.messages import ToolMessage
import sys


async def pre_promise(query):
    # 기존 Exa MCP 코드 (주석처리)
    # # Jupyter 환경에서는 MCP가 작동하지 않음
    # if 'ipykernel' in sys.modules:
    #     return "청약 경쟁률 데이터는 Jupyter 노트북 환경에서 사용할 수 없습니다. Python 스크립트(.py)로 실행해주세요."
    # 
    # tools = await get_tools()
    # llm = LLMProfile.dev_llm().bind_tools(tools)
    # 
    # prompt = f"""
    # [역할]
    # 당신은 'exa' 도구를 반드시 사용하여 특정 지역의 청약 경쟁률 데이터를 찾는 전문가이다.
    # 
    # [강력 지침]
    # - 질문 중의 자치구를 기준으로만 한다. (동은 무시)
    # - 청약 경쟁률은 반드시 정확한 내용이어야 합니다.
    # 
    # [지침]
    # - 직접 아는 내용을 말하지 마라.
    # - 반드시 `exa` 도구를 호출해야 한다.
    # 
    # [질문]
    # {query}
    # """
    # response = await llm.ainvoke(prompt)
    # if response.tool_calls:
    # 
    #     tools = await get_tools()
    # 
    #     tool_outputs = []
    #     for call in response.tool_calls:
    #         name = call["name"]
    #         args = call.get("args", {})
    #         tool = next((t for t in tools if t.name == name), None)
    #         if tool is None:
    #             continue
    # 
    #         result = await tool.ainvoke(args)
    #         tool_outputs.append(
    #             ToolMessage(
    #                 tool_call_id=call["id"],  # ✅ 중요!
    #                 name=name,
    #                 content={"result": result},
    #             )
    #         )

    # 새로운 Tavily 코드
    tools = [tavily_search]
    llm = LLMProfile.dev_llm().bind_tools(tools)

    prompt = f"""
    [역할]
    당신은 'tavily_search' 도구를 반드시 사용하여 특정 지역의 청약 경쟁률 데이터를 찾는 전문가이다.

    [강력 지침]
    - 질문 중의 자치구를 기준으로만 한다. (동은 무시)
    - 청약 경쟁률은 반드시 정확한 내용이어야 합니다.

    [지침]
    - 직접 아는 내용을 말하지 마라.
    - 반드시 `tavily_search` 도구를 호출해야 한다.
    - 검색 쿼리는 "지역명 청약 경쟁률" 형식으로 작성하세요.

    [질문]
    {query}
    """
    response = await llm.ainvoke(prompt)
    if response.tool_calls:
        tool_outputs = []
        for call in response.tool_calls:
            name = call["name"]
            args = call.get("args", {})
            tool = next((t for t in tools if t.name == name), None)
            if tool is None:
                continue

            result = await tool.ainvoke(args)
            tool_outputs.append(
                ToolMessage(
                    tool_call_id=call["id"],
                    name=name,
                    content=str(result),
                )
            )

        final = await llm.ainvoke(
            [
                response,
                *tool_outputs,
                {
                    "role": "system",
                    "content": """
                    [지침]
                    - 직접 아는 내용을 말하지 마라.
                    - 검색 결과를 바탕으로 `JSON`만 반환한다.
                    - 절대로 자연어 설명을 하지 마라.
                    - 출력 형식은 아래 예시와 완전히 동일해야 한다.

                    [주의 사항]
                    - 무순위 경쟁률은 찾지마십시오
                    - 실제 청약시의 경쟁률을 기준으로 찾아주십시오 

                    [출력 형식]
                    - 공고일은 명확하게 해주세요 잘 모르겠으면 2025-10 까지 월까지 적으십시오.
                    - 경쟁률은 항상 :1 로 뒤에 붙여주십시오.
                    [
                      {
                        "주소": "서울특별시 동작구 사당동 155-4번지 일원",
                        "공고일": "2025-10-02",
                        "경쟁률": "447.90:1"
                      }
                    ]
                """,
                },
            ]
        )
        return final.content

    else:
        return "제공된 청약 내용이 없습니다."
