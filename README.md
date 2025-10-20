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
```docker run -d --name rag_pg -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=ragdb -p 5433:5433 -v "%cd%/pgdata:/var/lib/postgresql/data" postgres:16 -c shared_preload_libraries=vector```

포트: localhost:5433  
계정: postgres / postgres  
데이터베이스: ragdb  
vector 확장 모듈 자동 로드


### 2. pgAdmin 실행  
```docker run -d --name rag_pgadmin -e PGADMIN_DEFAULT_EMAIL=admin@local.com -e PGADMIN_DEFAULT_PASSWORD=admin -p 5050:80 dpage/pgadmin4```   
   
브라우저에서 http://localhost:5050 접속

Email: admin@local.com   
Password: admin


### 3. pgvector 확장 활성화 (최초 1회만)
```docker exec -it rag_pg psql -U postgres -d ragdb -c "CREATE EXTENSION IF NOT EXISTS vector;"```

확인
```docker exec -it rag_pg psql -U postgres -d ragdb -c "\dx"```
vector 가 보이면 OK 
   

### 4. env 설정 
```POSTGRES_URL=postgresql+psycopg2://postgres:postgres@localhost:5433/ragdb```

### 5. pgAdmin에서 DB 연결

- “Add New Server”
- Host name/address: host.docker.internal
(Windows Docker Desktop 기준)
- Port: 5433
- Username: postgres
- Password: postgres