from enum import StrEnum

class ModelName(StrEnum):
    GPT_4_1_MINI = "gpt-4.1-mini"
    GPT_4_1 = "gpt-4.1"
    GPT_5_MINI = "gpt-5-mini"
    GPT_5 = "gpt-5"
    GPT_5_PRO = "gpt-5-pro-2025-10-06"

    CLAUDE_OPUS_4_1_20250805 = "claude-opus-4-1-20250805"
    CLAUDE_SONNET_4_5_20250929 = "claude-sonnet-4-5-20250929"
    
class LLMProfile(StrEnum):
    DEV_ROUTE = ModelName.GPT_4_1_MINI
    
    START_COMFIRMATION = ModelName.GPT_4_1_MINI
    
    # 테스트 끝나면 GPT 5 사용 예정
    ANALYSIS = ModelName.GPT_4_1_MINI
    
    # 테스트 끝나면 클로드 사용예정
    REPORT = ModelName.CLAUDE_SONNET_4_5_20250929
    
    
    