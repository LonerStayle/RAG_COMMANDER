# policy_agent_design 폴더 이해 및 통합 가이드

## 1. policy_agent_design 폴더의 핵심 개념

### 1.1 전체 구조
이 폴더는 부동산 정책 PDF를 분석하는 독립적인 시스템입니다. 현재 프로젝트(RAG_COMMANDER)에 통합하려면 다음 핵심 기능을 이해해야 합니다:

1. **SmartPDFLoader**: PDF를 로드하고 메타데이터 추출
2. **PolicyRetriever**: 하이브리드 검색 (의미 검색 + 키워드 검색)
3. **PolicyAnalysisAgent**: 재검색 로직이 있는 LangGraph 워크플로우

### 1.2 핵심 파일 설명

#### `real_estate_policy_agent.py` (가장 중요)
- **SmartPDFLoader 클래스** (54-209줄)
  - PDF를 로드하는 방법: pdfplumber → PyPDF2 → OCR 순서로 시도
  - 정책 날짜, 타입, 제목 자동 추출
  - 표 데이터를 텍스트로 변환

- **PolicyRetriever 클래스** (211-345줄)
  - 하이브리드 검색 구현
  - 의미 검색 70% + 키워드 검색 30% 결합
  - PGVector 사용

- **PolicyAnalysisAgent 클래스** (347-638줄)
  - LangGraph로 워크플로우 구성
  - 재검색 로직: retrieve → analyze → validate → 재검색 필요시 다시 retrieve
  - 최대 3번까지 재검색

#### `policy_prompt.yaml`
- 보고서 생성 형식 정의
- CONTEXT1의 프롬프트 형식으로 출력되게 하는 템플릿

#### `run_analysis.py`
- 실행 스크립트 예시
- interactive, batch, quick 모드 지원

## 2. 현재 프로젝트에 통합하는 방법

### 2.1 통합 전략

현재 프로젝트에는 이미 다음이 있습니다:
- PDF 로더: `src/tools/rag/document_loader/default_loader.py`의 `best_loader`
- 벡터 스토어: `src/tools/rag/vector_store.py`의 `get_pgvector_store`
- 정책 에이전트: `src/agents/analysis/policy_agent.py`

**통합 방법:**
1. policy_agent_design의 핵심 로직을 현재 프로젝트 구조에 맞게 변환
2. 기존 코드 재사용 (best_loader, get_pgvector_store)
3. 재검색 로직만 추가

### 2.2 필요한 작업 단계

#### 단계 1: 파일 해시 관리자 만들기
**목적**: 같은 파일을 중복으로 로드하지 않기 위해

**위치**: `src/tools/rag/document_loader/file_hash_manager.py`

**구현 예시**:
```python
import hashlib

class FileHashManager:
    def __init__(self):
        self.loaded_hashes = set()
    
    def get_file_hash(self, file_path: str) -> str:
        # MD5 해시 계산
        pass
    
    def is_file_loaded(self, file_path: str) -> bool:
        # 이미 로드된 파일인지 확인
        pass
    
    def mark_as_loaded(self, file_path: str) -> None:
        # 파일을 로드된 것으로 표시
        pass
```

**참고**: `policy_agent_design/README.md` 275-296줄 참고

#### 단계 2: 정책 PDF 로더 만들기
**목적**: PDF를 로드하고 정책 메타데이터 추출

**위치**: `src/tools/rag/document_loader/policy_pdf_loader.py`

**구현 방법**:
- **표 추출**: Docling 우선 사용 (이미 설치됨, 표 추출 성능 우수)
- **텍스트 추출**: Docling 또는 현재 프로젝트의 `best_loader` 함수 사용
- `real_estate_policy_agent.py`의 SmartPDFLoader 클래스 참고 (54-209줄)
- 정책 날짜, 타입, 제목 추출 로직 가져오기

**Docling 사용 예시** (표 추출에 우수):
```python
from docling.document_converter import DocumentConverter

converter = DocumentConverter()
result = converter.convert(file_path)

# 표 추출
for table in result.document.tables:
    # 표를 텍스트로 변환
    table_text = table.to_markdown()  # 또는 table.to_dict()
```

**표 추출 전략**:
1. **Docling 시도** (복잡한 표, 병합 셀, 스캔 PDF의 표 추출에 우수)
2. **pdfplumber 시도** (간단한 표, 빠른 처리 속도)
3. **best_loader 사용** (일반 텍스트 추출)

**핵심 함수**:
```python
def load_pdf(file_path: str) -> PolicyDocument:
    # 1. Docling으로 PDF 로드 시도 (표 추출 우선)
    #    - 표가 있으면 Docling 사용
    #    - 표가 없거나 실패하면 pdfplumber 또는 best_loader 사용
    # 2. 표 데이터를 텍스트로 변환
    # 3. 정책 날짜 추출 (_extract_policy_date)
    # 4. 정책 타입 판별 (_determine_policy_type)
    # 5. 제목 추출 (_extract_title)
    # 6. PolicyDocument 반환
```

**참고**: TATR(Table Transformer)은 더 정확하지만 별도 설치가 필요합니다. Docling이 이미 설치되어 있고 표 추출 성능이 우수하므로 Docling을 우선 사용하는 것을 권장합니다.

#### 단계 3: 정책 Retriever 만들기
**목적**: 하이브리드 검색 구현

**위치**: `src/tools/rag/retriever/policy_pdf_retriever.py`

**구현 방법**:
- `real_estate_policy_agent.py`의 PolicyRetriever 클래스 참고 (211-345줄)
- 현재 프로젝트의 `get_pgvector_store` 사용
- 하이브리드 검색 로직 구현

**핵심 함수**:
```python
def hybrid_search(query: str, k: int = 5) -> List[Document]:
    # 1. semantic_search 수행 (의미 검색)
    # 2. keyword_search 수행 (키워드 검색)
    # 3. 두 결과를 점수로 결합
    # 4. 점수순 정렬 후 상위 k개 반환
```

#### 단계 4: 정책 에이전트에 재검색 로직 추가
**목적**: 검색 결과가 부적절하면 자동 재검색

**위치**: `src/agents/analysis/policy_agent.py` 수정

**구현 방법**:
- `real_estate_policy_agent.py`의 PolicyAnalysisAgent 참고 (347-638줄)
- LangGraph 워크플로우에 재검색 노드 추가

**워크플로우 예시**:
```
START → national_news
     → region_news
     → policy_pdf_retrieve (신규)
     → validate_retrieval (신규: 검색 결과 검증)
     → [재검색 필요시] → policy_pdf_retrieve
     → [완료시] → analysis_setting
     → agent
```

**핵심 함수**:
```python
def policy_pdf_retrieve(state: PolicyState) -> PolicyState:
    # 1. 검색 쿼리 생성
    # 2. retriever.hybrid_search 호출
    # 3. 검색 결과를 state에 저장
    pass

def validate_retrieval(state: PolicyState) -> PolicyState:
    # 1. 검색 결과가 충분한지 확인
    # 2. 부족하면 재검색 플래그 설정
    pass

def should_retry_retrieval(state: PolicyState) -> str:
    # 재검색 필요 여부 판단
    # "retry" 또는 "continue" 반환
    pass
```

#### 단계 5: 인덱싱 스크립트 만들기
**목적**: PDF 파일을 벡터 DB에 인덱싱

**위치**: `src/tools/rag/indexing/policy_pdf_indexing.py`

**구현 방법**:
- `run_analysis.py` 참고
- PDF 파일 목록을 받아서 인덱싱

**핵심 함수**:
```python
def index_policy_files(file_paths: List[str]) -> None:
    # 1. 각 파일을 policy_pdf_loader로 로드
    # 2. policy_pdf_retriever.add_documents 호출
    pass
```

## 3. 필요한 라이브러리

### 필수 라이브러리 (requirements.txt에 추가)
```
pdfplumber==0.10.3
PyPDF2==3.0.1
pdf2image==1.16.3  # OCR 사용시만
pytesseract==0.3.10  # OCR 사용시만
```

### UV 가상환경에서 설치
```bash
uv pip install pdfplumber PyPDF2
```

### Windows에서 추가 설치 (OCR 사용시만)
- Tesseract OCR: https://github.com/UB-Mannheim/tesseract/wiki
- Poppler: pdf2image 사용을 위해 필요

## 4. 구현 순서 추천

1. **파일 해시 관리자** (가장 단순)
   - MD5 해시 계산만 하면 됨

2. **정책 PDF 로더**
   - Docling 우선 사용 (표 추출 성능 우수, 이미 설치됨)
   - 기존 best_loader 활용 (폴백)
   - 메타데이터 추출 로직 추가

3. **정책 Retriever**
   - 하이브리드 검색 구현
   - 기존 get_pgvector_store 활용

4. **정책 에이전트 수정**
   - 재검색 로직 추가
   - 워크플로우 수정

5. **인덱싱 스크립트**
   - 위의 컴포넌트들을 조합

## 5. 참고할 코드 위치

### policy_agent_design 폴더에서 참고할 부분

1. **PDF 로더**: `real_estate_policy_agent.py` 54-209줄
   - `load_pdf` 메서드: PDF 로드 로직
   - `_extract_policy_date`: 날짜 추출
   - `_determine_policy_type`: 타입 판별
   - `_extract_title`: 제목 추출

2. **Retriever**: `real_estate_policy_agent.py` 211-345줄
   - `hybrid_search`: 하이브리드 검색 로직
   - `semantic_search`: 의미 검색
   - `keyword_search`: 키워드 검색
   - `_extract_keywords`: 키워드 추출

3. **Agent**: `real_estate_policy_agent.py` 347-638줄
   - `retrieve_information`: 검색 노드
   - `validate_analysis`: 검증 노드
   - `should_continue_analysis`: 재검색 판단
   - `create_analysis_graph`: 워크플로우 생성

### 현재 프로젝트에서 재사용할 부분

1. **PDF 로더**: `src/tools/rag/document_loader/default_loader.py`
   - `best_loader` 함수 사용 (폴백)
   - **Docling**: 표 추출에 우수 (이미 설치됨)

2. **벡터 스토어**: `src/tools/rag/vector_store.py`
   - `get_pgvector_store` 함수 사용

3. **텍스트 분할**: `src/tools/rag/chunker/default_chunker.py`
   - `chunk_with_recursive` 함수 참고

## 6. 주의사항

1. **파일 중복**: 해시 기반으로 체크하지만, 같은 파일을 다시 인덱싱하면 중복될 수 있음
2. **벡터 DB**: PostgreSQL에 pgvector 확장이 설치되어 있어야 함
3. **재검색 로직**: 최대 재시도 횟수 설정 필요 (예: 3번)
4. **검증 기준**: 검색 결과가 충분한지 판단하는 기준 필요 (예: 텍스트 길이 100자 이상)

## 7. 테스트 방법

각 단계마다 테스트:
1. 파일 해시 관리자: 같은 파일 두 번 로드 시도
2. PDF 로더: PDF 파일 하나 로드해서 메타데이터 확인
3. Retriever: 간단한 쿼리로 검색 테스트
4. 에이전트: 전체 워크플로우 테스트

## 8. 다음 단계

1. 위 순서대로 하나씩 구현
2. 각 단계 완료 후 테스트
3. 문제 발생 시 policy_agent_design 폴더의 코드 참고
4. 현재 프로젝트의 기존 코드 재사용 최대화

