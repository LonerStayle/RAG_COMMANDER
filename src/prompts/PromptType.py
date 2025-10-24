from enum import Enum
from pathlib import Path
from utils.util import get_project_root


class PromptType(Enum):
    
    def __init__(self, value, path, description):
        self._value_ = value   # ✅ Enum의 내부 value는 _value_ 로 할당
        self.path = path
        self.description = description

    def to_dict(self):
        return {"path": self.path, "description": self.description}


    MAIN_START_CONFIRMATION = (
        "MAIN_START_CONFIRMATION",
        str(Path(get_project_root()) / "src" / "prompts" / "main_prompts.yaml"),
        "메인 에이전트의 시작 여부 확인 메시지",
    )
    
    MAIN_START = (
        "MAIN_START",
        str(Path(get_project_root()) / "src" / "prompts" / "main_prompts.yaml"),
        "메인 에이전트의 보고서 작성 시작 메시지",
    )
    
    JUNG_MIN_JAE_SYSTEM = (
        "JUNG_MIN_JAE_SYSTEM",
        str(Path(get_project_root()) / "src" / "prompts" / "jung_min_jae_prompts.yaml"),
        "정민재 이사의 생각이 담긴 시스템 메시지",
    )
    
    