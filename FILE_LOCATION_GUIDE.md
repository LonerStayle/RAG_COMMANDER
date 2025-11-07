# 구현할 파일 위치 및 구조 가이드

## 파일 구조 요약

```
C:\RAG_COMMANDER\
├── src\
│   ├── tools\
│   │   └── rag\
│   │       ├── document_loader\
│   │       │   ├── file_hash_manager.py          ✅ 이미 있음 (14줄)
│   │       │   ├── policy_pdf_loader.py          ⬅️ 여기에 만들기
│   │       │   └── policy_file_loader.py         ⬅️ 여기에 만들기
│   │       ├── retriever\
│   │       │   └── policy_pdf_retriever.py       ⬅️ 여기에 만들기
│   │       └── indexing\
│   │           └── policy_pdf_indexing.py        ⬅️ 여기에 만들기
│   └── agents\
│       └── analysis\
│           └── policy_agent.py                    ⬅️ 여기 수정하기
```

## 1. 파일 해시 관리자 (이미 있음)

**위치**: `src/tools/rag/document_loader/file_hash_manager.py`

**상태**: 이미 파일이 있음 (14줄)

**확인사항**: 파일 내용이 완성되어 있는지 확인하고, 필요시 완성하세요.

---

## 2. 정책 PDF 로더 (새로 만들기)

**위치**: `src/tools/rag/document_loader/policy_pdf_loader.py`

**파일 생성**: 이 경로에 새 파일 생성

**필요한 import**:
```python
import os
import re
from typing import List, Dict, Any
from dataclasses import dataclass
from enum import Enum
from langchain_core.documents import Document

# 현재 프로젝트의 기존 코드 사용
from tools.rag.document_loader.default_loader import best_loader
from tools.rag.document_loader.file_hash_manager import file_hash_manager

# Docling 사용 (표 추출)
from docling.document_converter import DocumentConverter
```

**필요한 클래스/함수**:
1. `PolicyType` (Enum) - 정책 타입 정의
2. `PolicyDocument` (dataclass) - 정책 문서 데이터 구조
3. `PolicyPDFLoader` (클래스) - PDF 로더
   - `load_pdf(file_path: str) -> PolicyDocument`
   - `_extract_policy_date(content: str, file_path: str) -> str`
   - `_determine_policy_type(content: str, file_path: str) -> PolicyType`
   - `_extract_title(content: str, file_path: str) -> str`

**참고 코드**: `policy_agent_design/real_estate_policy_agent.py` 37-209줄

---

## 3. 통합 파일 로더 (새로 만들기)

**위치**: `src/tools/rag/document_loader/policy_file_loader.py`

**파일 생성**: 이 경로에 새 파일 생성

**필요한 import**:
```python
import os
import json
import re
from typing import Dict, Any
from pathlib import Path

from tools.rag.document_loader.policy_pdf_loader import (
    PolicyPDFLoader,
    PolicyDocument,
    PolicyType
)
from tools.rag.document_loader.file_hash_manager import file_hash_manager
```

**필요한 클래스**:
- `PolicyFileLoader` (클래스)
  - `load_file(file_path: str) -> PolicyDocument`
  - `_load_pdf(file_path: str) -> PolicyDocument`
  - `_load_markdown(file_path: str) -> PolicyDocument`
  - `_load_json(file_path: str) -> PolicyDocument`

**참고 코드**: `policy_agent_design/README.md` 238-273줄

---

## 4. 정책 PDF Retriever (새로 만들기)

**위치**: `src/tools/rag/retriever/policy_pdf_retriever.py`

**파일 생성**: 이 경로에 새 파일 생성

**필요한 import**:
```python
import re
from typing import List, Optional, Dict
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from tools.rag.vector_store import get_pgvector_store
from tools.rag.document_loader.policy_file_loader import PolicyDocument
```

**필요한 상수**:
```python
POLICY_DOCUMENTS_COLLECTION = "policy_documents"
```

**필요한 클래스**:
- `PolicyPDFRetriever` (클래스)
  - `__init__(self)`
  - `add_documents(policy_documents: List[PolicyDocument]) -> None`
  - `semantic_search(query: str, k: int = 5) -> List[Document]`
  - `keyword_search(keywords: List[str], k: int = 5) -> List[Document]`
  - `hybrid_search(query: str, keywords: Optional[List[str]] = None, semantic_weight: float = 0.7, k: int = 5) -> List[Document]`
  - `_extract_keywords(query: str) -> List[str]`

**참고 코드**: `policy_agent_design/real_estate_policy_agent.py` 211-345줄

---

## 5. 인덱싱 스크립트 (새로 만들기)

**위치**: `src/tools/rag/indexing/policy_pdf_indexing.py`

**파일 생성**: 이 경로에 새 파일 생성

**필요한 import**:
```python
import os
from pathlib import Path
from typing import List

from tools.rag.document_loader.policy_file_loader import policy_file_loader, PolicyDocument
from tools.rag.retriever.policy_pdf_retriever import PolicyPDFRetriever
from utils.util import get_project_root
```

**필요한 함수**:
- `index_policy_files(file_paths: List[str]) -> None`
- `index_policy_directory(directory_path: str) -> None`
- `main()` (선택사항)

**참고 코드**: `policy_agent_design/run_analysis.py` 65-159줄

---

## 6. 정책 에이전트 수정 (기존 파일 수정)

**위치**: `src/agents/analysis/policy_agent.py`

**파일 수정**: 기존 파일에 함수 추가

**추가할 import**:
```python
from tools.rag.retriever.policy_pdf_retriever import PolicyPDFRetriever
```

**추가할 함수**:
- `policy_pdf_retrieve(state: PolicyState) -> PolicyState`
- `validate_retrieval(state: PolicyState) -> PolicyState`
- `should_retry_retrieval(state: PolicyState) -> str`

**수정할 함수**:
- `analysis_setting(state: PolicyState) -> PolicyState` - PDF 컨텍스트 추가

**워크플로우 수정**: 그래프에 노드와 엣지 추가

**참고 코드**: `policy_agent_design/real_estate_policy_agent.py` 409-493줄

---

## 7. State 수정 (선택사항)

**위치**: `src/agents/state/analysis_state.py`

**수정 내용**: `PolicyState`에 필드 추가 (필요시)

**추가할 필드** (필요한 경우):
- `pdf_context: Optional[str]`
- `retry_count: Optional[int]`

**참고**: 현재 프로젝트 구조에 맞게 수정 필요

---

## 구현 순서

1. **file_hash_manager.py** 확인 및 완성
   - 위치: `src/tools/rag/document_loader/file_hash_manager.py`
   - 이미 있으므로 내용 확인

2. **policy_pdf_loader.py** 생성
   - 위치: `src/tools/rag/document_loader/policy_pdf_loader.py`
   - 새 파일 생성

3. **policy_file_loader.py** 생성
   - 위치: `src/tools/rag/document_loader/policy_file_loader.py`
   - 새 파일 생성

4. **policy_pdf_retriever.py** 생성
   - 위치: `src/tools/rag/retriever/policy_pdf_retriever.py`
   - 새 파일 생성

5. **policy_pdf_indexing.py** 생성
   - 위치: `src/tools/rag/indexing/policy_pdf_indexing.py`
   - 새 파일 생성

6. **policy_agent.py** 수정
   - 위치: `src/agents/analysis/policy_agent.py`
   - 기존 파일 수정

---

## 각 파일의 기본 구조 예시

### policy_pdf_loader.py 기본 구조
```python
"""
정책 PDF 로더
PDF 파일을 로드하고 정책 메타데이터를 추출합니다.
"""

import os
import re
from typing import List, Dict, Any
from dataclasses import dataclass
from enum import Enum

from tools.rag.document_loader.default_loader import best_loader
from tools.rag.document_loader.file_hash_manager import file_hash_manager
from docling.document_converter import DocumentConverter

class PolicyType(Enum):
    """정책 문서의 유형"""
    LOAN_REGULATION = "대출규제"
    HOUSING_MARKET = "주택시장"
    TAX_POLICY = "세제정책"
    SUPPLY_POLICY = "공급정책"
    UNKNOWN = "기타"

@dataclass
class PolicyDocument:
    """정책 문서의 메타데이터와 내용"""
    file_path: str
    policy_date: str
    policy_type: PolicyType
    title: str
    content: str
    metadata: Dict[str, Any]

class PolicyPDFLoader:
    """정책 PDF 파일을 로드하는 클래스"""
    
    def load_pdf(self, file_path: str) -> PolicyDocument:
        """PDF 파일을 로드하고 메타데이터 추출"""
        # 여기에 구현
        pass
    
    def _extract_policy_date(self, content: str, file_path: str) -> str:
        """정책 날짜 추출"""
        # 여기에 구현
        pass
    
    def _determine_policy_type(self, content: str, file_path: str) -> PolicyType:
        """정책 타입 판별"""
        # 여기에 구현
        pass
    
    def _extract_title(self, content: str, file_path: str) -> str:
        """제목 추출"""
        # 여기에 구현
        pass

# 전역 인스턴스
policy_pdf_loader = PolicyPDFLoader()
```

### policy_pdf_retriever.py 기본 구조
```python
"""
정책 PDF Retriever
하이브리드 검색을 구현한 Retriever입니다.
"""

import re
from typing import List, Optional, Dict
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from tools.rag.vector_store import get_pgvector_store
from tools.rag.document_loader.policy_file_loader import PolicyDocument

POLICY_DOCUMENTS_COLLECTION = "policy_documents"

class PolicyPDFRetriever:
    """정책 문서 검색 시스템"""
    
    def __init__(self):
        """초기화"""
        self.vector_store = get_pgvector_store(POLICY_DOCUMENTS_COLLECTION)
        self.documents_cache = []
    
    def add_documents(self, policy_documents: List[PolicyDocument]) -> None:
        """정책 문서를 벡터 스토어에 추가"""
        # 여기에 구현
        pass
    
    def semantic_search(self, query: str, k: int = 5) -> List[Document]:
        """의미 기반 검색"""
        # 여기에 구현
        pass
    
    def keyword_search(self, keywords: List[str], k: int = 5) -> List[Document]:
        """키워드 기반 검색"""
        # 여기에 구현
        pass
    
    def hybrid_search(self, query: str, keywords: Optional[List[str]] = None, 
                      semantic_weight: float = 0.7, k: int = 5) -> List[Document]:
        """하이브리드 검색"""
        # 여기에 구현
        pass
    
    def _extract_keywords(self, query: str) -> List[str]:
        """키워드 추출"""
        # 여기에 구현
        pass
```

---

## 참고할 파일 위치

### policy_agent_design 폴더에서 참고
- **PDF 로더**: `policy_agent_design/real_estate_policy_agent.py` 54-209줄
- **Retriever**: `policy_agent_design/real_estate_policy_agent.py` 211-345줄
- **Agent**: `policy_agent_design/real_estate_policy_agent.py` 347-638줄

### 현재 프로젝트에서 재사용
- **PDF 로더**: `src/tools/rag/document_loader/default_loader.py`의 `best_loader`
- **벡터 스토어**: `src/tools/rag/vector_store.py`의 `get_pgvector_store`
- **텍스트 분할**: `src/tools/rag/chunker/default_chunker.py`의 `chunk_with_recursive`
- **기존 Retriever 예시**: `src/tools/rag/retriever/national_policy_retriever.py` 참고

---

## 주의사항

1. **경로**: 모든 경로는 Windows 형식 (`C:\RAG_COMMANDER\...`)
2. **import 경로**: `from tools.rag.xxx import yyy` 형식 사용
3. **파일명**: 소문자와 언더스코어 사용 (`policy_pdf_loader.py`)
4. **클래스명**: 파스칼 케이스 사용 (`PolicyPDFLoader`)
5. **함수명**: 소문자와 언더스코어 사용 (`load_pdf`)

