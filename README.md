.env 파일 생성해서 아래와 같이 세팅해주세요. 
.gitignore 에 .env 작성 필수 입니다. 

LANGSMITH_API_KEY=...   
LANGSMITH_TRACING=...   
TAVILY_API_KEY=...   
OPENAI_API_KEY=...   

(옵션) MATHPIX 파싱 쓰실 분은 아래를 세팅해주세요 
MATHPIX_API_KEY=...   
MATHPIX_API_ID=...


# PostgreSQL 로컬 세팅법 

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