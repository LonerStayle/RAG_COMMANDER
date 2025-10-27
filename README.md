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
- prompt 사용법
```
# 1단계 -> PromptType 에서 사용하고자 하는 프롬프트를 고릅니다.
```

```
# 2단계 -> PromptManager를 사용하면서 위 PromptType 를 넣어줍니다.
prompt = PromptManager(PromptType.).get_prompt(
    messages=messages_str
)

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