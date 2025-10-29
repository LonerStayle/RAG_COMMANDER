# 세팅 방식 - 궁금한거 언제든지 질문 주십쇼

## 1. 주요 패키지 설명

- agents : 에이전트 관리 패키지 입니다.
  - .state -> 랭그래프의 상태가 정의되어 있습니다.
  - .main -> 전체 워크플로우를 뜻합니다.
  - .analysis -> 1단계 분석용 병렬 에이전트 모음
  - .jung_min_jae -> 2단계 정민재 에이전트 

- data : pdf, csv 등 각종 데이터 파일을 관리하는 패키지 입니다
- lab : 연구소, 프로젝트 상관없이 각종 코드 테스트 하는 공간 입니다. 
- prompts: 여러 프롬프트 관리 패키지 입니다. 특별한 경우가 없으면 모든 프롬프트를 이곳에서 관리 합니다.
- tools : 에이전트의 도구들을 관리합니다.
  - rag -> rag 관련 모음 입니다. (문서 파싱, 청킹, 벡터스토어, 리트리버 객체 등)
  - mcp -> mcp 관련 모음 입니다. 

- utils : 개발자에게 각종 편의를 위해 제공하는 패키지입니다.

## 2. 코드 컨벤션
- **prompt 사용법**
```
# 1단계
"""PromptType 에서 사용하고자 하는 프롬프트를 고릅니다."""

class PromptType(Enum):
...

LOCATION_INSIGHT_SYSTEM = (
  ...yaml 
)

"""예시로 LOCATION_INSIGHT_SYSTEM를 골랐다고 가정하겠습니다.
yaml 경로를 파악해서 킨다음 내부 데이터를 보고 input_variables 의 내용을 봅니다.
"""
input_variables:
- messages 

```


```
# 2단계
"""PromptManager를 사용하면서 위 골랐던 PromptType.LOCATION_INSIGHT_SYSTEM 를 넣어줍니다."""

# 실제 프롬프트를 가져와 사용하는곳에서 다음과 같이 사용하면 됩니다. 
# yaml 파일에서 확인했던 input_variables 를 보고 get_prompt 안에 다음과  같이 채워주시면 됩니다. messages_str 은 내가 넣을 데이터입니다. 변수명 아무렇게나 써서 넣으셔도 됩니다.

prompt = PromptManager(PromptType.LOCATION_INSIGHT_SYSTEM).get_prompt(
    messages=messages_str
)

```

- **LangGraph 내의 키 사용법**
```
"""상태 클래스를 생성했다면 
 attach_auto_keys를 가져와서 만든 클래스 위에 @attach_auto_keys 를 붙여 줍니다. (이미 만들어진건 제가 다해놨습니다.)"""

... 생략 ...
from utils.util import attach_auto_keys

@attach_auto_keys
class LocationInsightState(TypedDict):
    start_input: dict
    ...
```

```
"""랭그래프 파일 .py 
상단에 아래와 같이 사용해주면 됩니다."""

# 사용할 상태.KEY.사용할 키 
start_input_key = LocationInsightState.KEY.start_input
```

```
# 전체 예시
from utils.util import attach_auto_keys

@attach_auto_keys
class AgentState(TypedDict):
    start_input: dict
    ...생략...

start_input_key = AgentStateAgentState.KEY.start_input

def agent(state:AgentState):
  start_input = state[start_input_key]
  ... 생략 ...
```

- **tools 폴더 이용법**


```tools 폴더에 예를들어 내가 테스트 하고자하는 도구 코드가 있다면 .ipynb 버전과 .py 버전을 둘다 사용하시면 됩니다.```

```
# 예시 
maps.ipynb
maps.py 
```


- **LLM 호출법**
```
utils.llm 폴더에 
LLMProfile 이라는 클래스가 있습니다.

```


## 9. .env 세팅
.env 파일 생성해서 아래와 같이 세팅해주세요. 
.gitignore 에 .env 작성 필수 입니다. 

LANGSMITH_API_KEY=...   
LANGSMITH_TRACING=...(false 권장)   
TAVILY_API_KEY=...   
OPENAI_API_KEY=...   
R_ONE_API_KEY= ...   
POSTGRES_URL= ...   
MCP_KEY = ...   
PERPLEXITY_API_KEY= ...   
ANTHROPIC_API_KEY= ...   

(옵션) MATHPIX 파싱 쓰실 분은 아래를 세팅해주세요    
MATHPIX_API_KEY=...   
MATHPIX_API_ID=...


# 10. PostgreSQL 로컬 세팅법 

### 1. 도커 실행후 postgres 계정 생성   

docker run -d `
  --name rag_pg `
  -e POSTGRES_USER=postgres `
  -e POSTGRES_PASSWORD=postgres `
  -e POSTGRES_DB=ragdb `
  -p 5432:5432 `
  -v ${PWD}/pgdata:/var/lib/postgresql/data `
  ankane/pgvector:latest

포트: localhost:5432  
계정: postgres / postgres  
데이터베이스: ragdb  
vector 확장 모듈 자동 로드


### 2. pgvector 확장 활성화 (최초 1회만)
```docker exec -it rag_pg psql -U postgres -d ragdb -c 'CREATE EXTENSION IF NOT EXISTS vector;'```

확인
```docker exec -it rag_pg psql -U postgres -d ragdb -c '\dx'```
vector 가 보이면 OK 
   

### 3. env 설정 
```POSTGRES_URL=postgresql://postgres:postgres@localhost:5432/ragdb```

### 4. pgAdmin에서 DB 연결
- “Add New Server”
- Host name/address: host.docker.internal
(Windows Docker Desktop 기준)
- Port: 5432
- Username: postgres
- Password: postgres


## 진섭 개인 노트북 문제 해결 커맨드 
code --uninstall-extension ms-toolsai.jupyter
code --install-extension ms-toolsai.jupyter  