import inspect
from typing import get_type_hints, Type

def build_tool_prompt(tools: list):
    text = "사용 가능한 도구 목록:\n\n"
    for tool in tools:
        sig = inspect.signature(tool)
        doc = inspect.getdoc(tool)
        text += f"- {tool.__name__}{sig}\n  설명: {doc}\n\n"
    return text



def build_tool_prompt(tools: list):
    text = "사용 가능한 도구 목록:\n\n"
    for tool in tools:
        sig = inspect.signature(tool)  # 함수의 (a:int, b:int) 시그니처
        doc = inspect.getdoc(tool)     # """ """ 안의 docstring
        text += f"- {tool.__name__}{sig}\n  설명: {doc}\n\n"
    return text


async def process_stream(stream_generator):
    results = []
    try:
        async for chunk in stream_generator:
            key = list(chunk.keys())[0]
            
            if key == 'agent':
                # Agent 메시지의 내용을 가져옵니다. 메시지가 비어있는 경우 어떤 도구를 어떻게 호출할지 정보를 가져옵니다.
                content = chunk['agent']['messages'][0].content if chunk['agent']['messages'][0].content != '' else chunk['agent']['messages'][0].additional_kwargs
                print(f"'agent': '{content}'")
            
            elif key == 'tools':
                for tool_msg in chunk['tools']['messages']:
                    print(f"'tools:': '{tool_msg.content}'")
                    
            results.append(chunk)
        return results
    except Exception as e:
        print(f'Error processing stream: {e}')
        return results
    
import inspect
from typing import get_type_hints, TypeVar, Type, Any

T = TypeVar("T")

def attach_auto_keys(cls: Type[T]) -> Type[T]:
    """클래스 정의 이후 자동으로 Key 클래스를 주입합니다 (TypedDict, BaseModel, MessagesState 전부 호환)."""
    annotations: dict[str, Any] = {}
    for base in reversed(cls.__mro__):
        try:
            hints = get_type_hints(base, include_extras=True)
        except Exception:
            hints = getattr(base, "__annotations__", {})
        annotations.update(hints or {})

    if not annotations:
        annotations = {
            k: v for k, v in vars(cls).items()
            if not k.startswith("_") and not inspect.isroutine(v)
        }
    key_cls = type(
        "KEY",
        (),
        {k: k for k in annotations.keys()}
    )
    setattr(cls, "KEY", key_cls)
    return cls


from datetime import datetime

def get_today_str(pattern="%a %b %d, %Y"):
    return datetime.now().strftime(pattern)


from pathlib import Path
def get_current_dir() -> Path:
    return Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()

def get_project_root(marker="pyproject.toml"): # 현재 프로젝트의 경로를 가져오기 위해 사용용
    cur = Path(__file__).resolve() if "__file__" in globals() else Path().resolve()
    return next((p for p in [cur, *cur.parents] if (p / marker).exists()), cur)    