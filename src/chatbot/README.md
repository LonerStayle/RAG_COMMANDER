# 🏠 주택 FAQ 챗봇 (LangGraph 기반)

주택 청약 및 분양에 대한 질문에 답변하는 AI 챗봇입니다. LangGraph를 사용하여 구조화된 워크플로우로 구현되었습니다.

## 📋 목차

- [특징](#특징)
- [시스템 아키텍처](#시스템-아키텍처)
- [설치](#설치)
- [실행 방법](#실행-방법)
- [사용법](#사용법)
- [API 문서](#api-문서)
- [프로젝트 구조](#프로젝트-구조)

## ✨ 특징

- **LangGraph 기반**: 구조화된 상태 머신으로 챗봇 워크플로우 구현
- **다중 데이터 소스**:
  - FAQ 데이터베이스
  - 주택공급규칙 데이터베이스
  - 정책 문서 (PDF)
- **하이브리드 검색**: 의미 기반 검색 + 키워드 검색
- **상세한 출처 표시**: 파일명, 페이지, 청크 정보 포함
- **PDF 업로드**: 새로운 정책 PDF를 DB에 추가 가능
- **스트리밍 지원**: 실시간 응답 생성
- **세션 관리**: 대화 기록 유지 및 관리

## 🏗️ 시스템 아키텍처

```
┌─────────────────────┐
│   Streamlit UI      │
│   (Port 8502)       │
└──────────┬──────────┘
           │
           │ HTTP/REST
           ▼
┌─────────────────────┐
│   FastAPI Server    │
│   (Port 8000)       │
└──────────┬──────────┘
           │
           │ LangGraph
           ▼
┌─────────────────────────────────┐
│   LangGraph Workflow            │
│                                 │
│   ┌───────────┐  ┌───────────┐│
│   │ FAQ       │  │  Rule     ││
│   │ Retriever │  │ Retriever ││
│   └─────┬─────┘  └─────┬─────┘│
│         │              │       │
│         │  ┌───────────▼─────┐│
│         └─►│ Policy Retriever││
│            └─────────┬───────┘│
│                      │         │
│            ┌─────────▼───────┐│
│            │   LLM Generate  ││
│            └─────────┬───────┘│
│                      │         │
│            ┌─────────▼───────┐│
│            │ Format Sources  ││
│            └─────────────────┘│
└─────────────────────────────────┘
           │
           ▼
┌─────────────────────┐
│  PostgreSQL         │
│  (Vector DB)        │
└─────────────────────┘
```

### 🔌 포트 정보

| 서비스 | 포트 | URL | 비고 |
|--------|------|-----|------|
| **챗봇 Streamlit** | 8502 | http://localhost:8502 | 새 챗봇 UI |
| **챗봇 FastAPI** | 8000 | http://localhost:8000 | 챗봇 백엔드 API |
| **보고서 Streamlit** | 8501 | http://localhost:8501 | 기존 보고서 생성기 |
| **보고서 FastAPI** | 8080 | http://localhost:8080 | 기존 보고서 백엔드 |

> ⚠️ 두 Streamlit 앱을 동시에 실행할 경우 **포트 충돌**이 발생하므로 반드시 다른 포트를 사용해야 합니다.

## 🔧 설치

### 1. 필수 요구사항

- Python 3.10+
- PostgreSQL (Vector DB용)
- 환경 변수 설정 (.env 파일)

### 2. 의존성 설치

```bash
# 프로젝트 루트로 이동
cd RAG_COMMANDER

# 가상환경 생성 (선택사항)
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 3. 환경 변수 설정

`.env` 파일을 생성하고 다음 내용을 추가:

```env
# OpenAI API
OPENAI_API_KEY=your_openai_api_key

# PostgreSQL Vector DB
PGVECTOR_CONNECTION_STRING=postgresql://user:password@localhost:5432/dbname

# 기타 설정
LOG_LEVEL=INFO
```

## 🚀 실행 방법

### 1. FastAPI 백엔드 실행

```bash
# backend 디렉토리로 이동
cd src/chatbot/backend

# FastAPI 서버 실행
python main.py

# 또는 uvicorn 직접 실행
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

서버가 실행되면 http://localhost:8000 에서 API에 접근할 수 있습니다.

### 2. Streamlit 프론트엔드 실행

새 터미널을 열고:

```bash
# frontend 디렉토리로 이동
cd src/chatbot/frontend

# Streamlit 앱 실행 (포트 8502 사용)
streamlit run streamlit_chat.py --server.port 8502
```

브라우저가 자동으로 열리며 http://localhost:8502 에서 챗봇 UI에 접근할 수 있습니다.

> ⚠️ **포트 충돌 주의**: 기존 보고서 생성기(`src/streamlit/web.py`)가 포트 8501을 사용 중이므로, 챗봇은 **포트 8502**를 사용합니다.

## 💬 사용법

### 1. 웹 UI 사용 (Streamlit)

1. **사업지 정보 입력** (선택사항):
   - 사업지 장소 (예: 서울특별시 강남구 역삼동)
   - 단지 타입 (예: 84타입)
   - 세대수 (예: 120세대)

2. **데이터 소스 선택**:
   - FAQ 데이터
   - 주택공급규칙 데이터
   - 정책문서 데이터

3. **PDF 업로드** (선택사항):
   - 새로운 정책 PDF 파일을 업로드하여 DB에 추가

4. **질문 입력**:
   - 채팅 입력창에 질문 입력
   - 실시간으로 AI 응답 확인

5. **출처 확인**:
   - 각 응답 아래의 "📄 참조 문서" 클릭
   - 상세한 출처 정보 확인 (파일명, 날짜, 페이지, 청크 등)

### 2. API 직접 사용

#### 일반 채팅 (POST /chat)

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "1세대 1주택자 청약 조건은?",
    "target_area": "서울특별시 강남구",
    "main_type": "84타입",
    "total_units": "120세대",
    "use_faq": true,
    "use_rule": true,
    "use_policy": true
  }'
```

#### 스트리밍 채팅 (POST /chat/stream)

```bash
curl -X POST "http://localhost:8000/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "생애최초 특별공급 자격은?",
    "use_faq": true,
    "use_rule": true,
    "use_policy": true
  }'
```

#### PDF 업로드 (POST /upload/pdf)

```bash
curl -X POST "http://localhost:8000/upload/pdf" \
  -F "file=@/path/to/policy.pdf"
```

## 📚 API 문서

FastAPI가 실행 중일 때, 다음 URL에서 자동 생성된 API 문서를 확인할 수 있습니다:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 주요 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/` | 헬스체크 |
| GET | `/health` | 서비스 상태 확인 |
| POST | `/chat` | 일반 채팅 (비스트리밍) |
| POST | `/chat/stream` | 스트리밍 채팅 |
| POST | `/upload/pdf` | PDF 업로드 및 DB 저장 |
| GET | `/chat/history/{session_id}` | 대화 기록 조회 |
| DELETE | `/chat/history/{session_id}` | 대화 기록 삭제 |

## 📁 프로젝트 구조

```
src/chatbot/
├── backend/
│   ├── main.py                      # FastAPI 서버 메인
│   ├── models.py                    # Pydantic 모델
│   ├── chatbot_state.py             # LangGraph 상태 정의
│   ├── chatbot_graph_agent.py       # LangGraph 그래프 구현
│   ├── chat_agent_langgraph.py      # LangGraph 에이전트 래퍼
│   └── chat_agent.py                # 기존 에이전트 (레거시)
├── frontend/
│   └── streamlit_chat.py            # Streamlit UI
└── README.md                        # 이 파일
```

## 🔍 LangGraph 워크플로우

챗봇은 다음과 같은 LangGraph 워크플로우로 동작합니다:

```
START
  ├─> retrieve_faq (FAQ 검색)
  ├─> retrieve_rule (규칙 검색)
  └─> retrieve_policy (정책 검색)
       │
       └─> generate_response (LLM 응답 생성)
            │
            └─> format_sources (출처 포맷팅)
                 │
                 └─> END
```

각 노드는 독립적으로 실행되며, 결과는 상태(state)에 저장됩니다.

## 🛠️ 트러블슈팅

### 1. 모듈을 찾을 수 없음 (ModuleNotFoundError)

```bash
# sys.path 문제인 경우, PYTHONPATH 설정
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"  # Unix/Linux/Mac
set PYTHONPATH=%PYTHONPATH%;%cd%\src  # Windows
```

### 2. PostgreSQL 연결 오류

- `.env` 파일의 `PGVECTOR_CONNECTION_STRING` 확인
- PostgreSQL 서버가 실행 중인지 확인
- pgvector 확장이 설치되어 있는지 확인

### 3. OpenAI API 키 오류

- `.env` 파일의 `OPENAI_API_KEY` 확인
- API 키가 유효한지 확인

### 4. PDF 업로드 실패

- 파일이 PDF 형식인지 확인
- 파일 크기가 적절한지 확인
- 서버 로그 확인 (`/logs` 디렉토리)

## 📝 예시 질문

- "1세대 1주택자는 어떤 청약 조건이 필요한가요?"
- "생애최초 특별공급 자격은 어떻게 되나요?"
- "청약 가점제와 추첨제의 차이는 무엇인가요?"
- "특별공급과 일반공급의 차이를 알려주세요."
- "재개발 아파트 청약은 어떻게 하나요?"
- "2025년 6월 27일 정책의 LTV 규제는?"

## 📄 라이선스

This project is licensed under the MIT License.

## 👥 기여

버그 리포트, 기능 제안, Pull Request를 환영합니다!

## 📧 문의

질문이나 문의사항은 이슈 트래커를 통해 남겨주세요.
