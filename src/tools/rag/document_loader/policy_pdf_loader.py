"""
정책 PDF 파일 로더
PDF 파일을 로드하고 정책 메타데이터를 추출합니다.
현재 프로젝트의 best_loader 함수를 사용하여 PDF 파일을 로드합니다.
"""

import os
import re
from typing import List, Dict, Any
from dataclasses import dataclass
from enum import Enum
from langchain_core.documents import Document

from tools.rag.document_loader.default_loader import best_loader
from tools.rag.document_loader.file_hash_manager import file_hash_manager

class PolicyType(Enum):
    """
    정책문서의 유형을 정의합니다.
    """
    LOAN_REGULATION = "대출규제"
    HOUSING_MARKET = "주택시장"
    TAX_POLICY = "세제정책"
    SUPPLY_POLICY = "공급정책"
    UNKNOWN = "기타"

@dataclass
class PolicyDocument:
    """
    정책 문서의 메타데이터와 내용을 저장하는 데이터 클래스
    """
    file_path: str
    policy_date: str
    policy_type: PolicyType
    title: str
    content: str
    metadata: Dict[str, Any]

class PolicyPDFLoader:
    """
    정책 PDF 파일을 로드하고 메타데이터를 추출하는 클래스
    현재 프로젝트의 best_loader 를 활용하여 PDF 파일을 로드합니다.
    """
    def load_pdf(self, file_path: str) -> PolicyDocument:
        f"""
        PDF 파일을 로드하고 정책 메타데이터를 추출합니다.

        Args:
            file_path: 로드할 PDF 파일의 경로

        Returns:
            PolicyDocument 객체 (메타데이터와 내용 포함)
        """
        # 파일 존재 여부 체크
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")

        # 파일 중복 체크
        if file_hash_manager.is_file_loaded(file_path):
            print(f"이미 로드된 파일입니다: {file_path}")

        # best_loader 함수를 사용하여 PDF 파일을 로드합니다.
        langchain_documents = best_loader(file_path)

        # langchain_documents를 하나의 텍스트로 합치기
        content = self._combine_documents(langchain_documents)

        # 정책 메타데이터 추출
        policy_date = self._extract_policy_data(content, file_path)
        policy_type = self._determine_policy_type(content, file_path)
        title = self._extract_title(content, file_path)

        # 메타데이터 준비
        metadata = {
            "source": file_path,
            "policy_date": policy_date,
            "policy_type": policy_type.value,
            "title": title
        }

        # 파일을 로드된 것으로 표시
        file_hash_manager.mark_as_loaded(file_path)

        # PolicyDocument 객체생성
        policy_document = PolicyDocument(
            file_path=file_path,
            policy_date=policy_date,
            policy_type=policy_type,
            title=title,
            content=content,
            metadata=metadata
        )

        return policy_document

    def _combine_documents(self, documents: List[Document]) -> str:
        """
        여러 Langchain Document를 하나의 텍스트로 합치는 함수

        Args:
            documents: 합칠 Document 리스트

        Returns:
            합쳐진 텍스트 내용
        """
        content_parts = []

        for doc in documents:
            content_parts.append(doc.page_content)

        combined_content = "\n\n".join(content_parts)
        return combined_content

    def _extract_policy_data(self, content: str, file_path: str) -> str:
        """
        정책 문서의 날짜를 추출합니다.
        먼저 파일명에서 날짜를 찾고, 없으면 문서 내용에서 찾습니다.

        Args:
            content: 문서 내용
            file_path: 파일 경로

        Returns:
            추출된 날짜 문자열 (없으면 "날짜 미상")
        """
        # 파일명에서 날짜 추출 시도
        file_name = os.path.basename(file_path)
        file_data_match = re.search(r'(\d{6}|\d{4}\.\d{1,2}\.\d{1,2})', file_name)

        if file_data_match:
            return file_data_match.group(1) # 날짜 그룹 반환

        # 문서 내용 앞부분에서 날짜 패턴 찾기
        date_patterns = [
            r'(\d{4}년\s*\d{1,2}월\s*\d{1,2}일)',
            r'(\d{4}\.\s*\d{1,2}\.\s*\d{1,2})',
            r'(\d{2}\.\s*\d{1,2}\.\s*\d{1,2})'
        ]

        # 문서 앞부분만 검색(처음 1000자)
        content_start = content[:1000]

        for pattern in date_patterns:
            match = re.search(pattern, content_start)
            if match:
                return match.group(1) # 날짜 그룹 반환

        return "날짜 미상"

    def _determine_policy_type(self, content: str, file_path: str) -> PolicyType:
        """
        정책 문서의 유형을 자동으로 판별합니다.
        키워드 기반으로 분류합니다.

        Args:
            content: 문서 내용
            file_path: 파일 경로
        
        Returns:
            PolicyType 열거형 값
        """
        content_lower = content.lower()
        file_lower = file_path.lower()

        # 대출 규제 관련 키워드 확인
        loan_keywords = [ '대출', 'ltv', 'dsr', 'dti', '대출수요' ]
        has_loan_keywords = False
        for keyword in loan_keywords:
            if keyword in content_lower or keyword in file_lower:
                has_loan_keywords = True
                break
        
        if has_loan_keywords:
            return PolicyType.LOAN_REGULATION

        # 주택시장 관련 키워드 확인
        housing_keywords = ['주택시장', '부동산시장', '주택가격']
        has_housing_keywords = False
        for keyword in housing_keywords:
            if keyword in content_lower or keyword in file_lower:
                has_housing_keywords = True
                break
        if has_housing_keywords:
            return PolicyType.HOUSING_MARKET

        # 세제 관련 키워드 확인
        tax_keywords = ['세제', '취득세', '재산세', '양도세']
        has_tax_keywords = False
        for keyword in tax_keywords:
            if keyword in content_lower or keyword in file_lower:
                has_tax_keywords = True
                break
        
        if has_tax_keywords:
            return PolicyType.TAX_POLICY

        # 공급 관련 키워드 확인
        supply_keywords = ['공급', '분양', '입주']
        has_supply_keywords = False
        for keyword in supply_keywords:
            if keyword in content_lower or keyword in file_lower:
                has_supply_keywords = True
                break

        if has_supply_keywords:
            return PolicyType.SUPPLY_POLICY

        # 기본값
        return PolicyType.UNKNOWN

    def _extract_title(self, content: str, file_path: str) -> str:
        """
        문서의 제목을 추출합니다.
        먼저 파일명에서 제목을 추출하고, 없으면 문서 내용에서 찾습니다.

        Args:
            content: 문서 내용
            file_path: 파일 경로

        Returns:
            추출된 제목 문자열 (없으면 "날짜 미상")
        """

        file_name = os.path.basename(file_path)
        title_from_file = file_name.replace('.pdf', '')
        title_from_file = re.sub(r'\d+_?', '', title_from_file)
        title_from_file = title_from_file.replace('_',' ').strip()

        # 문서 내용에서 제목 찾기
        lines = content.split('\n')

        for line in lines[:10]:
            line_stripped = line.strip()
            line_length = len(line_stripped)

            # 적절한 길이의 라인인지 확인 
            if line_length < 10 or line_length > 100:
                continue
            
            # 페이지 표시가 아닌지 확인
            if line_stripped.startswith("["):
                continue

            # 제목으로 사용 가능한 라인 발견
            return line_stripped

        # 문서에서 제목을 찾지 못하는 경우 파일명 사용
        return title_from_file

# 전역 인스턴스 생성
policy_pdf_loader = PolicyPDFLoader()

    