from enum import StrEnum
from langchain.chat_models import init_chat_model


class ModelName(StrEnum):
    GPT_4_1_MINI = "gpt-4.1-mini"
    GPT_4_1 = "gpt-4.1"
    GPT_5_MINI = "gpt-5-mini"
    GPT_5 = "gpt-5"
    GPT_5_PRO = "gpt-5-pro-2025-10-06"

    CLAUDE_OPUS_4_1_20250805 = "claude-opus-4-1-20250805"
    CLAUDE_SONNET_4_5_20250929 = "claude-sonnet-4-5-20250929"


class LLMProfile(StrEnum):
    # 개발자가 사용할 LLM 
    DEV = ModelName.GPT_4_1_MINI

    # 챗봇용 LLM   
    CHAT_BOT = ModelName.GPT_4_1

    # 분석용 LLM
    ANALYSIS = ModelName.GPT_5

    # 보고서 작성용 LLM
    REPORT = ModelName.GPT_5
    
    @staticmethod
    def dev_llm():
        return init_chat_model(
            model=LLMProfile.DEV,
            temperature=0,
        )
    @staticmethod
    def chat_bot_llm():
        return init_chat_model(
            model=LLMProfile.CHAT_BOT,
            temperature=0,
        )
    
    @staticmethod
    def chat_llm():
        return init_chat_model(
            model=LLMProfile.CHAT_BOT,
            temperature=0,
            reasoning_effort="high",
            verbosity="high",
        )

    @staticmethod
    def analysis_llm():
        
        return init_chat_model(
            model=LLMProfile.ANALYSIS,
            temperature=0,
            reasoning_effort="high",
            verbosity="high",
        )

    @staticmethod
    def report_llm():
        return init_chat_model(
            model=LLMProfile.REPORT,
            temperature=0,
        )
