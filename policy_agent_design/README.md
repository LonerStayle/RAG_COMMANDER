# 📘 부동산 정책 비교 분석 Agent 시스템 사용 가이드

## 목차
1. [시스템 개요](#시스템-개요)
2. [설치 방법](#설치-방법)
3. [시스템 아키텍처](#시스템-아키텍처)
4. [핵심 기능](#핵심-기능)
5. [사용 방법](#사용-방법)
6. [PDF 추가 가이드](#pdf-추가-가이드)
7. [트러블슈팅](#트러블슈팅)

---

## 🎯 시스템 개요

이 시스템은 부동산 정책 PDF 문서들을 자동으로 분석하고, YAML 프롬프트 형식에 따라 정책 비교 보고서를 생성하는 AI Agent 시스템입니다.

### 주요 특징
- ✅ **지능형 PDF 처리**: 텍스트, 스캔 이미지, 표 데이터 모두 처리
- ✅ **하이브리드 검색**: 의미 기반 + 키워드 기반 검색 조합
- ✅ **자가 검증**: 검색 결과가 부적절하면 자동 재검색
- ✅ **사업지 맞춤 분석**: 특정 사업지에 미치는 영향 분석

---

## 🛠️ 설치 방법

### 1. 필수 패키지 설치

```bash
pip install -r requirements.txt
```

### 2. PostgreSQL 설정 (선택사항)

```bash
# PostgreSQL 설치
sudo apt-get install postgresql postgresql-contrib

# 데이터베이스 생성
createdb policy_db

# pgvector 확장 설치
psql policy_db -c "CREATE EXTENSION vector;"
```

### 3. 환경 변수 설정

```bash
export OPENAI_API_KEY="your-api-key-here"
```

---

## 🏗️ 시스템 아키텍처

```
┌─────────────────────────────────────────────────┐
│                  사용자 입력                      │
│         (사업지, 세대수, 주력평형)                 │
└────────────────────┬────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────┐
│              SmartPDFLoader                      │
│   ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│   │pdfplumber│ │ PyPDF2   │ │   OCR    │      │
│   └──────────┘ └──────────┘ └──────────┘      │
└────────────────────┬────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────┐
│            PolicyRetriever                       │
│   ┌──────────────┐     ┌──────────────┐       │
│   │Semantic Search│     │Keyword Search│       │
│   └──────────────┘     └──────────────┘       │
│            ▼                    ▼               │
│         ┌────────────────────────┐              │
│         │  Hybrid Search Engine  │              │
│         └────────────────────────┘              │
└────────────────────┬────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────┐
│          PolicyAnalysisAgent                     │
│                                                  │
│   ┌─────────┐  ┌─────────┐  ┌──────────┐      │
│   │Retrieve │→ │ Analyze │→ │ Validate │      │
│   └─────────┘  └─────────┘  └──────────┘      │
│        ↑             ↓              ↓           │
│        └─────────────┴──────────────┘           │
│                     ▼                           │
│              ┌──────────┐                       │
│              │  Format  │                       │
│              └──────────┘                       │
└────────────────────┬────────────────────────────┘
                     ▼
            ┌────────────────┐
            │  최종 보고서    │
            └────────────────┘
```

---

## 🌟 핵심 기능

### 1. SmartPDFLoader - 지능형 PDF 처리

```python
# 처리 우선순위
1. pdfplumber → 표 데이터 추출 가능
2. PyPDF2 → 일반 텍스트 추출
3. OCR → 스캔 이미지 처리
```

**특징:**
- 자동 정책 날짜 추출
- 정책 유형 자동 분류
- 표 데이터를 구조화된 텍스트로 변환

### 2. PolicyRetriever - 하이브리드 검색

```python
# 검색 방식
- Semantic Search: 의미 유사도 기반 (70%)
- Keyword Search: 핵심 키워드 매칭 (30%)
```

**재검색 로직:**
```python
if 검색_결과_부적절:
    retry_count += 1
    if retry_count < max_retries:
        쿼리_확장()
        재검색()
```

### 3. PolicyAnalysisAgent - 자동 분석 및 보고서 생성

**LangGraph 워크플로우:**
```
Retrieve → Analyze → Validate → Format
    ↑__________|_________↓
        (재검색 필요시)
```

---

## 📖 사용 방법

### 방법 1: 대화형 모드 (Interactive)

```bash
python run_analysis.py --mode interactive
```

프로그램이 안내에 따라 필요한 정보를 입력합니다:
- PDF 파일 선택
- 사업지 정보 입력
- 세대수 및 평형 입력

### 방법 2: 빠른 실행 모드 (Quick)

```bash
python run_analysis.py --mode quick \
  --pdf /path/to/pdf1.pdf /path/to/pdf2.pdf \
  --area "강남구" \
  --type "84㎡" \
  --units 500 \
  --output /path/to/report.md
```

### 방법 3: 배치 모드 (Batch)

```bash
# 설정 파일 준비
cp batch_config.yaml my_config.yaml
# 설정 편집 후 실행
python run_analysis.py --mode batch --config my_config.yaml
```

### Python 코드로 직접 사용

```python
from real_estate_policy_agent import (
    SmartPDFLoader,
    PolicyRetriever,
    PolicyAnalysisAgent
)
from langchain.chat_models import ChatOpenAI

# 1. PDF 로드
loader = SmartPDFLoader()
doc1 = loader.load_pdf("정책1.pdf")
doc2 = loader.load_pdf("정책2.pdf")

# 2. Retriever 초기화
retriever = PolicyRetriever("postgresql://user:pass@localhost/db")
retriever.initialize_vectorstore([doc1, doc2])

# 3. Agent 생성
llm = ChatOpenAI(temperature=0, model_name="gpt-4")
agent = PolicyAnalysisAgent(retriever, llm)
agent.load_yaml_prompt("policy_prompt.yaml")

# 4. 보고서 생성
report = agent.generate_comparison_report(
    policy_files=["정책1.pdf", "정책2.pdf"],
    target_area="강남구",
    main_type="84㎡",
    total_units=500
)

print(report)
```

---

## 📄 PDF 추가 가이드

### 새로운 정책 PDF 추가 방법

1. **PDF 파일 준비**
   ```bash
   # uploads 폴더에 복사
   cp new_policy.pdf /home/claude/uploads/
   ```

2. **파일명 규칙 (권장)**
   ```
   YYMMDD_정책명.pdf
   예: 251120_금리인상정책.pdf
   ```

3. **코드에서 추가**
   ```python
   # 기존 PDF 목록에 추가
   pdf_files.append("/home/claude/uploads/new_policy.pdf")
   ```

### 다른 형식 파일 추가

#### Markdown 파일
```python
def load_markdown(file_path: str) -> PolicyDocument:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    return PolicyDocument(
        file_path=file_path,
        policy_date=extract_date(content),
        policy_type=determine_type(content),
        title=extract_title(content),
        content=content,
        metadata={}
    )
```

#### JSON 파일
```python
def load_json(file_path: str) -> PolicyDocument:
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # JSON 구조를 텍스트로 변환
    content = json.dumps(data, ensure_ascii=False, indent=2)
    
    return PolicyDocument(
        file_path=file_path,
        policy_date=data.get('date', '날짜 미상'),
        policy_type=PolicyType.HOUSING_MARKET,
        title=data.get('title', '제목 없음'),
        content=content,
        metadata=data
    )
```

### 파일 중복 방지

```python
# 파일 해시로 중복 체크
import hashlib

def get_file_hash(file_path: str) -> str:
    with open(file_path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

loaded_hashes = set()

def load_if_new(file_path: str) -> PolicyDocument:
    file_hash = get_file_hash(file_path)
    
    if file_hash in loaded_hashes:
        print(f"⚠️ 이미 로드된 파일: {file_path}")
        return None
    
    loaded_hashes.add(file_hash)
    return loader.load_pdf(file_path)
```

---

## 🔧 트러블슈팅

### 문제 1: PDF 텍스트 추출 실패

**증상:** PDF 내용이 제대로 추출되지 않음

**해결책:**
```bash
# Tesseract OCR 설치
sudo apt-get install tesseract-ocr tesseract-ocr-kor

# Poppler 설치 (pdf2image용)
sudo apt-get install poppler-utils
```

### 문제 2: 메모리 부족

**증상:** 대용량 PDF 처리시 메모리 오류

**해결책:**
```python
# 청크 크기 조정
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,  # 기존 2000에서 축소
    chunk_overlap=100  # 기존 200에서 축소
)
```

### 문제 3: OpenAI API 한도 초과

**증상:** Rate limit 오류

**해결책:**
```python
import time
from tenacity import retry, wait_exponential

@retry(wait=wait_exponential(min=1, max=10))
def call_llm_with_retry(prompt):
    return llm.predict(prompt)
```

### 문제 4: 검색 결과 부정확

**증상:** 관련없는 내용이 검색됨

**해결책:**
```python
# 하이브리드 검색 가중치 조정
results = retriever.hybrid_search(
    query=query,
    semantic_weight=0.8,  # 의미 검색 비중 증가
    k=10  # 검색 결과 수 증가
)
```

### 문제 5: PostgreSQL 연결 실패

**증상:** 벡터 DB 연결 오류

**해결책:**
```python
# SQLite로 대체 (개발/테스트용)
connection_string = "sqlite:///policy_vectors.db"

# 또는 환경 변수로 관리
import os
connection_string = os.environ.get(
    'DB_CONNECTION',
    'sqlite:///policy_vectors.db'
)
```

---

## 📊 성능 최적화 팁

1. **PDF 전처리**
   - 큰 PDF는 미리 분할
   - 불필요한 이미지 제거

2. **캐싱 활용**
   ```python
   from functools import lru_cache
   
   @lru_cache(maxsize=100)
   def cached_search(query: str) -> List[Document]:
       return retriever.semantic_search(query)
   ```

3. **병렬 처리**
   ```python
   from concurrent.futures import ThreadPoolExecutor
   
   with ThreadPoolExecutor(max_workers=4) as executor:
       results = executor.map(loader.load_pdf, pdf_files)
   ```

4. **임베딩 사전 생성**
   ```python
   # 임베딩을 미리 생성하여 저장
   embeddings = model.encode(documents)
   np.save('embeddings.npy', embeddings)
   ```

---

## 📚 참고 자료

- [LangChain Documentation](https://python.langchain.com/)
- [LangGraph Guide](https://github.com/langchain-ai/langgraph)
- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [pdfplumber Documentation](https://github.com/jsvine/pdfplumber)

---

## 💡 추가 개선 아이디어

1. **웹 인터페이스 추가** - Streamlit/Gradio로 GUI 제공
2. **실시간 모니터링** - 분석 진행상황 시각화
3. **다국어 지원** - 영문 정책 문서 분석
4. **자동 업데이트** - 새 정책 발표시 자동 수집/분석
5. **비교 시각화** - 차트/그래프로 정책 변화 표현

---

## 📞 지원

문제가 발생하거나 추가 기능이 필요한 경우:
- 이슈 등록: GitHub Issues
- 이메일: support@example.com

---

*Last Updated: 2025.01*
