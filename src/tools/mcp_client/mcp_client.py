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
                "@smithery/cli@0.1.8",
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
                "@smithery/cli@0.1.8",
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
            print("[MCP] Waiting up to 180s for Smithery MCP manifest...")
            _tools = await asyncio.wait_for(client.get_tools(), timeout=180)
            print(f"[MCP] ✅ {len(_tools)} tools loaded successfully")
        except asyncio.TimeoutError:
            raise RuntimeError("⚠️ Smithery MCP 서버가 180초 내 manifest를 반환하지 않았습니다.")
        except Exception as e:
            print(f"❌ MCP 연결 실패 ({type(e).__name__}): {e}")
            # MCP 내부 에러 메시지 추출용
            import traceback
            traceback.print_exc()
            raise
    return _tools