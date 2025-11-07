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

# 컬렉션 이름 상수
POLICY_DOCUMENTS_COLLECTION = "policy_documents"

class PolicyPDFRetriever:
    """
    정책 문서 검색 시스템
    의미기반 검색과 키워드기반 검색을 하이브리드로 결합한 검색 시스템입니다.
    """
    def __init__(self):
        """
        PolicyPDFRetriever 초기화
        PGVector 스토어를 가져옵니다.
        """
        self.vector_store = get_pgvector_store(POLICY_DOCUMENTS_COLLECTION)
        self.documents_cache = []

    def add_documents(self, policy_documents: List[PolicyDocument]) -> None:
        """
        정책 문서를 벡터스코어에 추가 합니다.

        Args:
            policy_documents: 추가할 PolicyDocument 리스트
        """
        langchain_docs = []

        # 텍스트 분할기 초기화
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,
            chunk_overlap=150
        )

        # 각 정책 문서를 청크로 분할 
        for policy_doc in policy_documents:
            # content가 문자열인지 확인
            if not isinstance(policy_doc.content, str):
                raise TypeError(f"policy_doc.content는 문자열이어야 합니다. 현재 타입: {type(policy_doc.content)}")
            
            chunks = text_splitter.split_text(policy_doc.content)
            for chunk_idx, chunk in enumerate(chunks):
                langchain_doc = Document(
                    page_content=chunk,
                    metadata={
                        "source": policy_doc.file_path,
                        "policy_date": policy_doc.policy_date,
                        "policy_type": policy_doc.policy_type.value,
                        "title": policy_doc.title,
                        "chunk_id": chunk_idx,
                        "total_chunks": len(chunks)
                    }
                )
                langchain_docs.append(langchain_doc)
        
        # 벡터스코어에 문서추가
        self.vector_store.add_documents(langchain_docs)

        # 캐시에도 저장(키워드 검색용)
        self.documents_cache.extend(policy_documents)

    def semantic_search(self, query: str, k: int = 5) -> List[Document]:
        """
        의미기반 검색을 수행합니다.
        벡터 유사도를 기반으로 관련 문서를 찾습니다.

        Args:
            query: 검색 쿼리
            k: 반환할 문서 개수

        Returns:
            검색된 Document 리스트
        """
        if not self.vector_store:
            return []

        results = self.vector_store.similarity_search(query, k=k)
        return results

    def keyword_search(self, keywords: List[str], k: int=5) -> List[Document]:
        """
        키워드 기반 검색을 수행합니다.
        문서 내용에서 키워드가 나타나는 빈도를 기반으로 점수를 계산합니다.

        Args:
            keywords: 검색할 키워드 리스트
            k: 반환할 문서 개수

        Returns:
            검색된 Document 리스트(점수순 정렬)
        """
        scored_docs = []

        for doc in self.documents_cache:
            score = 0
            content_lower = doc.content.lower()

            for keyword in keywords:
                keyword_lower = keyword.lower()
                if keyword_lower in content_lower:
                    score += content_lower.count(keyword_lower)

            if score > 0:
                scored_docs.append((doc, score))

        # 점수순 정렬
        scored_docs.sort(key=lambda x: x[1], reverse=True)

        # 상위 k개 반환
        result_docs = []
        for doc, score in scored_docs[:k]:
            result_docs.append(doc)

        return result_docs

    def hybrid_search(
        self,
        query: str,
        keywords: Optional[List[str]] = None,
        semantic_weight: float = 0.7,
        k: int = 5
    ) -> List[Document]:
        """
        하이브리드 검색을 수행합니다.
        의미 검색과 키워드 검색의 결과를 결합하여 최종 결과를 반환합니다.
 
        Args:
            query: 검색 쿼리
            keywords: 검색할 키워드 리스트 (None이면 자동 추출)
            semantic_weight: 의미검색의 가중치 (0.0~1.0)
            k: 반환할 문서 개수

        Returns:
            검색된 Document 리스트(점수순 정렬)
        """
           
        # 의미검색수행
        semantic_results = self.semantic_search(query, k=k*2)
        
        # 키워드 추출(제공되지 않은 경우)
        if keywords is None:
            keywords = self._extract_keywords(query)

        # 키워드 검색 수행
        keyword_results = self.keyword_search(keywords, k=k*2)

        # 결과 병합 및 점수 계산
        combined_scores = {}

        # 의미 검색 결과에 점수 부여
        semantic_count = len(semantic_results)
        for idx, doc in enumerate(semantic_results):
            doc_id = self._get_doc_id(doc)
            # 순위가 높을수록 높은 점수 (1.0 → 0.0)
            rank_score = (semantic_count - idx) / semantic_count if semantic_count > 0 else 0
            score = semantic_weight * rank_score
            combined_scores[doc_id] = {
                'doc': doc,
                'score': score
            }

        # 키워드 검색 결과에 점수 부여(이미 있으면 점수 추가)
        keyword_count = len(keyword_results)
        keyword_weight = 1.0 - semantic_weight

        for idx, doc in enumerate(keyword_results):
            doc_id = self._get_doc_id(doc)
            keyword_score = keyword_weight * (1 - idx / keyword_count) if keyword_count > 0 else 0

            if doc_id in combined_scores:
                combined_scores[doc_id]['score'] += keyword_score
            else:
                combined_scores[doc_id] = {
                    'doc': doc,
                    'score': keyword_score
                }

        # 점수순 정렬
        sorted_results = sorted(
            combined_scores.values(),
            key=lambda x: x['score'],
            reverse=True
            )

        # 상위 k개 반환
        result_docs = []
        for item in sorted_results[:k]:
            result_docs.append(item['doc'])

        return result_docs

    def _get_doc_id(self, doc: Document) -> str:
        """
        Document 고유 ID를 생성합니다.

        Args:
            doc: Document 객체

        Returns:
            고유 ID 문자열
        """
        source = doc.metadata.get('source', '')
        chunk_id = doc.metadata.get('chunk_id', 0)
        return f"{source}_{chunk_id}"

    def _extract_keywords(self, query: str) -> List[str]:
        """
        쿼리에서 중요한 키워드를 추출합니다.

        Args:
            query: 검색쿼리

        Returns:
            추출된 키워드 리스트
        """
        keywords = []
        # 중요 키워드 목록
        important_terms = [
            'LTV', 'DTI', 'DSR', '규제지역', '투기과열지구', '조정대상지역',
            '대출', '주담대', '전세대출', '신용대출', '중도금대출',
            '주택', '아파트', '분양', '청약', '전매제한',
            '취득세', '양도세', '재산세', '종부세',
            '수도권', '지방', '서울', '경기',
            '금리', '한도', '만기', '상환'
        ]

        query_upper = query.upper()

        # 중요 키워드 확인
        for term in important_terms:
            if term.upper() in query_upper:
                keywords.append(term)

        # 숫자 패턴 추출(날짜, 비율 등)
        numbers_pattern = r'\d+(?:\.\d+)?[%년월일억원]?' # \d+ - 1개 이상의 숫자 (예: 70, 2024, 5)
        # (?:\.\d+)? - 소수점과 숫자가 선택적으로 올 수 있음 (예: .5, .75)
        # ? - 0번 또는 1번 나타남
        # [%년월일억원]? - 단위 문자가 선택적으로 올 수 있음 (예: %, 년, 월, 일, 억, 원)
        #   ? - 바로 앞의 문자 집합이 0번 또는 1번 나타남 (있어도 되고 없어도 됨)
        #(\.\d+)? - 소수점 부분을 그룹1에 저장
        # (?:\.\d+)? - 소수점 부분을 저장 안 함, 그냥 묶기만
        numbers = re.findall(numbers_pattern, query)
        keywords.extend(numbers)

        return keywords

    def as_retriever(self, search_kwargs: Optional[Dict] = None):
        """
        LangChain Retriever 인터페이스를 제공합니다.

        Args:
            search_kwargs: 검색 옵션 딕셔너리

        Returns:
            LangChain Retriever 객체
        """
        if search_kwargs is None:
            search_kwargs = {"k": 5}

        return self.vector_store.as_retriever(search_kwargs=search_kwargs)