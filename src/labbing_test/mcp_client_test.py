import os
import platform
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()

_client = None
_tools = None


def get_exa_config():
    """Exa MCP 예시"""
    MCP_KEY = os.getenv("MCP_KEY")


    if platform.system() == "Windows":
        return {
            "command": "cmd",
            "args": [
                "/c",
                "npx",
                "-y",
                "@smithery/cli@latest",
                "run",
                "exa",
                "--key",
                MCP_KEY,
                "--profile",
                "usual-reindeer-MZSQQr",
            ],
            "transport": "stdio",
        }
    else:
        return {
            "command": "npx",
            "args": [
                "-y",
                "@smithery/cli@latest",
                "run",
                "exa",
                "--key",
                MCP_KEY,
                "--profile",
                "usual-reindeer-MZSQQr",
            ],
            "transport": "stdio",
        }



async def get_client():
    """MCP 클라이언트 단일 인스턴스 생성"""
    global _client
    if _client is None:
        _client = MultiServerMCPClient(
            {
                "exa": get_exa_config(),
            }
        )
    return _client


async def get_tools():
    """MCP 툴 목록 불러오기"""
    global _tools
    if _tools is None:
        client = await get_client()
        _tools = await client.get_tools()
    return _tools