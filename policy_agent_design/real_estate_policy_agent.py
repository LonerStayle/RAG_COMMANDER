"""
부동산 정책 비교 분석 Agent System
PDF 문서를 읽고 YAML 프롬프트 형식에 따라 정책 비교 보고서를 자동 생성
"""

import os
import json
import yaml
import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

# PDF 처리
import pypdf2
import pdfplumber
from pdf2image import convert_from_path
import pytesseract

# 임베딩 및 벡터 DB
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import PGVector
from langchain.text_splitter import RecursiveCharacterTextSplitter

# LangGraph Agent
from langchain.agents import Tool, AgentExecutor
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate
from langchain.schema import Document
from langgraph.prebuilt import ToolExecutor, ToolInvocation
from langgraph.graph import StateGraph, END

# LLM
from langchain.chat_models import ChatOpenAI
from langchain.callbacks import get_openai_callback

class PolicyType(Enum):
    """정책 문서 타입"""
    LOAN_REGULATION = "대출규제"
    HOUSING_MARKET = "주택시장"
    TAX_POLICY = "세제정책"
    SUPPLY_POLICY = "공급정책"

@dataclass
class PolicyDocument:
    """정책 문서 메타데이터"""
    file_path: str
    policy_date: str
    policy_type: PolicyType
    title: str
    content: str
    metadata: Dict[str, Any]

class SmartPDFLoader:
    """
    다양한 PDF 형식을 지능적으로 처리하는 로더
    - 텍스트 기반 PDF: PyPDF2 사용
    - 스캔 이미지 PDF: OCR 사용
    - 표 데이터 포함: pdfplumber 사용
    """
    
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""],
            length_function=len
        )
    
    def load_pdf(self, file_path: str) -> PolicyDocument:
        """PDF 파일을 지능적으로 로드"""
        content = ""
        metadata = {}
        
        # 1. pdfplumber로 시도 (표 데이터 추출 가능)
        try:
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    # 텍스트 추출
                    text = page.extract_text()
                    if text:
                        content += f"\n[페이지 {page_num + 1}]\n{text}\n"
                    
                    # 표 데이터 추출
                    tables = page.extract_tables()
                    for table_idx, table in enumerate(tables):
                        metadata[f"table_p{page_num + 1}_t{table_idx + 1}"] = table
                        # 표를 텍스트로 변환
                        table_text = self._table_to_text(table)
                        content += f"\n[표 {table_idx + 1}]\n{table_text}\n"
        except Exception as e:
            print(f"pdfplumber 처리 실패: {e}")
            
            # 2. PyPDF2로 재시도
            try:
                with open(file_path, 'rb') as file:
                    pdf_reader = pypdf2.PdfReader(file)
                    for page_num in range(len(pdf_reader.pages)):
                        page = pdf_reader.pages[page_num]
                        text = page.extract_text()
                        content += f"\n[페이지 {page_num + 1}]\n{text}\n"
            except Exception as e2:
                print(f"PyPDF2 처리 실패: {e2}")
                
                # 3. OCR로 최종 시도
                content = self._extract_with_ocr(file_path)
        
        # 정책 날짜와 타입 자동 추출
        policy_date = self._extract_policy_date(content, file_path)
        policy_type = self._determine_policy_type(content, file_path)
        title = self._extract_title(content, file_path)
        
        return PolicyDocument(
            file_path=file_path,
            policy_date=policy_date,
            policy_type=policy_type,
            title=title,
            content=content,
            metadata=metadata
        )
    
    def _table_to_text(self, table: List[List]) -> str:
        """표를 구조화된 텍스트로 변환"""
        if not table:
            return ""
        
        text_lines = []
        for row in table:
            cleaned_row = [str(cell).strip() if cell else "" for cell in row]
            text_lines.append(" | ".join(cleaned_row))
        
        return "\n".join(text_lines)
    
    def _extract_with_ocr(self, file_path: str) -> str:
        """OCR을 사용한 텍스트 추출"""
        try:
            images = convert_from_path(file_path)
            content = ""
            
            for i, image in enumerate(images):
                text = pytesseract.image_to_string(image, lang='kor+eng')
                content += f"\n[페이지 {i + 1}]\n{text}\n"
            
            return content
        except Exception as e:
            print(f"OCR 처리 실패: {e}")
            return ""
    
    def _extract_policy_date(self, content: str, file_path: str) -> str:
        """정책 날짜 추출"""
        import re
        
        # 파일명에서 날짜 추출
        file_date_match = re.search(r'(\d{6}|\d{4}\.\d{1,2}\.\d{1,2})', file_path)
        if file_date_match:
            return file_date_match.group(1)
        
        # 내용에서 날짜 추출
        date_patterns = [
            r'(\d{4}년\s*\d{1,2}월\s*\d{1,2}일)',
            r'(\d{4}\.\s*\d{1,2}\.\s*\d{1,2})',
            r'(\d{2}\.\s*\d{1,2}\.\s*\d{1,2})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, content[:1000])  # 문서 앞부분에서 검색
            if match:
                return match.group(1)
        
        return "날짜 미상"
    
    def _determine_policy_type(self, content: str, file_path: str) -> PolicyType:
        """정책 유형 자동 판별"""
        content_lower = content.lower()
        file_lower = file_path.lower()
        
        # 키워드 기반 분류
        if any(word in content_lower or word in file_lower 
               for word in ['대출', 'ltv', 'dsr', 'dti', '대출수요']):
            return PolicyType.LOAN_REGULATION
        elif any(word in content_lower or word in file_lower 
                for word in ['주택시장', '부동산시장', '주택가격']):
            return PolicyType.HOUSING_MARKET
        elif any(word in content_lower or word in file_lower 
                for word in ['세제', '취득세', '재산세', '양도세']):
            return PolicyType.TAX_POLICY
        elif any(word in content_lower or word in file_lower 
                for word in ['공급', '분양', '입주']):
            return PolicyType.SUPPLY_POLICY
        
        return PolicyType.HOUSING_MARKET  # 기본값
    
    def _extract_title(self, content: str, file_path: str) -> str:
        """문서 제목 추출"""
        import re
        
        # 파일명에서 제목 추출
        file_name = os.path.basename(file_path)
        title = re.sub(r'\d+_?', '', file_name)  # 숫자 제거
        title = title.replace('.pdf', '').replace('_', ' ')
        
        # 문서 첫 줄에서 제목 찾기
        lines = content.split('\n')
        for line in lines[:10]:  # 첫 10줄에서 검색
            if len(line) > 10 and len(line) < 100:  # 적절한 길이의 라인
                if not line.startswith('['):  # 페이지 표시가 아닌 경우
                    return line.strip()
        
        return title.strip()

class PolicyRetriever:
    """
    정책 문서 검색 시스템
    - 의미 기반 검색 (Semantic Search)
    - 키워드 기반 검색 (Keyword Search)
    - 하이브리드 검색
    """
    
    def __init__(self, connection_string: str):
        self.embeddings = OpenAIEmbeddings()
        self.connection_string = connection_string
        self.vector_store = None
        self.documents = []
        
    def initialize_vectorstore(self, documents: List[PolicyDocument]):
        """벡터 스토어 초기화"""
        # Document 객체로 변환
        docs = []
        for doc in documents:
            # 청크 분할
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=1500,
                chunk_overlap=150
            )
            chunks = splitter.split_text(doc.content)
            
            for i, chunk in enumerate(chunks):
                docs.append(Document(
                    page_content=chunk,
                    metadata={
                        "source": doc.file_path,
                        "policy_date": doc.policy_date,
                        "policy_type": doc.policy_type.value,
                        "title": doc.title,
                        "chunk_id": i,
                        "total_chunks": len(chunks)
                    }
                ))
        
        self.documents = docs
        
        # PGVector 초기화
        self.vector_store = PGVector.from_documents(
            documents=docs,
            embedding=self.embeddings,
            connection_string=self.connection_string,
            collection_name="policy_documents"
        )
    
    def semantic_search(self, query: str, k: int = 5) -> List[Document]:
        """의미 기반 검색"""
        if not self.vector_store:
            return []
        
        return self.vector_store.similarity_search(query, k=k)
    
    def keyword_search(self, keywords: List[str], k: int = 5) -> List[Document]:
        """키워드 기반 검색"""
        results = []
        for doc in self.documents:
            score = 0
            content_lower = doc.page_content.lower()
            
            for keyword in keywords:
                if keyword.lower() in content_lower:
                    score += content_lower.count(keyword.lower())
            
            if score > 0:
                results.append((doc, score))
        
        # 점수순 정렬
        results.sort(key=lambda x: x[1], reverse=True)
        return [doc for doc, _ in results[:k]]
    
    def hybrid_search(self, query: str, keywords: List[str] = None, 
                      semantic_weight: float = 0.7, k: int = 5) -> List[Document]:
        """하이브리드 검색 (의미 + 키워드)"""
        # 의미 검색 결과
        semantic_results = self.semantic_search(query, k=k*2)
        
        # 키워드 검색 결과
        if not keywords:
            keywords = self._extract_keywords(query)
        keyword_results = self.keyword_search(keywords, k=k*2)
        
        # 결과 병합 및 점수 계산
        combined = {}
        
        for i, doc in enumerate(semantic_results):
            doc_id = f"{doc.metadata['source']}_{doc.metadata['chunk_id']}"
            combined[doc_id] = {
                'doc': doc,
                'score': semantic_weight * (1 - i / len(semantic_results))
            }
        
        for i, doc in enumerate(keyword_results):
            doc_id = f"{doc.metadata['source']}_{doc.metadata['chunk_id']}"
            if doc_id in combined:
                combined[doc_id]['score'] += (1 - semantic_weight) * (1 - i / len(keyword_results))
            else:
                combined[doc_id] = {
                    'doc': doc,
                    'score': (1 - semantic_weight) * (1 - i / len(keyword_results))
                }
        
        # 점수순 정렬
        sorted_results = sorted(combined.values(), key=lambda x: x['score'], reverse=True)
        return [item['doc'] for item in sorted_results[:k]]
    
    def _extract_keywords(self, query: str) -> List[str]:
        """쿼리에서 키워드 추출"""
        import re
        
        # 중요 키워드 패턴
        important_terms = [
            'LTV', 'DTI', 'DSR', '규제지역', '투기과열지구', '조정대상지역',
            '대출', '주담대', '전세대출', '신용대출', '중도금대출',
            '주택', '아파트', '분양', '청약', '전매제한',
            '취득세', '양도세', '재산세', '종부세',
            '수도권', '지방', '서울', '경기',
            '금리', '한도', '만기', '상환'
        ]
        
        keywords = []
        query_upper = query.upper()
        
        for term in important_terms:
            if term.upper() in query_upper:
                keywords.append(term)
        
        # 숫자 패턴 추출 (날짜, 비율 등)
        numbers = re.findall(r'\d+(?:\.\d+)?[%년월일억원]?', query)
        keywords.extend(numbers)
        
        return keywords

class PolicyAnalysisAgent:
    """
    부동산 정책 분석 Agent
    YAML 프롬프트에 따라 보고서 생성
    """
    
    def __init__(self, retriever: PolicyRetriever, llm: ChatOpenAI):
        self.retriever = retriever
        self.llm = llm
        self.memory = ConversationBufferMemory(memory_key="chat_history")
        self.yaml_prompt = None
        self.max_retries = 3
        
    def load_yaml_prompt(self, yaml_path: str):
        """YAML 프롬프트 로드"""
        with open(yaml_path, 'r', encoding='utf-8') as f:
            self.yaml_prompt = yaml.safe_load(f)
    
    def create_analysis_graph(self):
        """LangGraph 분석 워크플로우 생성"""
        
        # State 정의
        class AgentState(Dict):
            messages: List[str]
            current_section: str
            retrieved_docs: List[Document]
            analysis_results: Dict[str, Any]
            retry_count: int
        
        # 그래프 생성
        workflow = StateGraph(AgentState)
        
        # 노드 정의
        workflow.add_node("retrieve", self.retrieve_information)
        workflow.add_node("analyze", self.analyze_section)
        workflow.add_node("validate", self.validate_analysis)
        workflow.add_node("format", self.format_report)
        
        # 엣지 정의
        workflow.set_entry_point("retrieve")
        workflow.add_edge("retrieve", "analyze")
        workflow.add_conditional_edges(
            "analyze",
            self.should_continue_analysis,
            {
                "validate": "validate",
                "retrieve": "retrieve",
                "end": END
            }
        )
        workflow.add_conditional_edges(
            "validate",
            self.is_valid_analysis,
            {
                "format": "format",
                "retrieve": "retrieve"
            }
        )
        workflow.add_edge("format", END)
        
        return workflow.compile()
    
    def retrieve_information(self, state: Dict) -> Dict:
        """정보 검색 노드"""
        current_section = state.get('current_section', '')
        retry_count = state.get('retry_count', 0)
        
        # 섹션별 최적화된 쿼리 생성
        query = self._generate_retrieval_query(current_section, retry_count)
        
        # 하이브리드 검색 수행
        docs = self.retriever.hybrid_search(query, k=10)
        
        state['retrieved_docs'] = docs
        state['retry_count'] = retry_count + 1
        
        return state
    
    def analyze_section(self, state: Dict) -> Dict:
        """섹션 분석 노드"""
        current_section = state.get('current_section', '')
        retrieved_docs = state.get('retrieved_docs', [])
        
        if not retrieved_docs:
            state['analysis_results'][current_section] = "정보 없음"
            return state
        
        # 섹션별 분석 프롬프트 생성
        analysis_prompt = self._create_analysis_prompt(current_section, retrieved_docs)
        
        # LLM 분석
        with get_openai_callback() as cb:
            response = self.llm.predict(analysis_prompt)
            
        if 'analysis_results' not in state:
            state['analysis_results'] = {}
        
        state['analysis_results'][current_section] = response
        
        return state
    
    def validate_analysis(self, state: Dict) -> Dict:
        """분석 결과 검증 노드"""
        current_section = state.get('current_section', '')
        analysis_result = state.get('analysis_results', {}).get(current_section, '')
        
        # 검증 기준
        validation_criteria = {
            '규제지역': ['투기과열지구', '조정대상지역', '지정', '해제'],
            'LTV': ['비율', '%', '무주택', '1주택', '2주택'],
            'DSR': ['스트레스', '금리', '적용', '산정'],
            '대출한도': ['억원', '제한', '한도', '축소'],
            '시행시기': ['시행', '적용', '경과규정', '날짜']
        }
        
        # 섹션에 맞는 키워드 확인
        is_valid = True
        for section_key, keywords in validation_criteria.items():
            if section_key in current_section:
                if not any(kw in analysis_result for kw in keywords):
                    is_valid = False
                    break
        
        state['is_valid'] = is_valid
        return state
    
    def should_continue_analysis(self, state: Dict) -> str:
        """분석 계속 여부 결정"""
        retry_count = state.get('retry_count', 0)
        
        if retry_count >= self.max_retries:
            return "end"
        
        if state.get('retrieved_docs'):
            return "validate"
        
        return "retrieve"
    
    def is_valid_analysis(self, state: Dict) -> str:
        """분석 유효성 확인"""
        if state.get('is_valid', False):
            return "format"
        
        if state.get('retry_count', 0) < self.max_retries:
            return "retrieve"
        
        return "format"
    
    def format_report(self, state: Dict) -> Dict:
        """최종 보고서 포맷팅"""
        analysis_results = state.get('analysis_results', {})
        
        # YAML 프롬프트 형식에 맞춰 보고서 생성
        report = self._format_according_to_yaml(analysis_results)
        
        state['final_report'] = report
        return state
    
    def _generate_retrieval_query(self, section: str, retry_count: int) -> str:
        """섹션별 검색 쿼리 생성"""
        base_queries = {
            '정책배경': '정책 추진배경 목적 가계대출 주택시장 동향',
            '규제지역': '투기과열지구 조정대상지역 토지거래허가구역 지정 해제',
            'LTV': 'LTV 주택담보대출 담보인정비율 무주택 1주택 2주택 처분조건부',
            'DSR': 'DSR DTI 총부채원리금상환비율 스트레스금리 차주단위',
            '대출한도': '주담대 한도 6억원 4억원 2억원 생활안정자금',
            '전세대출': '전세대출 보증비율 소유권이전조건부 전세자금',
            '정책대출': '디딤돌 버팀목 보금자리론 주택기금',
            '시행시기': '시행일 적용시기 경과규정 예외사항'
        }
        
        # 재시도시 쿼리 확장
        if retry_count > 0:
            query = base_queries.get(section, section)
            query += f" 상세 내용 추가 정보 {section} 관련"
        else:
            query = base_queries.get(section, section)
        
        return query
    
    def _create_analysis_prompt(self, section: str, docs: List[Document]) -> str:
        """분석 프롬프트 생성"""
        # 문서 내용 결합
        context = "\n\n".join([doc.page_content for doc in docs[:5]])
        
        prompt = f"""
        다음은 {section}에 대한 정책 문서 내용입니다:
        
        {context}
        
        위 내용을 바탕으로 다음 항목들을 분석하여 정리해주세요:
        
        1. 주요 변경사항
        2. 이전 정책과의 차이점
        3. 적용 대상 및 범위
        4. 구체적인 수치나 비율
        5. 시행시기 및 경과규정
        
        표 형식으로 정리가 필요한 경우 마크다운 표를 사용해주세요.
        불확실한 내용은 명시하지 마시고, 문서에 있는 내용만 정확히 기술해주세요.
        """
        
        return prompt
    
    def _format_according_to_yaml(self, analysis_results: Dict) -> str:
        """YAML 형식에 맞춰 보고서 생성"""
        if not self.yaml_prompt:
            return str(analysis_results)
        
        report = []
        
        # YAML 구조에 따라 보고서 구성
        for segment in ['POLICY_SUMMARY', 'POLICY_SEGMENT_01', 'POLICY_SEGMENT_02', 'POLICY_SEGMENT_03']:
            if segment in self.yaml_prompt:
                segment_content = self.yaml_prompt[segment].get('prompt', '')
                
                # 템플릿 채우기
                for section, result in analysis_results.items():
                    if section in segment_content:
                        segment_content = segment_content.replace(f'{{{section}}}', result)
                
                report.append(segment_content)
        
        return "\n\n".join(report)
    
    def generate_comparison_report(self, 
                                 policy_files: List[str],
                                 target_area: str,
                                 main_type: str,
                                 total_units: int) -> str:
        """정책 비교 보고서 생성"""
        
        # 그래프 생성
        analysis_graph = self.create_analysis_graph()
        
        # 섹션별 분석 수행
        sections = [
            '정책배경', '규제지역', 'LTV', 'DSR', 
            '대출한도', '전세대출', '정책대출', '시행시기'
        ]
        
        all_results = {}
        
        for section in sections:
            state = {
                'current_section': section,
                'retry_count': 0,
                'retrieved_docs': [],
                'analysis_results': {}
            }
            
            # 그래프 실행
            final_state = analysis_graph.invoke(state)
            all_results[section] = final_state.get('analysis_results', {}).get(section, '')
        
        # 최종 보고서 생성
        final_report = self._format_according_to_yaml(all_results)
        
        # 사업지 특화 분석 추가
        project_analysis = self._analyze_for_project(
            all_results, target_area, main_type, total_units
        )
        
        final_report += f"\n\n## {target_area} 사업지 영향 분석\n{project_analysis}"
        
        return final_report
    
    def _analyze_for_project(self, 
                            analysis_results: Dict,
                            target_area: str,
                            main_type: str,
                            total_units: int) -> str:
        """특정 사업지에 대한 영향 분석"""
        
        prompt = f"""
        다음 정책 분석 결과를 바탕으로 {target_area} 지역의 
        {main_type} {total_units}세대 사업에 미치는 영향을 분석해주세요:
        
        {json.dumps(analysis_results, ensure_ascii=False, indent=2)}
        
        다음 항목을 포함해주세요:
        1. 해당 지역 규제 수준
        2. 대출 가능성 변화
        3. 수요자 구매력 영향
        4. 분양 전략 제언
        5. 리스크 요인
        """
        
        with get_openai_callback() as cb:
            response = self.llm.predict(prompt)
        
        return response


def main():
    """메인 실행 함수"""
    
    # 환경 변수 설정
    os.environ["OPENAI_API_KEY"] = "your-api-key"
    
    # PostgreSQL 연결 설정
    connection_string = "postgresql://user:password@localhost:5432/policy_db"
    
    # PDF 로더 초기화
    pdf_loader = SmartPDFLoader()
    
    # PDF 파일 로드
    policy_docs = []
    pdf_files = [
        "/mnt/user-data/uploads/251015_대출수요_관리_강화_방안_주요_FAQ.pdf",
        "/mnt/user-data/uploads/251015_주택시장_안정화_대책.pdf",
        "/mnt/user-data/uploads/0627.pdf"
    ]
    
    for pdf_file in pdf_files:
        if os.path.exists(pdf_file):
            doc = pdf_loader.load_pdf(pdf_file)
            policy_docs.append(doc)
            print(f"✅ 로드 완료: {doc.title} ({doc.policy_date})")
    
    # Retriever 초기화
    retriever = PolicyRetriever(connection_string)
    retriever.initialize_vectorstore(policy_docs)
    
    # LLM 초기화
    llm = ChatOpenAI(temperature=0, model_name="gpt-4")
    
    # Agent 초기화
    agent = PolicyAnalysisAgent(retriever, llm)
    
    # YAML 프롬프트 로드 (CONTEXT1의 내용을 YAML 파일로 저장했다고 가정)
    agent.load_yaml_prompt("/home/claude/policy_prompt.yaml")
    
    # 보고서 생성
    report = agent.generate_comparison_report(
        policy_files=pdf_files,
        target_area="강남구",
        main_type="84㎡",
        total_units=500
    )
    
    # 보고서 저장
    with open("/home/claude/policy_comparison_report.md", "w", encoding="utf-8") as f:
        f.write(report)
    
    print("✅ 정책 비교 보고서 생성 완료!")
    print(f"📄 보고서 위치: /home/claude/policy_comparison_report.md")

if __name__ == "__main__":
    main()
