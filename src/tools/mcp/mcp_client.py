from langchain_mcp_adapters import MultiServerMCPClient
from dotenv import load_dotenv
import os, platform

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
    global _client
    if _client is None: 
        _client = MultiServerMCPClient(
            {
                "exa": get_exa_config()
            }
        )

async def get_tools():
    global _tools
    if _tools is None:
        client = await get_client()