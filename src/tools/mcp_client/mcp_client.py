from langchain_mcp_adapters.client import MultiServerMCPClient
from dotenv import load_dotenv
import os, platform
import asyncio

load_dotenv()
_client = None
_tools = None

import anyio
from langchain_mcp_adapters import sessions
from contextlib import asynccontextmanager

_original_create_stdio_session = sessions._create_stdio_session

@asynccontextmanager
async def _patched_create_stdio_session(*args, **kwargs):
    # timeout 구간을 context 전체에 적용
    with anyio.move_on_after(180):  # 3분까지 허용
        async with _original_create_stdio_session(*args, **kwargs) as session:
            yield session

# monkey-patch
sessions._create_stdio_session = _patched_create_stdio_session

def get_exa_config():
    """Exa MCP 예시"""
    MCP_KEY = os.getenv("MCP_KEY")
    print(MCP_KEY)

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
    global _client
    if _client is None: 
        _client = MultiServerMCPClient(
            {
                "exa": get_exa_config()
            }
        )
    return _client


async def get_tools():
    global _tools
    if _tools is None:
        client = await get_client()
        try:
            print("[MCP] Waiting up to 120s for tool manifest...")
            _tools = await asyncio.wait_for(client.get_tools(), timeout=120)
        except asyncio.TimeoutError:
            raise RuntimeError("⚠️ Smithery MCP 서버가 120초 내 manifest를 반환하지 않았습니다.")
    return _tools