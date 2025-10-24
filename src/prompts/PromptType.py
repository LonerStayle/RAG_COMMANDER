from enum import Enum
from pathlib import Path
from utils.util import get_project_root


class PromptType(Enum):
    SYSTEM_MAIN = (
        "SYSTEM_MAIN",
         f"{get_project_root()}\src\prompts\main_prompts.yaml",
        "메인 에이전트의 시스템 메시지",
    )

    def __init__(self, value, path, description):
        self._value_ = value   # ✅ Enum의 내부 value는 _value_ 로 할당
        self.path = path
        self.description = description

    def to_dict(self):
        return {"path": self.path, "description": self.description}
